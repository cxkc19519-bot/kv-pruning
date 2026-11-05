"""Snapshot installed metadata/source for N1; never import the measured backends.

Run on the server with the existing Python. Output is a new literature archive,
not an experiment. No package installation, model/tokenizer load or GPU probe.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time


PACKAGES = ("vllm", "xgrammar", "llguidance", "grid_guardrail", "torch",
            "tokenizers", "transformers", "psutil")
SOURCES = (
    "xgrammar/compiler.py", "xgrammar/tokenizer_info.py",
    "xgrammar/matcher.py", "llguidance/__init__.py", "llguidance/_lib.pyi",
    "vllm/v1/structured_output/utils.py",
    "vllm/v1/structured_output/backend_xgrammar.py",
    "vllm/v1/structured_output/__init__.py",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                       allow_nan=False) + "\n").encode()


def inspect(root, output):
    started = time.monotonic()
    if output.exists() or not output.is_relative_to(root / "literature"):
        raise ValueError("new_literature_directory_required")
    output.mkdir(parents=True, exist_ok=False)
    artifacts = []

    def snapshot(path, label):
        data = path.read_bytes()
        if len(data) > 512 * 1024:
            raise ValueError("source_snapshot_too_large")
        name = f"snapshot_{len(artifacts):02d}.txt"
        (output / name).write_bytes(data)
        row = {"source": str(path), "label": label, "name": name,
               "bytes": len(data), "sha256": digest(data)}
        artifacts.append(row)
        return data.decode(errors="replace"), row

    report = {"kind": "read_only_installed_metadata_and_source",
              "pid": os.getpid(), "python": sys.version,
              "backend_modules_imported": [], "environments": []}
    for env in (".venv", ".venv-controller-history"):
        directory = root / env
        row = {"name": env, "exists": directory.exists(), "sites": [],
               "packages": [], "source_capabilities": []}
        report["environments"].append(row)
        if not directory.exists():
            continue
        config = directory / "pyvenv.cfg"
        text, record = snapshot(config, env + "/pyvenv.cfg")
        settings = dict(line.split(" = ", 1) for line in text.splitlines()
                        if " = " in line)
        row["include_system_site_packages"] = (
            settings.get("include-system-site-packages") == "true")
        sites = list(directory.glob("lib/python*/site-packages"))
        if row["include_system_site_packages"]:
            # Static pyvenv.cfg provenance, not importing any base package.
            home = Path(settings["home"])
            sites.extend((home.parent / "lib").glob("python*/site-packages"))
        seen = set()
        for site in sites:
            site = site.resolve()
            if site in seen:
                continue
            seen.add(site)
            row["sites"].append(str(site))
            for package in PACKAGES:
                for metadata in sorted(site.glob(package + "-*.dist-info/METADATA")):
                    text, record = snapshot(metadata, env + ":" + package)
                    fields = {}
                    for key in ("Name", "Version", "Requires-Python"):
                        match = re.search("^" + key + r": (.*)$", text, re.M)
                        fields[key] = match.group(1) if match else None
                    fields["requires_dist"] = re.findall(
                        r"^Requires-Dist: (.*)$", text, re.M)
                    fields["snapshot"] = record["name"]
                    fields["sha256"] = record["sha256"]
                    row["packages"].append(fields)
            for source in SOURCES:
                path = site / source
                if not path.is_file():
                    continue
                text, record = snapshot(path, env + ":" + source)
                patterns = ("enable_dynamic_compilation", "cache_limit_bytes",
                            "cancel", "initial_lexer_fuel", "step_lexer_fuel",
                            "ThreadPoolExecutor", "compile_json_schema")
                row["source_capabilities"].append({
                    "source": source, "snapshot": record["name"],
                    "sha256": record["sha256"],
                    "text_hits_only_not_runtime_verification": {
                        pattern: [i + 1 for i, line in enumerate(text.splitlines())
                                  if pattern in line]
                        for pattern in patterns},
                })

    report["toolchain_paths"] = {name: shutil.which(name)
                                 for name in ("cargo", "rustc", "cc")}
    report["affinity_count"] = len(os.sched_getaffinity(0))
    cgroup_text = Path("/proc/self/cgroup").read_text()
    report["cgroup_membership"] = cgroup_text
    membership = next((line.split("::", 1)[1] for line in cgroup_text.splitlines()
                       if line.startswith("0::")), None)
    if membership is not None:
        cgroup = Path("/sys/fs/cgroup") / membership.lstrip("/")
        report["cgroup"] = {
            "path": str(cgroup), "directory_writable": os.access(cgroup, os.W_OK),
            "read_only_values": {
                name: {"value": (cgroup / name).read_text().strip()
                       if (cgroup / name).exists() else None,
                       "writable": os.access(cgroup / name, os.W_OK)}
                for name in ("cgroup.controllers", "cgroup.subtree_control",
                             "cpu.max", "memory.max", "pids.max")}}
    report["backend_modules_imported"] = [
        name for name in ("torch", "vllm", "xgrammar", "llguidance", "grid",
                          "transformers", "tokenizers") if name in sys.modules]
    if report["backend_modules_imported"]:
        raise RuntimeError("backend_import_not_allowed")
    report["elapsed_seconds"] = time.monotonic() - started
    (output / "inventory.json").write_bytes(encoded(report))
    (output / "source_manifest.json").write_bytes(encoded(artifacts))
    # The parent literature archive is sealed separately after external sources.
    files = list(output.iterdir())
    if len(files) > 64 or sum(p.stat().st_size for p in files) > 4 * 1024 * 1024:
        raise ValueError("preflight_archive_cap")
    return {"environment_count": len(report["environments"]),
            "snapshot_count": len(artifacts), "files": len(files),
            "bytes": sum(p.stat().st_size for p in files),
            "inventory_sha256": digest((output / "inventory.json").read_bytes()),
            "pid": report["pid"], "elapsed_seconds": report["elapsed_seconds"],
            "backend_modules_imported": report["backend_modules_imported"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    print(json.dumps(inspect(root, output), ensure_ascii=False))


if __name__ == "__main__":
    main()

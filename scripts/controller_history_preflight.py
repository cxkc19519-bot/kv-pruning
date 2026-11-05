"""Bounded, standard-library CPU algebra/state preflight; run on server only.

This is an independent float64 reference, not execution of vLLM/Triton.
It neither loads a model nor measures serving interference or GPU equivalence.
"""

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import signal
import sys
import time
import traceback
from datetime import datetime, timezone


COMMIT = "5df63a7203cdb9328d824a27b682e77c7b9928be"
BLOB = "f7a4a2f2c1e3221407d12c70cc067cc8cc045bd1"
PROPOSAL_SHA = "b597611cb56f802e6ea39535f705d62896723b1947ce143860f305dc640221d7"
REFERENCE_REVISION = 2  # Corrects the archived v1 fixture assertion; not rerun yet.
K, M, PERIOD, DAMPING, L2 = 4, 8, 100, 50.0, 0.001
ATOL, RTOL = 1e-9, 1e-8


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def flatten(value):
    if isinstance(value, dict):
        return sum((flatten(value[k]) for k in sorted(value)), [])
    if isinstance(value, (tuple, list)):
        return sum((flatten(v) for v in value), [])
    return [value]


def close(actual, expected):
    aa, bb = flatten(actual), flatten(expected)
    assert len(aa) == len(bb)
    worst = 0.0
    for a, b in zip(aa, bb):
        assert math.isfinite(a) and math.isfinite(b), (a, b)
        delta = abs(a - b)
        assert delta <= ATOL + RTOL * abs(b), (a, b, delta)
        worst = max(worst, delta)
    return worst


def sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


class Reference:
    """Estimator-only state. Does not model CUDA buffers or serving KV."""

    def __init__(self):
        self.s = {
            "slope": 0.5, "bias": [-0.2] * K,
            "info": [[0.0] * 3 for _ in range(K)],
            "grad": [[0.0] * 2 for _ in range(K)], "counts": [0] * K,
            "phase": 0, "refits": 0,
            "features": [[0.0] * K for _ in range(M)],
            "predictions": [[0.0] * K for _ in range(M)],
        }

    def snapshot(self):
        return copy.deepcopy(self.s)

    def restore(self, state):
        assert set(state) == set(self.s)
        self.s = copy.deepcopy(state)

    def coefficients(self):
        return [self.s["slope"], *self.s["bias"]]

    def step(self, rows):
        s = self.s
        slots = [r["slot"] for r in rows]
        assert len(slots) == len(set(slots)) and len(rows) <= M
        for r in rows:
            slot, x, accepted, admitted = (
                r["slot"], r["features"], r["accepted"], r["admitted"]
            )
            assert 0 <= slot < M and len(x) == K
            assert 0 <= accepted <= admitted <= K
            for k, feature in enumerate(x):
                feature = min(40.0, max(-40.0, feature))
                pred = sigmoid(s["slope"] * feature + s["bias"][k])
                s["features"][slot][k] = feature
                s["predictions"][slot][k] = pred
                # Same observed prefix semantics as the reviewed source.
                if k <= accepted and k < admitted:
                    weight = pred * (1.0 - pred)
                    resid = float(k < accepted) - pred
                    v = s["info"][k]
                    v[0] += weight * feature * feature
                    v[1] += weight * feature
                    v[2] += weight
                    s["grad"][k][0] += resid * feature
                    s["grad"][k][1] += resid
                    s["counts"][k] += 1
        s["phase"] += 1
        if s["phase"] == PERIOD:
            s["phase"] = 0
            self.refit()
            s["refits"] += 1

    def refit(self):
        s = self.s
        a = sum(row[0] for row in s["info"]) + L2
        b = [row[1] for row in s["info"]]
        c = [row[2] + L2 for row in s["info"]]
        g0 = sum(row[0] for row in s["grad"])
        g1 = [row[1] for row in s["grad"]]
        delta = (g0 - sum(b[k] * g1[k] / c[k] for k in range(K))) / (
            a - sum(b[k] * b[k] / c[k] for k in range(K))
        )
        total = sum(s["counts"])
        delta *= total / (total + DAMPING)
        if math.isnan(delta) or s["slope"] + delta < 0:
            delta = 0.0
        s["slope"] += delta
        for k in range(K):
            n = s["counts"][k]
            db = (g1[k] - b[k] * delta) / c[k] * n / (n + DAMPING)
            s["bias"][k] += 0.0 if math.isnan(db) else db
        s["info"] = [[0.0] * 3 for _ in range(K)]
        s["grad"] = [[0.0] * 2 for _ in range(K)]
        s["counts"] = [0] * K


def solve_dense(matrix, rhs):
    """Partial-pivot Gauss-Jordan; no arrowhead-specific identities."""
    n = len(rhs)
    a = [list(matrix[i]) + [rhs[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda i: abs(a[i][col]))
        a[col], a[pivot] = a[pivot], a[col]
        assert abs(a[col][col]) > 1e-15
        scale = a[col][col]
        a[col] = [v / scale for v in a[col]]
        for i in range(n):
            if i != col:
                scale = a[i][col]
                a[i] = [a[i][j] - scale * a[col][j] for j in range(n + 1)]
    return [row[-1] for row in a]


def dense_oracle(batches, coefficients):
    """Build full design vectors directly from accepted/first-failure labels."""
    h = [[L2 if i == j else 0.0 for j in range(K + 1)] for i in range(K + 1)]
    g, counts = [0.0] * (K + 1), [0] * K
    for batch in batches:
        for row in batch:
            labels = [1.0] * row["accepted"]
            if row["accepted"] < row["admitted"]:
                labels.append(0.0)
            for k, label in enumerate(labels):
                x = min(40.0, max(-40.0, row["features"][k]))
                p = sigmoid(coefficients[0] * x + coefficients[k + 1])
                z = [x] + [float(j == k) for j in range(K)]
                counts[k] += 1
                for i in range(K + 1):
                    g[i] += z[i] * (label - p)
                    for j in range(K + 1):
                        h[i][j] += p * (1.0 - p) * z[i] * z[j]
    solution = solve_dense(h, g)
    n = sum(counts)
    ds = solution[0] * n / (n + DAMPING)
    clipped = math.isnan(ds) or coefficients[0] + ds < 0
    if clipped:
        ds = 0.0
    # Source damps/clamps the slope BEFORE recalculating intercept deltas.
    db = [(g[k + 1] - h[k + 1][0] * ds) / h[k + 1][k + 1]
          * counts[k] / (counts[k] + DAMPING) for k in range(K)]
    return [coefficients[0] + ds, *[coefficients[k + 1] + db[k] for k in range(K)]], clipped


def batch(rng, num_rows=4, accepted=None, admitted=None):
    rows = []
    for slot in range(num_rows):
        a = rng.randrange(K + 1) if admitted is None else admitted
        j = rng.randrange(a + 1) if accepted is None else min(a, accepted)
        rows.append({"slot": slot, "features": [rng.uniform(-3, 3) for _ in range(K)],
                     "accepted": j, "admitted": a})
    return rows


class Case:
    def __init__(self, name, family, deadline):
        self.name, self.family, self.deadline = name, family, deadline
        self.steps = []
        self.details = {}

    def step(self, reference, rows, branch="main"):
        assert len(self.steps) < 256, "per-case call limit"
        assert time.monotonic() < self.deadline, "run deadline"
        self.steps.append({"branch": branch, "rows": copy.deepcopy(rows)})
        reference.step(rows)


def check_case(c, index):
    rng = random.Random(index + 314159)
    e = Reference()
    if c.family == "dense":
        batches = [batch(rng, M) for _ in range(8)]
        if index == 0:
            # Many observations with a relationship opposite to the initial slope.
            for rows in batches:
                for r in rows:
                    x = -3.0 if r["slot"] % 2 else 3.0
                    r.update(features=[x] * K, admitted=K, accepted=K if x < 0 else 0)
        initial = e.coefficients()
        for rows in batches[:-1]:
            c.step(e, rows)
        # An explicit near-boundary checkpoint, not a changed refit interval.
        e.s["phase"] = 99
        c.step(e, batches[-1])
        expected, clipped = dense_oracle(batches, initial)
        c.details = {"max_abs_delta": close(e.coefficients(), expected),
                     "slope_step_clipped": clipped, "coefficients": e.coefficients(),
                     "explicit_phase_before_last_step": 99}
    elif c.family == "mask":
        a, j = [(a, j) for a in range(K + 1) for j in range(a + 1)][index]
        row = {"slot": 7, "features": [0.0] * K, "accepted": j, "admitted": a}
        c.step(e, [row])
        expected = [int(k < j or (k == j and j < a)) for k in range(K)]
        assert e.s["counts"] == expected
        p = sigmoid(-0.2)
        close(e.s["grad"], [[0.0, ((1.0 if k < j else 0.0) - p) * expected[k]]
                               for k in range(K)])
        c.details = {"admitted": a, "accepted": j, "observed_counts": expected}
    elif c.family == "unobserved":
        before = e.coefficients()
        batches = []
        for _ in range(PERIOD):
            rows = batch(rng, 2, accepted=index, admitted=K)
            batches.append(rows)
            c.step(e, rows)
        expected, clipped = dense_oracle(batches, before)
        c.details = {"before": before, "after": e.coefficients(),
                     "dense_expected": expected, "slope_step_clipped": clipped,
                     "scope": "synthetic reference coupling, not a user effect"}
        c.details["dense_max_abs_delta"] = close(e.coefficients(), expected)
        assert e.s["bias"][index + 1:] == before[index + 2:]
        # Movement is possible, not mandatory: source rejects negative-slope steps.
        # Keep a designated movement fixture so a frozen implementation cannot pass.
        if index == 0:
            assert e.s["slope"] != before[0]
        assert all(math.isfinite(v) for v in e.coefficients())
    elif c.family == "empty":
        if index == 1:
            e.s["slope"], e.s["bias"] = 0.7, [0.8, 0.2, -0.5, -0.9]
        elif index >= 2:
            for _ in range(PERIOD):
                c.step(e, batch(rng, 2, accepted=K, admitted=K))
        if index == 3:
            state = e.snapshot()
            e.s["bias"][0] += 10.0
            e.restore(state)
        before = e.coefficients()
        for _ in range(PERIOD):
            c.step(e, [])
        assert e.coefficients() == before
        c.details = {"coefficients_preserved_exactly": True}
    elif c.family == "boundary":
        accepted = [K, 0, 2, None][index]
        for _ in range(99):
            c.step(e, [] if index == 3 else batch(rng, 2, accepted=accepted, admitted=K))
        assert e.s["phase"] == 99 and e.s["refits"] == 0
        assert e.coefficients() == [0.5, -0.2, -0.2, -0.2, -0.2]
        pending = e.snapshot()
        final = [] if index == 3 else batch(rng, 2, accepted=accepted, admitted=K)
        c.step(e, final)
        assert e.s["phase"] == 0 and e.s["refits"] == 1
        assert flatten(e.s["info"]) == [0.0] * (3 * K)
        assert flatten(e.s["grad"]) == [0.0] * (2 * K) and e.s["counts"] == [0] * K
        if index != 3:
            assert e.coefficients() != [0.5, -0.2, -0.2, -0.2, -0.2]
        c.details = {"before_refit": pending, "after_refit": e.snapshot()}
    elif c.family == "restore":
        for _ in range(45):
            c.step(e, batch(rng, 3))
        clean = e.snapshot()
        for _ in range(10):
            c.step(e, batch(rng, 3, accepted=K, admitted=K), "altered_history")
        dirty = e.snapshot()
        full, same, permuted, theta_only = (Reference() for _ in range(4))
        full.restore(clean)
        same.restore(clean)
        slot_map = [(slot + 1 + index % (M - 1)) % M for slot in range(M)]
        moved = copy.deepcopy(clean)
        for key in ("features", "predictions"):
            for slot, destination in enumerate(slot_map):
                moved[key][destination] = list(clean[key][slot])
        permuted.restore(moved)
        theta_only.restore(dirty)
        theta_only.s["slope"], theta_only.s["bias"] = clean["slope"], list(clean["bias"])
        full.s["features"][0][0] += 7.0
        assert clean["features"][0][0] != full.s["features"][0][0], "clone aliases input"
        full.restore(clean)
        # 45+10+4*50=255 calls, within the frozen 256-call case bound.
        for _ in range(50):
            rows = batch(rng, 3)
            c.step(full, rows, "full_restore")
            c.step(same, rows, "same_checkpoint")
            moved_rows = copy.deepcopy(list(reversed(rows)))
            for row in moved_rows:
                row["slot"] = slot_map[row["slot"]]
            c.step(permuted, moved_rows, "slot_and_batch_permutation")
            c.step(theta_only, rows, "theta_only_restore")
        assert full.snapshot() == same.snapshot(), "exact replay changed"
        unmoved = permuted.snapshot()
        for key in ("features", "predictions"):
            unmoved[key] = [list(permuted.s[key][slot_map[slot]]) for slot in range(M)]
        delta = close(unmoved, full.snapshot())
        assert theta_only.s["phase"] != full.s["phase"]
        assert theta_only.coefficients() != full.coefficients()
        c.details = {"exact_full_restore": True, "permutation_max_abs_delta": delta,
                     "slot_map": slot_map,
                     "theta_only_negative_control_detected": True,
                     "full": full.snapshot(), "theta_only": theta_only.snapshot()}
    else:
        raise AssertionError(c.family)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    assert str(root) == "/home/user/jhk/project/Directional Exploration/kv-pruning"
    out = Path(args.run_dir).resolve()
    assert out.is_relative_to(root / "results") and out.is_dir() and not out.is_symlink()
    assert not (out / "manifest.json").exists(), "never overwrite a run"
    started = time.monotonic()
    deadline = started + 60
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("60s bound")))
    signal.alarm(60)
    manifest = {"status": "running", "started_utc": now(), "pid": os.getpid(),
                "kind": "cpu_algebra_state_preflight", "rows": 0, "main_outputs": 0,
                "engineering_answers": 0, "fixture_results": 0, "failure": None,
                "python": sys.version, "platform": platform.platform(),
                "source_commit": COMMIT, "author_code_executed": False,
                "reference_revision": REFERENCE_REVISION,
                "gpu_used": False, "models_loaded": False, "files": {}}
    write_json(out / "manifest.json", manifest)
    active = None
    try:
        assert digest(out / "proposal.json") == PROPOSAL_SHA
        proposal = json.loads((out / "proposal.json").read_text())
        assert proposal["execution_enabled"] is False
        assert proposal["parameters"] == {"num_speculative_steps": K, "max_num_reqs": M,
            "refit_interval": PERIOD, "initial_slope": 0.5, "initial_bias": -0.2,
            "damping_observations": DAMPING, "l2_in_newton_system": L2, "max_log_odds": 40}
        source = (out / "upstream_acceptance_estimator.py.txt").read_bytes()
        assert hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest() == BLOB
        assert digest(__file__) == digest(out / "source_controller_history_preflight.py")
        manifest["source_sha256"] = {"controller_history_preflight.py": digest(__file__)}
        execution = copy.deepcopy(proposal)
        execution.update(execution_enabled=True, runner_implemented=True,
                         proposal_sha256=PROPOSAL_SHA, runner_sha256=digest(__file__),
                         upstream_blob_sha1=BLOB, permission="user_start_next_step")
        write_json(out / "execution_snapshot.json", execution)
        family_sizes = {"dense": 16, "mask": 15, "unobserved": 3,
                        "empty": 4, "boundary": 4, "restore": 12}
        assert sum(family_sizes.values()) <= proposal["bounds"]["max_fixture_cases"]
        results = []
        with (out / "fixtures.jsonl").open("x") as stream:
            for family, size in family_sizes.items():
                for i in range(size):
                    active = Case(f"{family}-{i:02d}", family, deadline)
                    check_case(active, i)
                    row = {"name": active.name, "family": family, "status": "pass",
                           "step_calls": len(active.steps), "trace": active.steps,
                           "details": active.details}
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                    stream.flush()
                    results.append({k: v for k, v in row.items() if k not in ("trace", "details")})
                    manifest["fixture_results"] = len(results)
                    active = None
        summary = {"status": "pass", "fixtures": len(results), "families": family_sizes,
                   "total_step_calls": sum(r["step_calls"] for r in results),
                   "max_step_calls_per_fixture": max(r["step_calls"] for r in results),
                   "cases": results, "main_outputs": 0, "engineering_answers": 0,
                   "qualification": "CPU reference algebra/state only; no GPU, model or attack validation."}
        write_json(out / "summary.json", summary)
        manifest["status"] = "complete"
        print(json.dumps({k: v for k, v in summary.items() if k != "cases"}))
    except BaseException as exc:
        manifest["status"] = "failed"
        manifest["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        write_json(out / "failure.json", {"failure": manifest["failure"],
            "traceback": traceback.format_exc(), "case": None if active is None else
            {"name": active.name, "family": active.family, "trace": active.steps,
             "details": active.details}})
        traceback.print_exc()
    finally:
        signal.alarm(0)
        manifest.update(finished_utc=now(), elapsed_seconds=time.monotonic() - started)
        manifest["files"] = {p.name: digest(p) for p in out.iterdir()
                             if p.is_file() and p.name not in ("manifest.json", "console.log", "launcher.json")}
        write_json(out / "manifest.json", manifest)
    return 0 if manifest["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())

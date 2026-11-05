"""Narrow CPU-import boundary for a pinned read-only loader query.

Not an OS sandbox. Native code is trusted; Python audit boundaries are observed.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import threading
import time


class CaptureLimit(RuntimeError):
    def __init__(self, reason, stdout=b'', stderr=b''):
        super().__init__(reason)
        self.stdout = stdout
        self.stderr = stderr


def drain(streams, seconds=1, stdout_limit=262144, stderr_limit=65536):
    """Bound bytes before buffering; caller owns process termination on errors."""
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    limits = {'stdout': stdout_limit, 'stderr': stderr_limit}
    until = time.monotonic() + seconds
    with selectors.DefaultSelector() as selector:
        for name, stream in streams.items():
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map():
            remaining = until-time.monotonic()
            if remaining <= 0:
                raise CaptureLimit('query_timeout', **{k:bytes(v) for k,v in buffers.items()})
            for key, _ in selector.select(min(.02, remaining)):
                name = key.data
                data = os.read(key.fileobj.fileno(), min(65536, limits[name]+1-len(buffers[name])))
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                buffers[name].extend(data)
                if len(buffers[name]) > limits[name]:
                    raise CaptureLimit(name+'_cap', **{k:bytes(v) for k,v in buffers.items()})
    return {k:bytes(v) for k,v in buffers.items()}


def birth(pid):
    text = Path(f'/proc/{pid}/stat').read_text()
    return int(text[text.rindex(')')+2:].split()[19])


class CapturedPopen:
    """Only the context/read/wait interface used by audited ctypes.util."""
    def __init__(self, argv, data, code, pid):
        self.args, self.returncode, self.pid = argv, code, pid
        self.stdin, self.stderr = None, None
        self.stdout = io.BytesIO(data)

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.stdout.close()

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode


class ImportBoundary:
    def __init__(self, root, output, pins, emit):
        self.root, self.output = Path(root).resolve(), Path(output).resolve()
        self.pins, self.emit = pins, emit
        self.original_popen = subprocess.Popen
        self.owner = threading.get_native_id()
        self.launching = False
        self.query_count = 0
        self.counts = dict(network_denied=0, process_denied=0, file_denied=0,
                           forbidden_imports=0, devnull_allowed=0, queries_allowed=0)

    def device_matches(self, path):
        if os.fspath(path) != self.pins['devnull']['path']:
            return False
        current = Path(path).stat()
        expected = self.pins['devnull']
        return stat.S_ISCHR(current.st_mode) and all(
            value == expected[key] for key,value in
            [('dev',current.st_dev),('ino',current.st_ino),('rdev',current.st_rdev)])

    def decide_open(self, path, mode, flags):
        path = os.fsdecode(path)
        resolved = Path(path).resolve()
        if resolved.is_relative_to(self.root/'models') or resolved.suffix in ('.safetensors','.bin','.pt','.pth'):
            return False
        writing = (isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if not writing or resolved.is_relative_to(self.output):
            return True
        safe_flags = os.O_ACCMODE | getattr(os,'O_CLOEXEC',0)
        return not(flags & ~safe_flags) and self.device_matches(path)

    def decide_query(self, argv, kwargs):
        expected = dict(stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, env={'LC_ALL':'C','LANG':'C'})
        if not isinstance(argv,list) or argv != self.pins['loader']['argv'] or kwargs != expected:
            return False
        path = Path(argv[0]); info=path.stat(); pin=self.pins['loader']
        return (str(path.resolve())==pin['resolved_path'] and info.st_dev==pin['dev']
                and info.st_ino==pin['ino'] and stat.S_ISREG(info.st_mode)
                and hashlib.sha256(path.read_bytes()).hexdigest()==pin['sha256'])

    def audit(self, event, args):
        category = None
        if event=='import' and args[0].split('.')[0] in ('vllm','tensorflow','jax'):
            category='forbidden_imports'
        if event in ('socket.__new__','socket.connect','socket.bind','socket.sendto','socket.getaddrinfo'):
            category='network_denied'
        if event in ('os.system','os.posix_spawn','os.fork','os.forkpty'):
            category='process_denied'
        if event=='subprocess.Popen':
            if not(self.launching and threading.get_native_id()==self.owner
                   and args[1]==self.pins['loader']['argv']):
                category='process_denied'
        if event=='open' and isinstance(args[0],(str,bytes)):
            if not self.decide_open(*args[:3]):
                category='file_denied'
            elif os.fsdecode(args[0])==self.pins['devnull']['path']:
                self.counts['devnull_allowed']+=1
                self.emit('devnull_allowed',flags=args[2])
        if category:
            self.counts[category]+=1
            self.emit('boundary_denied',category=category,audit_event=event,counts=dict(self.counts))
            if category=='network_denied':
                raise OSError('offline_socket_denied')
            raise RuntimeError('boundary_denied:'+category)

    def popen(self, argv, *positional, **kwargs):
        if positional or not self.decide_query(argv,kwargs):
            self.counts['process_denied']+=1
            self.emit('boundary_denied',category='process_denied',argv=repr(argv)[:300])
            raise RuntimeError('unapproved_library_query')
        if self.query_count>=4:
            raise RuntimeError('library_query_count_cap')
        self.query_count+=1
        self.counts['queries_allowed']+=1
        number=self.query_count
        start=time.monotonic()
        child=None; identity=None; data={'stdout':b'','stderr':b''}; error=None
        try:
            self.launching=True
            try:
                child=self.original_popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,env=kwargs['env'])
            finally:
                self.launching=False
            identity=birth(child.pid)
            self.emit('lookup_started',number=number,pid=child.pid,starttime=identity,argv=argv)
            remaining=1-(time.monotonic()-start)
            if remaining<=0:
                raise CaptureLimit('query_startup_timeout')
            data=drain({'stdout':child.stdout,'stderr':child.stderr},seconds=remaining)
            child.wait(timeout=max(.001,1-(time.monotonic()-start)))
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc)
            if isinstance(exc,CaptureLimit):
                data={'stdout':exc.stdout,'stderr':exc.stderr}
        finally:
            if child is not None and child.poll() is None:
                if birth(child.pid)!=identity:
                    raise RuntimeError('owned_query_identity')
                child.kill(); child.wait(timeout=1)
            if child is not None:
                child.stdout.close(); child.stderr.close()
            for name,value in data.items():
                (self.output/f'lookup-{number}-{name}.binlog').write_bytes(value)
            record=dict(number=number,argv=argv,pid=child.pid if child else None,starttime=identity,
                 exit_code=child.returncode if child else None,error=error,seconds=time.monotonic()-start,
                 stdout_bytes=len(data['stdout']),stderr_bytes=len(data['stderr']),
                 stdout_sha256=hashlib.sha256(data['stdout']).hexdigest(),
                 stderr_sha256=hashlib.sha256(data['stderr']).hexdigest())
            (self.output/f'lookup-{number}.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
            self.emit('lookup_finished',**record)
        if error or child.returncode!=0:
            raise RuntimeError('library_query_failed:'+str(error))
        return CapturedPopen(argv,data['stdout'],child.returncode,child.pid)

    def install(self):
        subprocess.Popen=self.popen
        sys.addaudithook(self.audit)
        self.emit('boundary_installed',counts=dict(self.counts))

"""Same-worker readiness and non-resetting startup/request clocks."""
import copy
import hashlib
import json
import time


class PhaseError(RuntimeError):
    pass


def fingerprint(scope):
    return hashlib.sha256(json.dumps(scope,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class PhaseController:
    def __init__(self,scope,owner,spawn_ns,clock=time.monotonic_ns,
                 import_only=True,emit=None,startup_ns=30_000_000_000,request_ns=5_000_000_000):
        self.scope=copy.deepcopy(scope);self.scope_hash=fingerprint(scope)
        self.owner=tuple(owner);self.spawn_ns=spawn_ns;self.clock=clock
        self.import_only=import_only;self.emit=emit
        self.startup_deadline=spawn_ns+startup_ns;self.request_budget=request_ns
        self.state='initializing';self.import_ready_ns=None;self.factory_begin_ns=None;self.factory_end_ns=None
        self.closed_ns=None;self.active=None;self.jobs=[];self.trace=[]
        self._last_ns=spawn_ns
        self._record('startup_begin',spawn_ns,deadline_ns=self.startup_deadline)

    def _now(self):
        now=self.clock()
        if now<self._last_ns:raise PhaseError('clock_regression')
        self._last_ns=now
        return now

    def _record(self,event,stamp,**data):
        row=dict(event=event,t_ns=stamp,state=self.state,owner=list(self.owner),scope_hash=self.scope_hash)
        row.update(data);self.trace.append(row)
        if self.emit:self.emit(row)

    def _deny(self,reason,stamp):
        self._record('denied',stamp,reason=reason)
        raise PhaseError(reason)

    def _startup_budget(self,stamp):
        if stamp>=self.startup_deadline:
            self.state='terminal';self._record('startup_timeout',stamp)
            raise PhaseError('startup_timeout')

    def startup_stage(self,name):
        stamp=self._now()
        if self.state!='initializing':self._deny('startup_state',stamp)
        self._startup_budget(stamp);self._record('startup_stage',stamp,name=name)

    def imports_ready(self,cuda_initialized=False,schema_work=0):
        stamp=self._now()
        if self.state!='initializing':self._deny('startup_state',stamp)
        self._startup_budget(stamp)
        if cuda_initialized or schema_work:self._deny('startup_scope_violation',stamp)
        self.import_ready_ns=stamp;self.state='library_import_ready'
        self._record('library_import_ready',stamp)

    def factory_begin(self):
        stamp=self._now()
        if self.import_only or self.state!='library_import_ready':self._deny('factory_not_admitted',stamp)
        self._startup_budget(stamp);self.factory_begin_ns=stamp;self._record('factory_begin',stamp)

    def factory_ready(self,domain_verified):
        stamp=self._now()
        if self.import_only or self.state!='library_import_ready' or self.factory_begin_ns is None:
            self._deny('factory_not_admitted',stamp)
        self._startup_budget(stamp)
        if domain_verified is not True:self._deny('domain_unverified',stamp)
        self.factory_end_ns=stamp;self.state='backend_factory_ready';self._record('backend_factory_ready',stamp)

    def check_context(self,scope,owner):
        stamp=self._now()
        if fingerprint(scope)!=self.scope_hash or tuple(owner)!=self.owner:
            self.state='terminal';self._record('scope_invalidated',stamp,observed_scope_hash=fingerprint(scope),observed_owner=list(owner))
            raise PhaseError('scope_changed')

    def submit(self,request_id,scope,owner):
        self.check_context(scope,owner);stamp=self._now()
        if self.state!='backend_factory_ready' or self.import_only:self._deny('backend_not_ready',stamp)
        if any(j['request_id']==request_id for j in self.jobs):self._deny('duplicate_request',stamp)
        job=dict(request_id=request_id,submit_ns=stamp,deadline_ns=stamp+self.request_budget,
                 stages=[],caller_return_ns=None,work_end_ns=None,censored=False)
        self.jobs.append(job);self.active=job;self.state='request_active'
        self._record('request_submitted',stamp,request_id=request_id,deadline_ns=job['deadline_ns'])
        return job['deadline_ns']

    def stage(self,name):
        stamp=self._now()
        if self.state!='request_active' or self.active is None:self._deny('no_active_request',stamp)
        if stamp>=self.active['deadline_ns']:self._deny('request_deadline',stamp)
        self.active['stages'].append(dict(name=name,t_ns=stamp))
        self._record('request_stage',stamp,name=name,deadline_ns=self.active['deadline_ns'])

    def dispatch_schema(self,callback):
        self.stage('schema_work')
        return callback()

    def caller_timeout(self):
        stamp=self._now()
        if self.active is None or self.active['work_end_ns'] is not None:self._deny('no_active_request',stamp)
        if stamp<self.active['deadline_ns']:self._deny('deadline_not_reached',stamp)
        self.active['caller_return_ns']=stamp
        self._record('caller_timeout',stamp,request_id=self.active['request_id'],work_ended=False)

    def work_finished(self):
        stamp=self._now()
        if self.active is None:self._deny('no_active_work',stamp)
        self.active['work_end_ns']=stamp
        self._record('work_finished',stamp,request_id=self.active['request_id'],after_deadline=stamp>=self.active['deadline_ns'])
        self.active=None
        if self.state!='terminal':self.state='backend_factory_ready'

    def close(self,reason='worker_exit'):
        stamp=self._now()
        if self.active is not None and self.active['work_end_ns'] is None:self.active['censored']=True
        self.state='terminal';self.closed_ns=stamp;self._record('closed',stamp,reason=reason)

    def ledger(self):
        request_durations=[None if j['work_end_ns'] is None else j['work_end_ns']-j['submit_ns'] for j in self.jobs]
        intervals=[]
        if self.import_ready_ns is not None:intervals.append((self.spawn_ns,self.import_ready_ns))
        if self.factory_begin_ns is not None and self.factory_end_ns is not None:intervals.append((self.factory_begin_ns,self.factory_end_ns))
        intervals.extend((j['submit_ns'],j['work_end_ns']) for j in self.jobs if j['work_end_ns'] is not None)
        covered=0;last=None
        for a,b in sorted(intervals):
            if last is None or a>=last:covered+=b-a;last=b
            elif b>last:covered+=b-last;last=b
        total=None if self.closed_ns is None else self.closed_ns-self.spawn_ns
        return dict(startup_ns=None if self.import_ready_ns is None else self.import_ready_ns-self.spawn_ns,
                    factory_setup_ns=None if self.factory_end_ns is None else self.factory_end_ns-self.factory_begin_ns,
                    cold_first_request_ns=request_durations[0] if request_durations else None,
                    warm_request_ns=request_durations[1:],end_to_end_ns=total,
                    accounted_interval_union_ns=covered,unallocated_or_idle_ns=None if total is None else total-covered,
                    request_jobs=copy.deepcopy(self.jobs),live_ready=False if self.closed_ns is not None else self.state in ('library_import_ready','backend_factory_ready'))

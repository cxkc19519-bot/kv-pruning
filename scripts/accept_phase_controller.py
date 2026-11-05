"""Eight deterministic software fixtures, no author backend or sleeping."""
import json
from phase_controller import PhaseController,PhaseError

SECOND=1_000_000_000


class Clock:
    def __init__(self):self.now=0
    def __call__(self):return self.now
    def at(self,seconds):self.now=int(seconds*SECOND)


def run(out):
    scope={'source':'fixture-v1','domain':'verified-fixture'};owner=(101,202)
    rows=[]

    def make(import_only=False):
        clock=Clock();return clock,PhaseController(scope,owner,0,clock=clock,import_only=import_only)

    def ready(clock,controller):
        clock.at(1);controller.imports_ready();controller.factory_begin();controller.factory_ready(True)

    def reject(callback,reason):
        try:callback()
        except PhaseError as error:
            assert str(error)==reason,(str(error),reason)
            return reason
        raise AssertionError('expected_rejection:'+reason)

    def record(case,clock,controller,evidence):
        if controller.closed_ns is None:controller.close('fixture_end')
        rows.append(dict(case=case,trace=controller.trace,ledger=controller.ledger(),evidence=evidence))

    clock,c=make(True);called=[];clock.at(.1)
    reason=reject(lambda:c.dispatch_schema(lambda:called.append(1)),'no_active_request');assert not called
    record('startup_denies_schema_work',clock,c,dict(rejection=reason,callback_calls=len(called)))

    clock,c=make(True);clock.at(30)
    reason=reject(c.imports_ready,'startup_timeout');assert c.state=='terminal'
    blocked=reject(lambda:c.submit('A',scope,owner),'backend_not_ready')
    record('startup_timeout_blocks_request_admission',clock,c,dict(rejection=reason,request_rejection=blocked))

    clock,c=make();clock.at(1);c.imports_ready()
    reason=reject(lambda:c.submit('A',scope,owner),'backend_not_ready')
    record('imports_ready_is_not_factory_ready',clock,c,dict(rejection=reason,observed_imports_ready=c.import_ready_ns is not None))

    clock,c=make();ready(clock,c);clock.at(2);deadline=c.submit('A',scope,owner);c.stage('validation')
    clock.at(7.1);reason=reject(lambda:c.stage('compile'),'request_deadline')
    record('validation_is_inside_request_deadline',clock,c,dict(rejection=reason,deadline_ns=deadline))

    clock,c=make();ready(clock,c);clock.at(2);deadline=c.submit('A',scope,owner)
    for name,stamp in [('validation',3),('queue',4),('compile',6.5)]:clock.at(stamp);c.stage(name)
    clock.at(7);reason=reject(lambda:c.stage('first_mask'),'request_deadline')
    assert c.active['deadline_ns']==deadline
    record('request_deadline_never_resets_across_stages',clock,c,dict(rejection=reason,deadline_ns=deadline))

    clock,c=make();ready(clock,c);clock.at(2);c.submit('A',scope,owner);clock.at(7);c.caller_timeout()
    assert c.active['work_end_ns'] is None
    clock.at(8);c.work_finished()
    record('caller_timeout_does_not_set_work_ended',clock,c,dict(caller_return_ns=7*SECOND,actual_work_end_ns=8*SECOND))

    clock,c=make();ready(clock,c);clock.at(2)
    reason=reject(lambda:c.check_context(dict(scope,source='fixture-v2'),owner),'scope_changed')
    assert c.state=='terminal'
    blocked=reject(lambda:c.submit('A',scope,owner),'backend_not_ready')
    # A second controller proves PID/starttime ownership is checked independently.
    clock2,c2=make();ready(clock2,c2);clock2.at(2)
    owner_reason=reject(lambda:c2.check_context(scope,(101,203)),'scope_changed');c2.close()
    record('scope_change_invalidates_readiness',clock,c,dict(rejection=reason,request_rejection=blocked,owner_rejection=owner_reason,owner_trace=c2.trace))

    clock,c=make();clock.at(20);c.imports_ready();clock.at(21);c.factory_begin();clock.at(25);c.factory_ready(True)
    clock.at(30);c.submit('cold',scope,owner);clock.at(31);c.stage('validation');clock.at(33);c.stage('compile');clock.at(34.5);c.work_finished()
    clock.at(40);c.submit('warm',scope,owner);clock.at(41);c.stage('first_mask');clock.at(42);c.work_finished();clock.at(45);c.close()
    ledger=c.ledger();assert ledger['startup_ns']==20*SECOND and ledger['factory_setup_ns']==4*SECOND
    assert ledger['cold_first_request_ns']==4.5*SECOND and ledger['warm_request_ns']==[2*SECOND]
    assert ledger['end_to_end_ns']==45*SECOND and ledger['unallocated_or_idle_ns']==14.5*SECOND
    record('ledger_separates_startup_cold_first_and_warm_costs',clock,c,dict(expected_total_ns=45*SECOND))
    assert len(rows)==8
    (out/'software-cases.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
    return rows

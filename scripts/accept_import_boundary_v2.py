"""Focused boundary acceptance, including one actual read-only loader query."""
import json
import os
from pathlib import Path
import subprocess

from import_boundary_v2 import ImportBoundary, CaptureLimit, drain


def run(root, out, pins, emit):
    boundary=ImportBoundary(root,out,pins,emit)
    kwargs=dict(stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                env={'LC_ALL':'C','LANG':'C'})
    rows=[]

    def check(name,actual,expected):
        rows.append(dict(case=name,actual=bool(actual),expected=expected,passed=bool(actual)==expected))
        if not rows[-1]['passed']:
            raise AssertionError(name)

    check('devnull_rdwr',boundary.decide_open('/dev/null',None,os.O_RDWR),True)
    check('devnull_append_denied',boundary.decide_open('/dev/null',None,os.O_RDWR|os.O_APPEND),False)
    check('devnull_create_denied',boundary.decide_open('/dev/null',None,os.O_RDWR|os.O_CREAT),False)
    writer_flags=os.O_WRONLY|os.O_CREAT|os.O_TRUNC
    check('pinned_devnull_buffered_writer',boundary.decide_open('/dev/null','w',writer_flags),True)
    check('pinned_devnull_pyio_writer',boundary.decide_open('/dev/null',None,writer_flags),True)
    bad=json.loads(json.dumps(pins));bad['devnull']['rdev']+=1
    check('devnull_wrong_identity_denied',ImportBoundary(root,out,bad,emit).decide_open('/dev/null',None,os.O_RDWR),False)
    check('run_write_allowed',boundary.decide_open(str(out/'allowed.txt'),'w',os.O_WRONLY|os.O_CREAT|os.O_TRUNC),True)
    check('outside_write_denied',boundary.decide_open(str(root/'outside.txt'),'w',os.O_WRONLY|os.O_CREAT|os.O_TRUNC),False)
    check('model_read_denied',boundary.decide_open(str(root/'models/forbidden.safetensors'),'r',0),False)
    check('query_exact',boundary.decide_query(['/sbin/ldconfig','-p'],kwargs),True)
    check('query_extra_arg_denied',boundary.decide_query(['/sbin/ldconfig','-p','-N'],kwargs),False)
    check('query_alias_denied',boundary.decide_query([pins['loader']['resolved_path'],'-p'],kwargs),False)
    check('query_shell_denied',boundary.decide_query(['/sbin/ldconfig','-p'],dict(kwargs,shell=True)),False)
    check('query_env_denied',boundary.decide_query(['/sbin/ldconfig','-p'],dict(kwargs,env={'LC_ALL':'C','LANG':'C','LD_PRELOAD':'x'})),False)
    check('query_stdout_denied',boundary.decide_query(['/sbin/ldconfig','-p'],dict(kwargs,stdout=None)),False)
    check('query_cwd_denied',boundary.decide_query(['/sbin/ldconfig','-p'],dict(kwargs,cwd=str(out))),False)
    bad=json.loads(json.dumps(pins));bad['loader']['sha256']='0'*64
    check('query_identity_denied',ImportBoundary(root,out,bad,emit).decide_query(['/sbin/ldconfig','-p'],kwargs),False)
    boundary.query_count=4
    try:
        boundary.popen(['/sbin/ldconfig','-p'],**kwargs)
        check('query_count_cap',False,True)
    except RuntimeError as exc:
        check('query_count_cap',str(exc)=='library_query_count_cap',True)
    boundary.query_count=0
    for kind in ('overflow','timeout'):
        r,w=os.pipe();r2,w2=os.pipe()
        stdout=os.fdopen(r,'rb',buffering=0);stderr=os.fdopen(r2,'rb',buffering=0)
        try:
            if kind=='overflow':
                os.write(w,b'x'*16)
            try:
                drain({'stdout':stdout,'stderr':stderr},seconds=.025,stdout_limit=8,stderr_limit=8)
                check('capture_'+kind,False,True)
            except CaptureLimit as exc:
                wanted='stdout_cap' if kind=='overflow' else 'query_timeout'
                check('capture_'+kind,str(exc)==wanted,True)
        finally:
            stdout.close();stderr.close();os.close(w);os.close(w2)
    boundary.install()
    import _pyio
    with open('/dev/null','wb') as builtin_writer,_pyio.open('/dev/null','wb') as python_writer:
        check('actual_builtin_and_pyio_writers',builtin_writer.write(b'fixture')==7 and python_writer.write(b'fixture')==7,True)
    with subprocess.Popen(['/sbin/ldconfig','-p'],**kwargs) as child:
        data=child.stdout.read()
        check('actual_query_bounded',child.wait()==child.poll()==0 and len(data)<=262144,True)
    try:
        boundary.original_popen(['/bin/true'])
        check('raw_popen_bypass_denied',False,True)
    except RuntimeError as exc:
        check('raw_popen_bypass_denied',str(exc)=='boundary_denied:process_denied',True)
    result=dict(cases=rows,passed=len(rows),boundary_counts=boundary.counts,
                query_count=boundary.query_count,actual_loader_output_bytes=len(data))
    (out/'software-results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

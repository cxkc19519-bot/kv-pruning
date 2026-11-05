"""Gold-blind BoolQ JSON-boolean adapter. No data or model I/O."""
import json
from answer_format_task import strict_json, TaskError


def extract_boolean(raw):
    if not isinstance(raw,str):raise ValueError('raw_not_string')
    s=raw.strip(' \t\r\n')
    try:value=strict_json(raw)
    except TaskError as exc:return dict(format=False,candidate=None,reason=str(exc))
    except json.JSONDecodeError:
        if s.startswith(('{','[','"','```')):return dict(format=False,candidate=None,reason='structured_parse_failure')
        value=s
    if isinstance(value,dict):
        answer=value.get('answer')
        if type(answer) is bool:return dict(format=set(value)=={'answer'},candidate=answer,reason='object_boolean')
        if isinstance(answer,str) and answer.strip().casefold() in ['yes','no','true','false']:
            return dict(format=False,candidate=answer.strip().casefold() in ['yes','true'],reason='object_string_boolean')
        return dict(format=False,candidate=None,reason='no_boolean_answer')
    if type(value) is bool:return dict(format=False,candidate=value,reason='bare_json_boolean')
    if isinstance(value,str) and value.strip().casefold() in ['yes','no','true','false']:
        return dict(format=False,candidate=value.strip().casefold() in ['yes','true'],reason='whole_boolean_literal')
    return dict(format=False,candidate=None,reason='ambiguous_or_unsupported_boolean')


def score_boolq(raw,gold):
    if type(gold) is not bool:raise ValueError('gold_not_boolean')
    r=extract_boolean(raw)
    r['candidate_status']='unavailable' if r['candidate'] is None else 'available'
    r['em']=None if r['candidate'] is None else r['candidate']==gold
    r['joint_success']=bool(r['format'] and r['em'])
    return r

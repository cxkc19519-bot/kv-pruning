"""Use a small, reviewed subset of pinned upstream serialization definitions.

No benchmark agent, executor, network client, or training module is imported.
Upstream definitions retain their Apache-2.0 license in the source audit.
"""
import ast
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any


@dataclass
class Action:
    tool_name: str | None = None
    arguments: dict = field(default_factory=dict)
    thought: str = ''
    raw_text: str = ''
    step: int = 0


@dataclass
class Observation:
    content: str
    step: int = 0


@dataclass
class UserMessage:
    content: str


@dataclass
class InteractionHistory:
    user_request: str
    initial_state: str = ''
    steps: list = field(default_factory=list)
    post_action_steps: list = field(default_factory=list)


@dataclass
class GuardrailContext:
    available_tools: list = field(default_factory=list)
    tool_schemas: list = field(default_factory=list)


def source_namespace(source_run):
    """Execute only reviewed pure syntax for native text/regex operations."""
    root = Path(source_run)
    manifest = json.loads((root/'manifest.json').read_text())
    assert manifest['status'] == 'complete'
    expected = {r['path']:r['sha256'] for r in manifest['files']}
    ns = dict(Action=Action, Observation=Observation, UserMessage=UserMessage,
              InteractionHistory=InteractionHistory, GuardrailContext=GuardrailContext,
              PromptProfile=object, BaseBenchmarkAdapter=object, re=re, ast=ast, json=json, Any=Any)
    hashes = {}
    specs = [
        ('github/src/guardrail/prompts/base.py', {'_parse_safe_unsafe','_parse_binary_judgment'}, None),
        ('github/src/guardrail/prompts/stepguard.py', {'RISK_SOURCES','STEPGUARD_PROMPT_NAME','STEPGUARD_PROMPT','_render_action',
          '_serialize_history','_render_tools','_available_tools','StepGuardProfile'}, None),
        ('github/src/evals/benchmarks/ts_bench.py', {'TSBenchAdapter'},
         {'_HISTORY_STEP_RE','_OBSERVATION_SPLIT_RE','_parse_action_text','_parse_history_steps','_parse_env_info'}),
    ]
    for name, allow, members in specs:
        path=root/'upstream'/name;raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest == expected[name]
        hashes[name]=digest
        tree=ast.parse(raw.decode())
        body=[]
        for node in tree.body:
            symbol = node.name if isinstance(node,(ast.FunctionDef,ast.ClassDef)) else (
                node.targets[0].id if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) else None)
            if symbol not in allow:
                continue
            if isinstance(node,ast.ClassDef) and members:
                node.body=[m for m in node.body if (
                    isinstance(m,ast.FunctionDef) and m.name in members) or (
                    isinstance(m,ast.Assign) and isinstance(m.targets[0],ast.Name) and m.targets[0].id in members)]
            body.append(node)
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        selected=ast.fix_missing_locations(ast.Module(body=[future]+body,type_ignores=[]))
        exec(compile(selected,str(path),'exec'),ns)
    return ns, hashes


def render_case(raw, ns):
    adapter=ns['TSBenchAdapter']
    request=str(raw['instruction'])
    history_text=str(raw.get('history','')).strip()
    steps=adapter._parse_history_steps(history_text)
    if history_text:
        matches=list(adapter._HISTORY_STEP_RE.finditer(history_text))
        assert not matches or not history_text[:matches[0].start()].strip(), 'Native parser would omit non-whitespace history preamble'
    history=InteractionHistory(user_request=request,steps=steps)
    step_number=sum(isinstance(s,Action) for s in steps)+1
    action=adapter._parse_action_text(str(raw.get('current_action','')),step=step_number)
    context=GuardrailContext(available_tools=adapter._parse_env_info(str(raw.get('env_info',''))))
    profile=ns['StepGuardProfile']()
    current=f'[Step {step_number}] [AGENT]:\n'+ns['_render_action'](action)
    tools=ns['_render_tools'](context.available_tools)
    result={}
    for condition,h in [('full',history),('no_history',InteractionHistory(user_request=request))]:
        text=ns['_serialize_history'](h)
        fields=dict(risk_sources=ns['RISK_SOURCES'],user_request=request,
                    history_text=text,current_action_text=current,tool_list_text=tools)
        prompt=profile.build_prompt(history=h,action=action,context=context)
        template=profile.template
        left,right=template.split('{history_text}')
        before=left.format(**fields)
        tail_before,tail_after=right.split('{current_action_text}')
        prefix=before+text+tail_before.format(**fields)
        suffix=current+tail_after.format(**fields)
        assert prompt == prefix+suffix == template.format(**fields)
        result[condition]=dict(prompt=prompt,prefix_text=prefix,suffix_text=suffix,
                               history_char_span=[len(before),len(before)+len(text)],
                               history_text=text, current_action_text=current, tools_text=tools)
    return result, dict(prior_agent_steps=step_number-1,tool_name=action.tool_name,
                       native_action_step=step_number, raw_history_chars=len(history_text))


def encode_rendered(rendered, tokenizer):
    messages=[dict(role='user',content=rendered['prompt'])]
    text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
    encoded=tokenizer(text,add_special_tokens=False,return_offsets_mapping=True)
    assert ids == encoded['input_ids']
    assert text.count(rendered['prompt']) == 1
    offset=text.index(rendered['prompt'])
    hs,he=[offset+n for n in rendered['history_char_span']]
    action_start=offset+len(rendered['prefix_text'])
    offsets=encoded['offset_mapping']
    boundary=next((i for i,(s,e) in enumerate(offsets) if s>=action_start and e>s),None)
    assert boundary is not None
    assert not any(s<action_start<e for s,e in offsets), 'Native action boundary crosses a token'
    history_positions=[i for i,(s,e) in enumerate(offsets) if e>hs and s<he and e>s]
    assert history_positions and max(history_positions)<boundary
    return dict(input_ids=ids, prefix_length=boundary, history_positions=history_positions,
                history_token_count=len(history_positions), full_token_count=len(ids),
                native_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                input_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest(),
                native_history_span=[hs,he],native_action_start=action_start)


def strict_judgment(text):
    tags=re.findall(r'<Judgment>\s*(safe|unsafe)\s*</Judgment>',text,flags=re.I)
    if len(tags)!=1 or len(re.findall(r'<Judgment\b',text,flags=re.I))!=1:
        return None
    return int(tags[0].lower()=='unsafe')


def schema_ok(text):
    pattern=r'\s*<Analysis>.+?</Analysis>\s*<Judgment>\s*(?:safe|unsafe)\s*</Judgment>\s*<RiskSourcePresent>\s*(?:yes|no)\s*</RiskSourcePresent>\s*<RiskSource>[^<>]+</RiskSource>\s*'
    return bool(re.fullmatch(pattern,text,flags=re.I|re.S))

# 条件级准入与工程证据：CPU验收

## 实验身份

- 2026-10-30，Asia/Singapore。用户要求“开始下一步”，按交接实现条件级预算准入和工程证据接口，用现有60计划格验收，不重新推理。
- 服务器绝对目录：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-condition-admission-v1`。
- 状态complete，v1单次成功，无失败/重试。PID924636已退出，0主/工程模型回答；新增1CPU run后累计108run2852历史主输出，不作独立样本量。
- 这是软件契约和归档证据回读，不是科学确认、模型重测或生产HF接线验证。

## 可复现条件

| 文件 | SHA256 |
| --- | --- |
| scripts/reliability_execution_contract.py | 9e279dc1e8ffa64134841cea9c46b6a3be876c70dd6d3345bd5a621f4d92a21c |
| scripts/execution_contract_acceptance.py | b009b1705fb1255a426f6c31d4f7a1713ef36215968053f577efe2178e0b23c1 |
| scripts/accept_condition_admission.py | bbeadb1024c780424b9d0c7bfacd2387754e3cf9b67e20cf2ee5488fe1c4287f |
| configs/condition-admission-acceptance-v1.json | 468f187e4390a4c1c87149c33481b0163aa63046587dda0f3617eac9944dc43a |

提案原false/未实现字段保持，实际execution snapshot另存。固定10输入527183bytes、78源JSONL记录（14个实际工程输出+4工程不可行+60主计划格）；包含原核心/适配器SHA，旧源码不修改。read-only源包括新SQuAD14题tokenized、Full/compact实际snapshot与工程/DEV记录，以及原报告。

纯标准库、现有`.venv/bin/python`，Python版本原样保存在snapshot。无torch/HF/vLLM/作者评分器导入，无模型/tokenizer/张量加载、GPU/网络查询或安装。AST允许列表及禁exec/eval动态执行检查通过。内部60秒/1MiB输入/100源JSONL行/8MiB归档/32文件、outer65秒；0生成。实际0.052992767秒包含读写，不是推理速度或生产性能。

已执行历史命令（固定目录拒绝覆盖，不重跑）：

```bash
.venv/bin/python -u scripts/accept_condition_admission.py --execute
```

stdout/stderr与pid/绝对命令/exit0保存在同级`.console.log`/`.launch.json`。原始证据、报告与逐格结果仅服务器，本地仅源码配置文档。没有新后台任务/服务，也未重新测GPU；上轮18MiB/0%不冒充本轮测量。

## 结果与解释

20软件用例全部通过，覆盖budget union/条件指纹、完整/缺失/失败/无可执行工程证据、token/trace/termination/input不一致、重复/过期证据、空token、截断一致性、历史不可行矛盾、not_run与诊断保留、以及被阻止时callback不调用。callback仅软件stub，不产生模型回答。

从每条件原生工程记录重建证据，**不读取总engineering_gate作为验证依据**：Full及无保护Snap/random各有两题路径序列一致，三个条件verified；保护条件的两工程题各全部预算不可行，两个条件unverified。Snap有一工程题两路径均截断但序列/trace相同，记录“在固定decode cap内数值一致，非完整交付”。

| 判断层次 | 数量 | 含义 |
| --- | --- | --- |
| 原DEV计划格 | 60 | 12组×5条件 |
| 数学预算可行 | 40 | 不等于有同条件工程证据 |
| 数学预算不可行 | 20 | 保留infeasible，不加预算 |
| 未来可准入 | 36 | Full12+无保护24，只是预检资格 |
| 未来因工程未验证阻止 | 4 | 两保护各2个预算可行DEV格 |
| 原历史实际输出 | 40 | 全部保持原执行、raw、指标和hash |
| 其中工程未覆盖的历史诊断 | 4 | 原保护输出不删除，不计新证据 |

历史40实际输出与20不可行不变；新严格policy拒绝未来执行那4格，不追改过去协议/分数/研究关卡。原分析report SHA仍`d6852baf…`。旧QA false关卡、BoolQ403来源失败、封存48/旧封存16均不改变。

## 独立复核与归档

外层不导入新接口，独立重算60格anchors/system并集与floor预算、三类准入计数，直接比较原工程token/trace/termination，验证两保护没有工程输出；逐格重算原始row的规范JSON hash并核对execution/truncated均保持，全部通过。原manifest15项逐SHA一致，10输入运行前后不变。新接口没有接入真实HF driver，producer仍保持原代码与历史总gate字段；本次仅消费者独立识别其证据边界。

| 工件 | SHA256 |
| --- | --- |
| manifest.json | 3a770769787e44e8f1764a6655e6cd4eb7697d0a90ebd96231d02f76e9f40a80 |
| summary.json | 170f1087dc7dff91e7e006d95cd0055693284d1c081ecfc997bc413b76fe45fa |
| report.json | 12010193f41af9b578e231d8dae045f1ab7ae143a6f69019728f92a27193bb81 |
| engineering_evidence.json | a4ecf27c81b1b71e176794314fdefc22deb4bb758d44bfcd5d25fe3762c42e59 |
| admission_cells.jsonl | 269d47c73ce6b1a7d40101bac7207c7a693aa44da2d58102c9778bae05eb5cd1 |
| independent_verification.json | b8a8f4808ade67b41761dfa34a13b4ef2ee2444f6ad109cc4e2d717287aa7f7c |
| closure.json | 6a3ddf1fa0228d514d613f3c95667cfb9b76b5734d5b93f0a298afcc5b4fffd1 |
| derived_manifest.json | 55161c2a1fd21e6a1d1e66f697cf74faa3e3dad6b692c243cc0730f9cd6170b7 |

目录19文件181862bytes，另同级launch/console。原manifest不追改后验文件，derived另覆盖此前18文件而不包含自身。新索引`results/20261030-run-index-condition-admission.json` SHA **`3972e01f54f70e310a6731bc0e1fb38b3a130f936d1903c9d93c9b260984c909`**，旧107run索引不变。

## 下一步

接口与证据范围见[设计说明](../CONDITION_ADMISSION_20261030.md)。下一条接入新HF编排壳，先仅dry-run验证每stage/case/condition顺序、预算/证据拦截与输入指纹，避免加载模型后才发现不可行；不要重新生成既有DEV。bootstrap工程stage与正式DEV的证据要求须明确区分；真实生成调用接线和新版本工程验证仍待独立有界协议，当前无GPU队列。STATUS/WORKLOG/HANDOFF与readiness维护并同步服务器；根环境无变化，GitHub未配置未push。

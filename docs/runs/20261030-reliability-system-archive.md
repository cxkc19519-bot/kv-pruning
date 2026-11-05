# 模块化系统首轮验收：两类任务、三组归档

## 实验身份

- 2026-10-30，Asia/Singapore。用户明确要求“开始做系统设计与实证”，本轮实现并验收系统公共核心，后续独立模型实证另按新来源协议准备。
- 服务器绝对目录：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-reliability-system-archive-v1`。
- 类型：系统正确性与历史标量报告回放，不是新的模型实验或独立科学确认。状态complete；v1一次成功，无失败run/重试。
- PID907824已退出；0主/工程模型回答，新增1CPU run后累计100run2812历史主输出，不能作样本量。

## 可复现条件

新增标准库模块，各自独立于旧生成器：

| 文件 | SHA256 |
| --- | --- |
| scripts/reliability_system_core.py | ea87bd0d1cff69014336cd59f61b4e77d2d0e43b6f679bf340d77c6f5c8ed546 |
| scripts/reliability_system_adapters.py | ecaeebf677778743cc6e8f9c8a3019a866cb00abb247c6369a8eabae109370b9 |
| scripts/reliability_system_acceptance.py | 1271a7e31ea76a20439dbbd31f59fb0fb6fab1c0b70553c33020031b82c572b1 |
| scripts/accept_reliability_system_archive.py | a79dc4c59f7d098f08753b070d1388a8a8a7edb43d8a0afa916b3976e4cc4a1a |

[原提案](../../configs/reliability-system-archive-acceptance-v1.json) SHA `8988fd99ee706891ac678fd057b6a6c3c0eae6cf383a14a8c9f1c3456c633023`保留false/未实现字段，实际执行快照另存。固定8输入SHA，合计840461bytes、324源JSONL行（其中34行是分组元数据），生成290规范化结果行；不是324个模型输出。

纯标准库，原`.venv/bin/python`版本写入execution snapshot。无Torch/HF/vLLM/旧评分器导入、模型/tokenizer/张量加载、联网下载/安装、GPU查询或服务；不改变环境。source AST核准标准库与三新模块的import，禁止动态exec/eval。上限60秒、2MiB输入/350源JSONL行、16MiB归档/32文件、0生成。

已执行命令（固定目录拒绝覆盖，不作为重跑待办）：

```bash
.venv/bin/python -u scripts/accept_reliability_system_archive.py --execute
```

外层launcher记录绝对命令、pid与exit0，同级`.launch.json`/`.console.log`保存；outer65秒未触发。CPU实际0.073419555秒，含输入检查和报告写入，不是模型性能或通用系统吞吐。原始归档记录、报告与测试结果只服务器，本地只源码、配置和文档。

## 验收结果

16软件检查全部通过：GQA/MHA字节、混合层布局、拒绝非Full/未支持dtype、精确保留比例/保护集合去重、保护超预算不扩容、非法位置/比例、重复cell、等预算拒绝、输入/配置身份错配、N/A风险、零分母、截断、缺cell、infeasible、净分相抵的损坏改善，以及连续F1/未知成本/指标版本与NaN类型拒绝。软件布局检查只验证描述符计算，未加载新模型张量。

| cohort | case数 | 规范化cell | Full任务正确 | Full约束合法 |
| --- | --- | --- | --- | --- |
| legacy_trec_development32 | 32 | 160 | 19 | 32 |
| legacy_trec_holdout10 | 10 | 50 | 7 | 10 |
| used_squad_json_development16 | 16 | 80 | 12 | 16 |

三组分别汇总，所有旧严格计数、四转移、可比较/未评估Full正确分母和QA F1完全一致（浮点误差门槛1e-12）。旧TREC任务/格式语义保持，QA连续F1没有被转换成布尔分。唯一随机QA截断仍排除严格配对并显式N/A；格式损坏覆盖范围[7/16,8/16]，不填成无风险或语义错。未测peak/latency/extra_buffer保持null及not_measured。

QA Full/压缩实际execution snapshot中的模型、解码、层数/head/dtype及字节常数一致性已核，布局描述重算57344bytes/token。TREC引用原回归中已建立的运行身份，**本轮没有重新审计其模型cache**；新comparison digest显式标明归档审计范围。case/condition计划从固定历史记录枚举，只用于回放，不冒充前瞻注册计划。

## 独立回读、摘要与收尾

外层不导入新系统核心，独立逐行Counter重算三组所有method的bool转移/分母/未知范围、连续分均值与配对差、290唯一键以及未知成本字段，全部通过。原manifest14条hash逐项一致；源码/提案/八输入hash运行前后不变。旧QA研究关卡false没有被新系统验收覆盖。

| 工件 | SHA256 |
| --- | --- |
| manifest.json | b289483e0c69aadb5a81469d5ed45fdb21a796b7c756e9ac293b5814145ba91b |
| summary.json | 920d2f13e25b07b9290b97546dd679870c48ebba8baa5c1951d433e0481fbfd9 |
| report.json | d416b7e73f299015405fe087e81441c2a3df24fd8103a6bd1f5e25c81683fc33 |
| normalized_records.jsonl | 7f2feead3f25b3539ed09eda9ee01fe0c04ec85a3df84b0ef4dc3d4f12e1953e |
| execution_snapshot.json | 97c06b52df0ec383ef5fa331bf65b64b61ff8a8584754b7e6a6a51249a0c1947 |
| independent_verification.json | a58eb7a9b2e12eb4b0fe00be75c6cec6cc994a251ae5484b6118cf3d45023da5 |
| closure.json | 9eaf72016ec7d6c43fae6f9a23f84a823d74e07b4334a670938f91ae9afcbaca |
| derived_manifest.json | 0979f383ef90edc67356cf25c061fa8ba358dbd101d2afeff37565572cb1ecc6 |

目录18文件647835bytes，另有同级launch/console。原manifest不覆盖后验文件，derived manifest另覆盖此前17文件而不包含自身。新索引`results/20261030-run-index-reliability-system.json` SHA `cef16cc43c6463dca7d58fcd203df7001d5231bfcbab536ce182a784dca46793`，旧99run索引不改。

自有PID907824退出；仅确认旧自有4PID不存在，未重新测GPU或其他进程，不把上轮18MiB/0%说成本轮测量。无环境/服务变化，未改旧生成脚本、输入、研究gate或原始输出。代码配置文档同步服务器，GitHub未配置未push。

## 解释与下一步

直接支持：报告与预算核心已摆脱旧题数/模型常数，能以两个适配器分别重现三组历史严格报告，并处理软件故障边界。系统总体、跨模型KV后端与新任务评分尚未全部实现，也无真实峰值/吞吐测量。

下一步按[独立实证方案](../RELIABILITY_EMPIRICAL_PLAN_20261030.md)先固定SQuADtrain/BoolQ来源、BoolQ评分与历史/跨任务分组排除，再实现有界CPU数据预检；新任务准备通过后才注册12题DEV的小规模模型实验。旧QA封存16不恢复。当前只有设计草案，无新GPU配置/后台运行任务；用户授权开展实证持续有效，待必要协议完整后可继续执行，不需重复申请常规许可。

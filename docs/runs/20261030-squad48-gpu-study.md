# Qwen/SQuAD原48组GPU独立描述性验证

## 实验身份

- 日期2026-10-30，Asia/Singapore；UTC 2026-10-30T15:07:44.512918+00:00 – 2026-10-30T15:10:10.337882+00:00。
- 授权：用户在实验会话要求“开始下一步”；按固定[协议](../SQUAD48_GPU_PROTOCOL_20261030.md)运行原48题。本run完整完成并独立核验，0失败/重试。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-squad48-gpu-study-v1`。
- 问题：在普通Full Attention Qwen与固定半prefix KV预算下，原48预留组的任务、JSON约束、联合交付和覆盖分别如何变化。
- 来源：项目独立实现的prefix-only Snap适配与uniform_random，非作者原版SnapKV，未读取或复制nano-vllm。

## 可复现条件

- [配置](../../configs/squad48-gpu-study-v1.json) SHA `11f0f216ff2c18304760fbf8f818abe47ff72de98de53a3447a0c55ca76f3080`，先同步SHA后执行；[readiness](../SQUAD48_GPU_READINESS_20261030.json)给出全部工件和指标；[研究解释](../SQUAD48_EVIDENCE_CONCLUSION_20261030.md)限制结论。
- 无Git仓库/commit/remote配置，不曾push GitHub。固定旧计算源码不改，新study入口与adapter独立实现，原HF角色限制仍拒绝该角色；未注入旧14答证据。
- Qwen/Qwen2.5-7B-Instruct revision a09a35458c702b33eeacc393d103063234e8bc28；逐4权重、6metadata SHA核验。实际28Full/GQA4/head128/BF16/SDPA/57344 bytes每K+V槽；4权重由独立validator再次完整核SHA。
- 既有Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1/safetensors0.6.2；具体实际config/decode/版本存actual_runtime与backend snapshot。物理GPU1 UUID4ce22e12-b5c0-e423-06c5-e858bb71daaa；加载前空闲15MiB/0%，沿配置memory≤128MiB/util0检查。当前驱动沿既有580.178.04，本轮未安装或改驱动/CUDA/依赖。
- 原48预留文章组、原ID/顺序/prompt/答案，1组1题，12个固定上游输入先核SHA。engineering沿原2题，不替换DEV/预留题。原scope/CPU false历史字段不追改。
- greedy128/rep1/TF32关闭，torch seed20261030；随机选择seed20261028。无保护，Full一次共享，两个压缩条件均floor(prefix/2)/sink4/recent64，预算不足不生成、不补齐。重新核50个完整原生输入（2工程+48主），独立validator只decode、不再编码。
- CPU软件S01–S16先于重型库与后端构造通过；现场Full三路径6工程答→Full48支持→两条件双路径8工程答→可行压缩90主答。共138主+14工程152答4664tokens。
- 内墙钟900秒、外960秒、TERM20秒后KILL自有组；独立核验180/外200秒；归档≤256文件/128MiB，无服务/端口。

实际执行命令（已执行，不需接手者重跑）：

```text
CUDA_VISIBLE_DEVICES=GPU-4ce22e12-b5c0-e423-06c5-e858bb71daaa KV_SQUAD48_WATCHDOG=registered_960_seconds PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/run_squad48_study.py --execute --proposal-sha256 11f0f216ff2c18304760fbf8f818abe47ff72de98de53a3447a0c55ca76f3080
.venv/bin/python -B scripts/verify_squad48_study.py --proposal-sha256 11f0f216ff2c18304760fbf8f818abe47ff72de98de53a3447a0c55ca76f3080
```

同级launcher顺序执行并看守。worker PID1052050内126.48500907886773秒、verifier PID1053387内18.1680721337907秒、launcher PID1052047共145.824922200758秒，均exit0且退出。console保留Torch dtype弃用警告，不作性能测量。GPU收尾15MiB/0%，未操作他人任务。

新增入口/依赖冻结摘要：

| 文件 | SHA256 |
| --- | --- |
| scripts/reliability_squad48_study.py | ac71b3cec3f800e581769bd1d3146f030fdc9eabe583305f7934b168406453a4 |
| scripts/reliability_group_statistics.py | 1a87e8ee243a1159ca055ae317ac5acd9940722d4312bd06d597fe62f5f59169 |
| scripts/verify_squad48_study.py | 9a950c227534a1f0b4ace19767e05dceb90d4e271b3fe87e9a0bc015bb65e1c0 |
| scripts/run_squad48_study.py | c0677014c23297f92bcafa641ff05b7fa56a33348751fe1a859fbbdd70df48a9 |
| scripts/verify_hf_DEV_acceptance.py | 0bf578b3e342d3c2554c5134c6774559a876d06327e319fe15fad5e96cf69143 |
| scripts/squad48_study_acceptance.py | 8c44f8468e49d87c4d6e6d32df2cf12fdef553a6b979eaca55e630828c8463ad |
| docs/SQUAD48_GPU_PROTOCOL_20261030.md | 582caf5dd6f191e397510e68843f4be0ad950fc375d6d12bb01b625667c5c987 |

## 结果与证据

Full支持：任务34≥24、格式44≥36、错误0、截断0≤4；48均返回，joint31，支持true。计数在完成且未截断输出上，与输出前协议一致。

| 条件 | 生成/计划 | 严格任务EM | 严格格式 | joint/48 | 截断 | 预算不足 |
| --- | --- | --- | --- | --- | --- | --- |
| Full | 48/48 | 34/48 | 44/48 | 31/48 | 0 | 0 |
| Snap适配 | 45/48 | 3/42 | 0/42 | 0/48 | 3 | 3 |
| 随机 | 45/48 | 9/41 | 5/44 | 0/48 | 1 | 3 |

任务分母排除截断/候选N/A；格式分母仅排除截断。随机有3候选N/A，不能把它们当语义错误或删组。全部48组/144格保留，预算不足6格分别为3原题×2条件；0未运行主格。工程截断匹配只算路径验证。

主要差值两个条件均-31/48，95%逐项paired group percentile CI均[-37/48,-24/48]=[-0.7708333333333334,-0.5]，10000次共享组抽样/seed20261030/type7，抽样流SHA `25cf2b9062d5cfb9ebdcf60180665d0982d8aaff5c0fbf86c6a179bb38ec33e5`。相同区间源自相同Full与两个全0的joint向量，不是独立重复或方法行为相同。不是总体风险/同时多比较认证。

任务严格配对Snap42组、random41组；Full正确转错28/31、20/29，可用Full正确共34、未知配对3/5；覆盖边界[28/34,31/34]与[20/34,25/34]不是CI。格式严格配对42/44组，Full正确转错38/38与35/40。F1及不同分母、四转移、actualprefix/final byte区间、unknown成本均在scalar_report/readiness，不隐藏Full错误、截断或未知。

独立核验通过：138文本重新decode并独立重判、4622trace步、94文件10528层-head map逐一重算（Snap由前缀分数排序、random以空CUDA可见性CPU Torch重建）、4权重/6metadata/所有源输入hash；all48 joint/bootstrap与scalar任务/F1/格式配对复核。独立validator不import主scorer、study、core或统计实现，只使用既有独立scoring helper。97次prefill的unhooked cache与reference内容一致，重复prefix scores/mappings不变。真实gather/value/shape/bytes由已锁backend与本次工程/逐次检查完成。

原manifest 189项；独立核验/closure/derived/report收尾共194文件5567444bytes。原manifest未追改。完整raw、text、ids、prefix scores/maps、trace、工程证据、输入/运行快照只在服务器，不复制本地。主要工件摘要：

| 工件 | SHA256 |
| --- | --- |
| Full_support.json | 9ea03a9c04f0185b2f515d8521d6a4c72bf60f6b984b02c57718a5db6e0a46d0 |
| actual_runtime.json | 7135a8b5f6434587dc7940ed03542b4c4699a291002489c08014d918e7ec5248 |
| backend_execution_snapshot.json | fad162ebdbb4b01b44192785bc2dda8cb983bd2db94d0741df6a37a93b3de6dc |
| closure.json | b4f8cc71329de396dc356a1269481526dc4012caf77edb41b0226870226ecc8a |
| derived_manifest.json | 9efec84846e8fcb7cffc8ccdb14b96595a731c25fddcd7dc92f27f9c3bf9a95c |
| engineering_evidence.json | bc5e3c27e9659fd10df13c7edb4e7f6effd2032d1cb3ac63ca977dadf656b454 |
| execution_snapshot.json | 1290380ac37e9eb0caa82f490ab97c181c5e565614b76cc2b747bbd8b8b606b9 |
| group_statistics.json | c724d5bebf7613f89251b3b519da3451028ee0245fdc16d06878da2608a3c96c |
| independent_verification.json | 628d90150827c57f9b1ddb673ff7746f11a3596dc13145d9627900d1ae46c573 |
| input_manifest.json | 29d13dbd30ad7d57228c82e193fe32ca5aead28284a7924e1a9094ecd83bc668 |
| integration_software_acceptance.json | c3ec3a42ed70dd2419e2d4c78ce82c7a9ed91e5fd6e0c487c6b79e72e09bdb01 |
| manifest.json | 00eeb8eaa6e01317a160e88236d0c98aa27318f3019e086e1e69eced728644ee |
| normalized_outcomes.jsonl | 6025162b60e16568f30c4991c151a4fe78fbd634ec96f69a9cabbce16e0566d4 |
| proposal_snapshot.json | 11f0f216ff2c18304760fbf8f818abe47ff72de98de53a3447a0c55ca76f3080 |
| raw_engineering.jsonl | 328619e8669a997436e4c6288e52644caf71a2098433b11c511456ebd0ef2df6 |
| raw_main.jsonl | 6483ba6a9451292966bad169f6db32a4aa091af7673b9e67f9f77c5236b563ad |
| registered_runtime.json | df43c58ff386f4c18e2a41cf34c1798cd2f7bdfee0991f405b66658e6668d61b |
| report.md | cd5495ee74134b3125ed94640f477794ea58387228adc2a86a8bc37605ec4b5a |
| scalar_report.json | 214db4f521784993fa93a98c8aadd3ac0d571782c551232001fc38b8343844ad |
| scored_main.jsonl | 8b1ae1e4bd841e78ebdf59806ec0dbe4eba359444f94cd3b2d65dc4b261299dd |
| summary.json | ecd17d5ee9cdc09b20a8f7b99776f7cb2d9fa45b60fcac1e4b6a4b1a94d27faf |

新增1GPU run/138主要回答/14工程回答，累计119run3038主；索引`results/20261030-run-index-squad48-study.json` SHA `d1c405bde0f1c8b9da7c7059bdccf3be66631cbc843e98791c08295d2744aaea`，旧118索引1e9b651d…不改。代码配置文档同步服务器，GitHub未配置。

## 解释与下一步

本次补齐固定一模型/任务/预算/seed的独立于DEV文章组描述性证据，不完成原跨任务/双模型确认。任务和格式同时受损，不能称安全特异机制或新算法发现；普通JSON规则也不等同真实安全功能。两个joint都触底但EM不同，是单指标局限的具体案例。精确文章去重不证明语义/预训练独立。保护收益/总体安全/真实峰值或时延未测；审计保留Full reference，不报进程显存减半。

下一步离线整理已有138答的错误类型和系统/实证论文章节，明确贡献、覆盖和未完成项；不据本次错误调prompt/换题/补生成，不自动追加保护/3/4/BoolQ/Mistral/旧16矩阵。旧QA/Mistral支持false保留。STATUS/WORKLOG/HANDOFF、系统matrix/readiness与环境记录更新，当前无运行任务。

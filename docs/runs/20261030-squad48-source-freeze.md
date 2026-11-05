# 原48组来源与分组冻结

## 实验身份

2026-10-30，Asia/Singapore。用户在已授权实验会话要求“开始下一步”，按[执行注册](../SQUAD48_SOURCE_FREEZE_PROTOCOL_20261030.md)实施[禁用历史提案](../../configs/squad48-scope-freeze-v1.json)的CPU准备。服务器绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-squad48-scope-freeze-v1`。研究问题是原预留48文章组的身份、原选择规则和来源排除是否保持，并冻结全部计划cell；不是模型推理或独立科学效果确认。

**状态complete，独立复核passed。** 单次CPU run，0模型/工程回答、0tokenizer编码、0权重/前向/GPU/网络，未下载或更改依赖。144格仅planned/not_run，不冒充生成结果。

## 可复现条件

固定proposal SHA `b1b975718152a4747ed25527f892a04224253d3b4ee0a7c5088ef9bd1420304f`，runner `73609092b067335aa9835db73154780f2db2ff1234120947a49755d8dcddc55a`，独立validator `4aa481d1c69d3a8560dca0baff255d1006625539088b9f520c9bc040aa29efe3`。项目未配置Git远端，以源码SHA和不可变snapshot定位。原proposal execution/runner=false字段保持历史原样，实际CLI/source SHA及execute权限另存，不因旧false重复已完成目录。按用户约定本地仅代码/配置/文档；原始文件与输出只服务器，不访问nano-vllm。

已有train-v1.1原文30288272bytes/SHA3527663986b8295af4f7fcdff1ba1ff3f72d07d61a20f487cb238a6ef92fd955及整个历史dev4854279bytes/SHA95aa6a52d5d6a735563366753ca50492a658031da74f301ac5238b03966972c9，raw合计35142551bytes；15固定输入及历史dev共16个SHA核验，总输入35489314bytes。保持原4工程/12DEV/48预留、原顺序和所有原字段，未重抽样/选长题/改gold或prompt。旧16封存仅历史来源文本做排除，无模型访问。

标准库Python3.11.13，加载前核已有answer_format_task.py SHA58783b7b…才使用其中纯标准库source validation和union-find；不导入旧network runner/scorer或模型/tokenizer。offline环境、CUDA_VISIBLE_DEVICES为空，audit hook拒绝模型库import、模型/权重文件打开、socket及子进程；所有禁止事件计数0。无GPU探测，旧读数不作本轮测量。

内部90秒/外层120秒watchdog，TERM后10秒仅自有进程组，raw源≤40MiB/归档<32文件16MiB。实际worker1022354内1.769917秒、launcher1022351共1.869884秒exit0，UTC 2026-10-30T14:09:30.659515+00:00—2026-10-30T14:09:32.529578+00:00；未超时、无失败/重试，两个PID均退出，无服务/端口/后台队列。

实际命令由归档launcher设置KV_SCOPE_FREEZE_WATCHDOG及离线env后运行，禁止裸跑重试：

```bash
.venv/bin/python -u scripts/freeze_squad48_scope.py --execute --proposal-sha256 b1b975718152a4747ed25527f892a04224253d3b4ee0a7c5088ef9bd1420304f --runner-sha256 73609092b067335aa9835db73154780f2db2ff1234120947a49755d8dcddc55a --validator-sha256 4aa481d1c69d3a8560dca0baff255d1006625539088b9f520c9bc040aa29efe3
```

## 结果与证据

- 重建全部442篇train文章组件，87599问题ID唯一、87599原标注span与原文slice全部精确相等；原git blob/完整SHA匹配。
- 原selection seed、组件hash顺序、组件内问题hash最小选择及4/12/48角色逐项重放，64行的ID/group/文章段落坐标/标题/正文/问题/全部gold/prompt及摘要/边界/原provisional字段完整相同。64个不同组件、64个不同题，未替换任何预留题目。
- selected48.jsonl严格为原sealed_descriptive_evaluation48行原顺序，保留provisional_cross_task_overlap=true；当前scope另声明SQuAD-only，并不把BoolQ跨任务false改true。
- 完整64个选中文章组件的规范标题及所有段落集合彼此无精确交集，也与整个历史dev48篇文章无精确交集。由原完整文章集合检查，而不是只看选中问题段落。精确去重不保证语义无近重复、全领域独立或预训练未见过。
- 全48题×Full/半预算Snap/半预算原seed random共144唯一格按源顺序归档。Full一次共享参照的计划身份明确；每格execution_state=not_run、budget_state=not_checked、工程未注册、指标null/model_called=false。当前没有tokenizer/KV预算、Full支持或新工程通过证据。

| 输出 | 数量与状态 |
| --- | --- |
| 原64题重建检查 | 64，全部与冻结选择一致 |
| 预留来源清单 | 48题/48组件，原顺序保留 |
| 计划cell | 144，3条件各48，全部未执行 |
| 新模型/工程回答 | 0/0 |
| 分词/模型前向/权重/GPU/网络 | 全部0 |

独立validator只用标准库构建共享规范标题/段落邻接图后BFS，与runner的union-find分开，不import原runner/组件库。它重验87599标注、全部64原选择/提示摘要和48身份顺序，逐组件核完整文章集合的历史/当前交集，以及144cell唯一键/条件/身份绑定/未测状态；原manifest、source snapshot与16输入hash一致。独立结果passed、额外模型/分词调用0。

原manifest15项；后验independent/closure/derived另存不覆盖原manifest，最终19文件448605bytes，另同级launch/console/launcher全部原样留档。重要SHA：

| 工件 | SHA256 |
| --- | --- |
| manifest.json | 20ab6ff77770c8597154d1a9259865602b4e6a16ba123ce41183d6ba3d8a2455 |
| summary.json | 87f887e93eb1c351348c48a3f748a33a2880011c4b72b8b8e22a08ccb92cdf63 |
| input_manifest.json | 1874ebca0acf8bac40397736e18be5a75b53446570db3ac770c45ea3ec80e475 |
| selected48.jsonl | 993ae6a45e4b041181e3aeed4d90afabc509d54f99ed0a20e5436492a50731af |
| planned_cells.jsonl | f256ae916c1d151e887aee22415f4be00387087088b853c9a03ac5b39a1e50aa |
| component_revalidation.json | 7a4e35d3b0ca38e27e11f4a32f82bd01e5e4174f95289c8398d1890409e25e1d |
| source_case_checks.json | 23f2cf359a029fe06c54ff6f43674018ea6a87e6aae78fb36f6e61ba763952f9 |
| scope_manifest.json | 3af6c3b5758f833e7125f45ec149592bd57da35805973eae13e2e22a61a6f3d3 |
| CPU_guard_observations.json | 22de7212fb35770c3a51a529395d44c03b5d33836b7508e89fa3fdc6400afc9b |
| independent_verification.json | 6afce6f9fecccd9070538fbcd0d5a91990d2d7f9290c81362d9e16427a90fe94 |
| closure.json | d8b758be2632f7a6483970bc480a5aa6288fbc8b652b3a8d0b2e15cdd17faf78 |
| derived_manifest.json | 7c403c95b2d7fb6f0b1aab500af955fc7e53184e8e01602970854fed15e0486d |

同级工件hash、完整来源计数与guard见[readiness](../SQUAD48_SOURCE_FREEZE_READINESS_20261030.json)。原始text/答案/ID/计划清单仅服务器，本地不保存实验数据，代码配置文档两端核SHA，GitHub未配置未push。

## 解释与下一步

当前已完成的是新SQuAD-only子研究的原48来源身份/文章组排除核验，不是原跨任务BoolQ分组完成，也不是48题科学确认。旧QA gate=false、Mistral当前Full支持false及停止决定不变；旧16封存不启用。保护/3/4仍不进入最小主矩阵，不能以当前计划清单反推其适用性。

下一步已写[Qwen48原生前端CPU提案](../../configs/squad48-native-preflight-v1.json) SHA `15dfe0e7294b5b8fbb137dedd4952907447058e5481de7940631cd7190551913`，execution=false/runner=false，未实施。固定当前selected48 SHA、原Qwen snapshot/6metadata/template及96编码上限，只核原48完整native ids/问题边界/header/半预算anchors可行性、把144planned格补上预算状态；预算不足保留，禁止填充/删题/改提示。0权重/GPU/网络，无额外工程替代query或对预留题调试改写。

CPU前端通过后仍需统计模块边界/独立验收，以及另冻GPU来源/runtime/工程证据适用关系和Full支持/输出/墙钟协议；本轮不直接启动144格。来源独立不等模型支持，预算可行不等工程通过，144回答不是144个独立样本。

新增1CPU run，0主/工程回答，累计116run2900主；新索引`results/20261030-run-index-squad48-source-freeze.json` SHA `5134913f864aec8b81502a0984eceb8e56fcbd1b5fd48142005a8a07b6f4b92e`，原115索引保持。STATUS/WORKLOG/HANDOFF及系统matrix/readiness更新，环境/依赖无变化，当前无运行任务。


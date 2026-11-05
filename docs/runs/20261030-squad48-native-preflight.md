# Qwen48原生模板与半预算CPU预检

## 实验身份

2026-10-30，Asia/Singapore；用户在已授权实验会话要求“开始下一步”，按[执行注册](../SQUAD48_NATIVE_CPU_PROTOCOL_20261030.md)完成固定[CPU提案](../../configs/squad48-native-preflight-v1.json)。服务器绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-squad48-native-preflight-v1`。问题是冻结的48题能否原样编码、按原生问题边界缓存prefix，以及半预算anchors是否可行；不是实际KV/Full支持/模型效果实验。

状态**complete，独立复核passed**。单次CPU，48完整native输入/96编码、144预算计划状态；0模型/工程回答、0权重/前向/GPU/网络。原题和48组全部保留，未修改预留问题或增加替代问题探针。

## 可复现条件

proposal SHA `15dfe0e7294b5b8fbb137dedd4952907447058e5481de7940631cd7190551913`，runner `bfc7bc406467e1b491e54ab2f1b0e9429d714fa4c6023ad395fb564ea8a02912`，独立verifier `cc76da868f43280773350073d125f5dce0bfcf5124675664a2810f44bcd6c3c2`。原execution/runner=false提案保持历史原样，实际source SHA/CLI/execute权限另存snapshot；不据false重复已完成目录。项目无Git远端，代码配置文档逐SHA标识。

来源为[已冻原48](20261030-squad48-source-freeze.md)，selected48 SHA993ae6a4…、原144plan f256ae91…；8输入SHA及父原/后验manifest全核。Qwen2.5-7B-Instruct固定a09a35458c702b33eeacc393d103063234e8bc28，6metadata与模板cd8e9439…摘要不变。复用effective_offsets/budget_plan的本项目纯CPU helper，源码2a356d6d…和ea87bd0d…单独锁定并归档；没有执行旧main或修改数值生成器。

既有Python3.11.13、Transformers4.57.1/tokenizers0.22.1/sentencepiece0.2.1/protobuf6.33.0/safetensors0.6.2不变。USE_TORCH/TF/FLAX=0、HF离线、CUDA_VISIBLE_DEVICES为空/禁止bytecode，仅本地AutoTokenizer/AutoConfig。guard限定原/解析后HFblob的6metadata白名单、拒绝权重/其他模型目录、模型库import、外联/socket绑定及子进程。固定urllib32.3.0 _has_ipv6 ::1:0可选probe1次仍在操作前被OSError阻止，单列记录；其他禁止事件0。console无Torch/TF/Flax提示是预期CPU保护，未安装依赖。

内层90秒/外层120秒watchdog、TERM后10秒仅自有组，2048输入token/96编码/32文件32MiB。实际worker1026473内2.926653秒、launcher1026470共3.121825秒exit0；UTC 2026-10-30T14:17:17.891967+00:00—2026-10-30T14:17:21.013969+00:00，无失败/重试/超时。两个PID退出、无服务/端口/后台队列，GPU当前状态本轮未测，不沿旧空闲读数。

实际命令由归档launcher设置离线env和KV_NATIVE48_CPU_WATCHDOG后调用：

```bash
.venv/bin/python -u scripts/preflight_squad48_native.py --execute --proposal-sha256 15dfe0e7294b5b8fbb137dedd4952907447058e5481de7940631cd7190551913 --runner-sha256 bfc7bc406467e1b491e54ab2f1b0e9429d714fa4c6023ad395fb564ea8a02912 --validator-sha256 cc76da868f43280773350073d125f5dce0bfcf5124675664a2810f44bcd6c3c2
```

完整args/env范围与source快照只服务器，禁止脱离watchdog或复用旧run目录直接重跑。本地只有代码配置文档，不保存48输入/offset/结果。

## 输入、边界与预算结果

原48题ID/顺序/role/prompt/gold/完整问题保持；每题Qwen完整system/user/assistant原生字串逐字校验，fast offset编码与apply_chat_template(tokenize=True) ids相同，共96API编码。没有对预留问题增加替代query或调试性改写。

prefix只含原question_start_user_character前token，完整ids无损拼回prefix/suffix；system/native framing全部字符覆盖、header索引均在prefix内。跨query token若出现会留在suffix，zero-offset控制token仅在有已知literal/ID证据时映射；本run实际这两类记录均0，不声称通用分支已实测覆盖。

| 量 | 实际前端范围 |
| --- | --- |
| 完整input token | 111–492 |
| prefix token | 94–472 |
| suffix token | 10–34 |
| 完整header token | 56 |
| 半预算floor槽数 | 47–236 |
| BF16 K+V bytes/slot | 57344，配置推导，非新tensor测量 |

主矩阵无完整system保护；56header仅归档，不额外计入无保护选择。固定sink4+recent64并集68槽，本批prefix都>68；半预算小于68的3题标infeasible，不padding/换题/删短题。Full为n槽、压缩为floor(n/2)，同题两个压缩条件预测prefix字节相同。

| 条件 | 计划 | 数学可行 | 数学不可行 | 已执行 |
| --- | ---: | ---: | ---: | ---: |
| Full | 48 | 48 | 0 | 0 |
| adapted_snapkv | 48 | 45 | 3 | 0 |
| uniform_random | 48 | 45 | 3 | 0 |

因此144格中138数学可行、6格预算不足（对应同3原题×2压缩条件）。若未来Full支持与工程/执行协议成立，主要回答上限为48+45+45=138，而非必须凑144回答；144计划格及所有48组仍保留。3题不被移出文章组分母，预算不足的语义分数仍null，不能按“只剩45题”重报总体方法优势。

所有execution_state仍not_run、model_called=false、metricsnull；可行格的admission为await_current_cohort_engineering_and_GPU_protocol，未借用旧14工程观测或产生新Full支持。CPU输出Full_support/engineering_gate=false意为未生成pass，不是实测Full失败。Qwen既有DEV支持和旧false gate也不受影响。

## 独立复核与归档

独立stdlib verifier不import原runner/helper/transformers、额外编码0；从原48文本逐一重构native串、问题字符位置、offset连续prefix/header覆盖，再用独立集合/整数floor公式重算Full/half槽数和预测字节。48顺序/组/输入gold绑定、144原唯一键/顺序/旧字段、6metadata/模板/8输入及父manifest全匹配，严格验证计划依旧not_run与指标null。两编码API和固定包版本提供实际编码对照，不冒称独立复跑tokenizer。

guard metadata打开11次；非白名单读/模型import/外联/子进程均0，已知本地能力probe1次被拒绝，权重读取/模型前向/GPU查询0。原manifest18项；后验verification/closure/derived分开不覆盖，最终22文件1926244bytes，另同级launch/console/launcher原样仅服务器。输入共278546bytes，原始ids/render/offset/预算只服务器。

| 工件 | SHA256 |
| --- | --- |
| manifest.json | 835ae7a8ddc479666b7eafab833fda53665846b96ce06543ab97d8fea7e7ea7d |
| summary.json | f19241c952cabdf5e5a1e6c9fcda197b5050b4f7d8304b7f7ff8f5abd5823de7 |
| input_manifest.json | f123bcf0981461bc669453ee2a8a90c4b0ee8c5ffa3946f685f9a9cf0943bdfe |
| execution_snapshot.json | d81c596149188d09c160b66002dbc4fe498e76d81e3d98cd1194cfe1f90d724e |
| metadata_checks.json | 86d90b6b795bddd3ccfc25831b42178ea63a0e16eee850372d31f11ceea479c2 |
| tokenized_cases.json | d2bbd05cfd146dfd334c3bef017da32e114500f81e060e8f7bde900d6fbebd65 |
| native_variants.json | 3a6a82026c6038baa4c26e7ce67a3e55a8c88648cf4a9a8d515c8f033fbcfd2e |
| planned_cells_with_budgets.jsonl | 287703323b534250e9e30876b45fced994547a7e583a029fd2c19208a0b29c47 |
| coverage.json | f875cef73f9b1d41b92334e4f72cabfd2855fbc617910f93b9b91cc0b44f43b4 |
| CPU_guard_observations.json | 2e7397b71a4f7d42c6f159c2b2c91d296468c5cf1b082c848803df31fadfb998 |
| independent_verification.json | 4a9e7ff75ab195cec9f34b3f698977a85e2b4cc689d5c976c03158fb4faf69c9 |
| closure.json | 5e1058ee65ce9c1993ed1d396a991713bab870889e0084751dcce3ea165250f8 |
| derived_manifest.json | 682b6f859fc418a612e5b843b2f78ae1c94ff56c8044f77a46072df88f7ea463 |

外层工件完整hash、条件范围和guard见[readiness](../SQUAD48_NATIVE_READINESS_20261030.json)。代码配置文档同步服务器核SHA，GitHub未配置未push。

## 解释与下一步

48题原生前端和预算覆盖已通过受限CPU检查；这不等真实tensor、模型能力或独立科学确认。预算不足是协议内结果，不是要修复题目的理由。旧Mistral支持false/停止队列、旧QA false、保护3/4/BoolQ暂停保持，无新模型答案/依赖变化。

下一步已冻[组级统计CPU验收提案](../../configs/group-statistics-acceptance-v1.json) SHA `b1e9d0420b530a745f84a4a72435bdf25238cb7b7916d2177279cb8bf0cc3126`，execution=false/runner=false，尚未实现/执行。18个软件用例涵盖完整配对、精确两组枚举、常差值/零差值、预算不足/截断/N/A、重复/缺失/身份错配、group膨胀、seed复现、Full支持失败与分母0，以及当前144格planned不能计算实际效应。拟用10000次同组共享配对抽样/seed20261030、95%逐项percentile区间、type7分位插值；不是风险认证或多比较同时保证。

统计必须保持全部48计划组；不可行joint交付可记0而语义null，截断/未知覆盖单列。仍处于pending或因Full支持失败整阶段停止时，不得把全not_run清单计算成“效果为0”的区间。软件fixture不算科学样本；本轮只写了提案，没有对48题计算任何模型效应。

统计模块验收后，另冻GPU输入/runtime/role和同条件工程证据规则、Full支持/停止线与≤138主要回答/工程资源上限；不直接修改旧engine的sealed角色白名单或注入旧证据。当前没有GPU队列。

新增1CPU run/0主工程模型回答，累计117run2900主，索引`results/20261030-run-index-squad48-native.json` SHA `724817ec9be87353cd75afde2b5c9121ca5c2276a833c1ab5eb9bdab842ad38b`，旧116索引保持。STATUS/WORKLOG/HANDOFF/系统matrix/readiness更新，进程均退出，当前无运行任务。


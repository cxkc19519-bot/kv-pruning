# 两模型原生前端与预算CPU预检

## 实验身份

2026-10-30，Asia/Singapore；用户在已授权实验会话要求“开始下一步”。按[固定执行注册](../INDEPENDENT_FRONTENDS_EXECUTION_PROTOCOL_20261030.md)和[v2修订](../INDEPENDENT_FRONTENDS_AMENDMENT_20261030.md)完成。研究问题是两模型能否原样表示相同输入、完整保护边界与两预算的可行覆盖；自建前端检查，不是模型任务/裁剪/安全或性能实验。

服务器绝对目录：
- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-independent-evidence-frontends-preflight-v1`：failed，最终访问守卫分类失败，原工件保留。
- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-independent-evidence-frontends-preflight-v2`：complete，独立复核passed。

新增2CPU run，0主/工程模型回答、0模型前向/权重/GPU/网络请求，48封存不编码。本地仅代码/配置/文档；全部输入ids、offset、native文本、失败与console只服务器。未访问/复制nano-vllm，也未改当前模型KV/评分/旧实验源码。

## 可复现条件

固定原SQuADtrain64组source SHA20f45408…，按原顺序取4工程+12DEV，两个模型各16题。额外2工程题仅CPU编码，不替换旧2题GPU证据。原system/user/question/gold和字符边界不改，不筛长题/填充。Qwen固定a09a35458c702b33eeacc393d103063234e8bc28，Mistral固定c170c708c41dac9275d15a8fff4eca08d52bab71；Qwen6与Mistral10元数据/模板摘要匹配，唯一文件合计14798934bytes。未读权重，模型文件存在性不等本轮权重校验。

现有Python3.11.13/Transformers4.57.1/tokenizers0.22.1/sentencepiece0.2.1/protobuf6.33.0/safetensors0.6.2不变。USE_TORCH/TF/FLAX=0、HF/Transformers离线、CUDA_VISIBLE_DEVICES为空、禁止bytecode；仅AutoTokenizer/AutoConfig，未导入torch/tensorflow/jax/vllm。库提示未发现Torch/TF/Flax并限制模型使用是预期保护，未安装依赖。

原提案v1 SHA `83136793b35bd7935a17c34949dec3330527e81968e7c7ae13be782807273e04`，v2 SHA `df3243f33b3ea96bc5a7c8b2808439a7c32bb5e3a678083c34620d2d5824839d`。新runner/validator SHA见[readiness](../INDEPENDENT_FRONTENDS_READINESS_20261030.json)；项目无Git远端，以快照SHA标版本。旧提案false字段保持历史原样，实际CLI注册另存execution snapshot，不据false/true重复已完成目录。

内部120秒/外层150秒watchdog，TERM后10秒仅自有组；96编码/128预算评估每run，32文件/32MiB、2048输入token。150秒外层没有触发。实际v1 worker987652/launcher987649，内3.973699秒、外4.124768秒exit1；v2 worker990438/launcher990435，内3.736171秒、外3.924029秒exit0，四PID均退出，无服务/端口/后台任务。本轮未查GPU，不沿旧15MiB/0%称当前空闲。

实际v2命令由固定离线env和KV_FRONTEND_CPU_WATCHDOG=registered_150_seconds的launcher执行，完整参数/源码/UTC归档：

```bash
.venv/bin/python -u scripts/preflight_independent_evidence_frontends_v2.py --execute --proposal-sha256 df3243f33b3ea96bc5a7c8b2808439a7c32bb5e3a678083c34620d2d5824839d --runner-sha256 2a356d6d8a37580b8ad66bb5c7f54e52b12592cb23cfd3b44b2670a52f95fcb3 --validator-sha256 ef9cd3607e8b16ffbd4ef7de5fc71ba3666ad381b5b40e3dc430943c69ad95c3
```

不要脱离watchdog重跑；目录存在即拒绝，当前无待执行GPU命令。

## v1停止与v2修正

v1已完成全部48完整native变体、96编码、32model/case与128预算计算，但最终CPU_boundary_guard失败。守卫记录forbidden_read=0、subprocess=0、network_attempt=1；原始状态仍failed，不把前端已算完说成原run成功。原manifest15项，后验加诊断/closure/derived，最终19文件2437556bytes；manifest `e85b93f7d0e43b6e5e53c36382e0a3ec2449c66f4be26ca8714d64a9c3a54208`、derived `70ab554e3fc50c8976c5c1fa7c061c1d0a00ba0635e591cced0cce04ca86f4e9`。

单独离线import-only诊断0编码/0tokenizer构造，定位urllib3 2.3.0的_has_ipv6对('::1',0)调用bind；操作在发生前被OSError阻止。没有外联、下载或实际绑定。诊断SHA `4348b88c0b6c98ab4c9fd23ca8156e4be67d544b7b24c1bdad90c5cfd53e67ed`，依赖源码SHA `2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74`。早先guard把可选的本地能力探测归为禁用网络尝试，导致保守失败。

v2执行前另冻修订：仍拒绝精确bind，只有固定地址、事件、caller、源码SHA/version匹配时，记录blocked_loopback_capability_probes=1；其他网络尝试仍失败。HF symlink原路径/真实blob路径的白名单同时收紧，原路径和解析路径的权重后缀都拒绝。没有允许任何网络操作或改变认证。

v2的48native变体/32tokenized rows/128预算工件与v1逐SHA完全相同，说明修正不改变编码/边界/预算结果。两次合计192编码/256预算计算为技术重复，唯一对象仍32个model/case、48变体/128预算格；不是新增独立样本。没有根据已经看到的预算结果改变样本、retention或保护范围。

## 原生边界与预算结果

每模型16原问题+4工程×2固定替代query=24完整对话变体，共48；每种fast offsets编码与apply_chat_template(tokenize=True)两路径一致，共96API编码。另每模型1次system-only探针仅渲染不编码。Qwen原14条input ids/prefix/suffix/header/prompt精确重现旧文件，32个base输入无损拼回，全部工程三query的prefix ids一致。当前样本zero-offset映射及跨query token数均0，不能据此宣称这些通用边界分支已实测覆盖。

Qwen使用原生system/user/assistant标记，Mistral使用原生BOS+[INST] system+两换行+user [/INST]；Mistral仅system探针只给BOS，故缓存由完整native串定位，不能用BOS充当system资料。system/native前缀frame的字符覆盖与token集合独立核验，范围内不漏字、不含未来query；两模型角色封装不同，比较保留该适配差异。

| 模型 | prefix token范围 | suffix范围 | 完整header token | BF16 K+V字节/槽（配置推导） |
| --- | --- | --- | --- | --- |
| Qwen | 146–312 | 12–27 | 56 | 57344 |
| Mistral | 154–359 | 9–24 | 59 | 131072 |

sink4/recent64与完整header并集收费；本样本并集Qwen120槽、Mistral123槽，无padding或增预算。1/2和3/4早已列入原独立实证草案，此处仅元数据预算计算，不改变旧半预算实验。

| 模型 | 保留率 | 保护模式 | 工程可行/4 | DEV可行/12 |
| --- | --- | --- | --- | --- |
| Qwen | 1/2 | anchors_only | 4/4 | 12/12 |
| Qwen | 1/2 | complete_system_union_anchors | 1/4 | 2/12 |
| Qwen | 3/4 | anchors_only | 4/4 | 12/12 |
| Qwen | 3/4 | complete_system_union_anchors | 3/4 | 12/12 |
| Mistral | 1/2 | anchors_only | 4/4 | 12/12 |
| Mistral | 1/2 | complete_system_union_anchors | 2/4 | 3/12 |
| Mistral | 3/4 | anchors_only | 4/4 | 12/12 |
| Mistral | 3/4 | complete_system_union_anchors | 3/4 | 12/12 |

全部128格保留，没有仅报告可行题。3/4下两模型DEV完整保护均12/12数学可行，是后续独立实证的预算覆盖信息；不是保护效果/工程路径通过。原先固定的两工程题中第一题在3/4仍保护不可行，所以不能直接把原两题工程gate设pass。4题工程池其余可行数仅作CPU清单，未来若需要条件级工程覆盖，须单独冻结范围，不能冒用旧证据。

## 独立核验与工件

v2独立validator仅标准库、未导入原runner/transformers/模型，额外编码0；核16输入SHA、16model metadata/模板、48渲染与原样source问题/角色、offset字符覆盖与prefix边界、工程query前缀相等、原Qwen14精确回归。128预算用另一份Fraction floor/集合/每层K+V字节公式重算，8行model/retention/protection覆盖分母4/12一致。独立原manifest、v1/v2数组SHA、source快照、外层PID/exit核对通过。

v2守卫实际model metadata open事件28，未白名单/权重尝试0、外联尝试0、子进程0；固定回环探测1次被阻止，真实网络请求0。没有GPU查询或模型前向。原manifest18项；后验verification/closure/derived另存，最终22文件2449492bytes。重要SHA：

| 工件 | SHA256 |
| --- | --- |
| manifest.json | bf93207d3cc6e110d625e6e4eb56e6caacf2bd55e6399628da2d470726d2571c |
| summary.json | cde07b1340d9a0ae8c44cbe56e9c509be144013d2ae78ced825ac715434eb4c5 |
| execution_snapshot.json | 9c091824286434a356c6f6e9fe33e6cc6b069b8993e0eb6c4a004f65297a167e |
| tokenized_cases.json | 75d33d34bc6979c3e9aa63120096748234d322a1196fc7f81845f8957a45d8c9 |
| native_variants.json | 42de914fa9e0932d08a83669ceacebcc176979d2c9e0f933ffd89d89b92074ef |
| budget_evaluations.json | 97074e150f5efc27cfe8c948a99e19eea20cef0685079fdebfac04ca27786daa |
| budget_coverage.json | 7e226785b5f74b53533e4fb30f8009d5f5bed3656ac6c270c16208ce9da7a4b0 |
| CPU_guard_observations.json | 382e182a3ead7c311977fddf2a3150601ca27f29ba37ca65f81a3e0f0b47c7fe |
| blocked_socket_probes.json | b73d05356cbb47360f9c6b0c16a5c8f8c574b572b037259f563a97c04f738abd |
| independent_verification.json | bd66f2bbcefbb9d20ae896451f1967b424b0bae88680de633cb4ff4094615d1c |
| closure.json | 181537ed29b495961e3d8f4a4f12735da12602c7c8acc95e6544aeb990bf7856 |
| derived_manifest.json | 23c50b2171753d934bb572b7db88151c899c680ead83d7946982c0a471cc305d |

两run各自launch/console/launcher SHA见readiness。原始只服务器，后验不覆盖原manifest，代码/配置/文档同步逐SHA检查，GitHub未配置未push。

## 解释与下一步

直接结论：两模型当前QA原生前端/保护边界已通过CPU检查，预算覆盖在模型及retention之间不同；配置推导字节与数学可行性不等真实tensor/生成正确性或任务能力。Mistral当前任务Full、缓存三路径与compact仍未测；现有Qwen后端仍不支持Mistral/3/4，不能仅改配置称迁移完成。安全、正常任务成绩和性能本轮均没有新增观测；旧QA gate=false/旧16与新48封存、BoolQ403及HF缺title问题不改。

下一具体任务：冻结Mistral Full-only协议，原前两工程题各整段native/分段native/custom共≤6工程，再固定12DEV Full≤12回答，0压缩/保护/封存。先重核3权重/32Full/BF16/SDPA真实cache131072bytes-slot、clone/reference和三路径，再按原Full支持门槛（任务≥6/12、格式≥9/12、错误0、截断≤1）报告；不过则停该适配，不修提示/换样本。工程范围与新实现源码须先锁定；本轮未启动该GPU任务。

新增2CPU run含1failed、0模型回答；累计114run2888主，当前索引`results/20261030-run-index-independent-frontends.json` SHA `491e4cbbd5986ffc8aa56197852047b650efc63d74475c04e5d7e06d158828a1`。STATUS/WORKLOG/HANDOFF和验收矩阵/readiness更新，旧113/112索引与所有失败保持。四PID退出，无运行任务，环境/依赖无变化。


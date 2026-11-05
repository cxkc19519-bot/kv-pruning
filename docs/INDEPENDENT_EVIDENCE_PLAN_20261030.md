# 独立实证推进方案：从系统验收到模型与覆盖边界

2026-10-30。用户“开始下一步”。本轮完成证据盘点、原始来源复核和下一CPU阶段注册草案，**没有新实验、分词、模型回答或GPU任务**。当前系统主链已验收，独立实证仍待补，停止重复现有12DEV或14工程回答。[验收矩阵](SYSTEM_ACCEPTANCE_MATRIX_20261030.json)逐项区分已过/部分/未测，[来源与服务器只读核验](INDEPENDENT_EVIDENCE_SOURCES_20261030.json)记录依据；以本页取代旧草案中的执行顺序，不修改已冻结旧提案或失败gate。

## 研究问题和可以主张的范围

当前面向的问题是：**在相同实际prefix KV预算下，如何同时报告输出约束、任务正确、完整保护可行覆盖和失败不确定性，避免仅在少量可运行样本上报告漂亮的合规率？** 系统实现/可复核实证是用户接受的硕士路线，但具体题名、工作量和贡献仍需导师认可。现在不能主张新压缩算法、首个诊断平台或普遍安全漏洞。

直接近邻已覆盖指令退化与保护策略、Full逐源配对及适用性诊断、相对Full风险校准。因此本研究把这些作为背景与对照，不把它们单独包装为创新。[Pitfalls](https://aclanthology.org/2026.acl-long.1926/)、[KVDiagnosis v1](https://arxiv.org/abs/2608.09412v1)、[Risk-Controlled v1](https://arxiv.org/abs/2609.27981v1)本轮仅重读官方摘要，未复现作者实现或新增全文新颖性认证。

本阶段的问题固定为：
1. 同预算保护相对无保护，分别产生多少格式修复、任务损坏/改善和joint交付变化？
2. 加入预算不可行、工程未验、截断和任务N/A后，可评估覆盖是否足以支持策略判断？报告不足本身也是结果，不要求排名翻转。
3. 在新文章组及另一个普通Full Attention模型上，方向与适用边界能否复查？同一12DEV换模型仍是开发诊断，不算独立上下文确认。

## 系统验收结论与缺口

| 项目 | 现有证据 | 尚缺 |
| --- | --- | --- |
| 来源/身份/失败归档、条件准入与恢复、双判分、统一报告 | 新版HF端到端36实际回答+24阻止格；60格逐行/评分/分母复核，v1失败保留 | 未经新来源/新模型验证不称通用 |
| 原生模板、真实KV布局、gather与逻辑/物理位置 | 当前SQuADtrain Qwen两工程题/3可行条件通过；同12DEV回归通过 | 当前保护条件工程未验；Mistral新任务前端/裁剪未验 |
| 预算及覆盖 | 半预算20DEV格不可行、4保护证据不足，全部保留 | 需预先报告两模型和两预算的完整可行覆盖 |
| 真实资源成本 | Qwen prefix/final KV字节有观测 | 额外buffer、peak allocated/reserved、同步阶段时间未测 |
| 独立实证与总体结论 | 当前12DEV仅开发与系统回归 | 48新文章组未推理、跨任务来源/去重未完成、第二模型与统计不确定性待补 |

旧SQuADdev16已有保护工程通过，但其确认gate仍false，不与新train保护未验状态混用；旧封存16不重新开放。新增train64角色为4工程/12DEV/48封存，48队列不参与当前调试。累计112run2888主回答包含重复开发，不能当独立样本量或论文工作量。

## 下一步优先做两模型CPU原生前端与预算预检

选择这一步，是因为第二模型权重已经存在，而BoolQ新来源仍有身份/分组问题；先解决不用下载新材料就能推进的迁移缺口，不等待来源重试。新[CPU提案](../configs/independent-evidence-frontends-preflight-v1.json)保持execution=false/runner_implemented=false，**本轮没有实现或运行该runner**。

- 输入只用原4工程+12DEV，每模型16题，顺序不变，0封存；额外2工程题的CPU编码不等于替换此前固定2GPU工程题。原文、system、user、gold、角色与问题字符边界均不改，禁止按长度/预算/模型分数过滤或填充。
- Qwen固定a09a35458c702b33eeacc393d103063234e8bc28，Mistral固定c170c708c41dac9275d15a8fff4eca08d52bab71。服务器Qwen6/Mistral10元数据SHA全部匹配；Mistral3权重分片存在/大小匹配，本轮未读权重正文或重新核其SHA。
- 固定Mistral[作者config](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/raw/c170c708c41dac9275d15a8fff4eca08d52bab71/config.json)为32层/8KV-head/滑窗null；BF16描述符应为131072bytes/slot，Qwen为57344。前者不是本轮新张量观测，Mistral旧权限任务Full工程通过也不能替代当前QA/cached-compaction验证。
- 继承原独立实证草案已声明的1/2和3/4保留率，仅计算可行性，不调整旧半预算结果，也不把3/4配置直接塞入现有只支持1/2的HF后端。每模型/同case/同预算的保护、无保护按真实K+V字节等量；跨模型同保留比例不代表同绝对字节。
- 每工程题原问题+2固定替代query，DEV只原问题；共48种native渲染，每种fast offsets编码与apply_chat_template(tokenize=True)对照，最多96编码。推断顺序、运行上限与版本完整写在CPU提案。
- 原始完整ids无损分成prefix/suffix。按完整native文本和question_start_user_character定位问题，跨越边界的token整体留在suffix，prefix不得包含query；3种query的prefix ids必须相同。全部system字符及相关native framing token完整纳入保护且记费，原Qwen14条必须重现旧ids/header/prefix。
- Mistral以其官方完整BOS+[INST] system+两换行+user [/INST]渲染为准。system-only调用只给BOS，不能当system缓存；不能套Qwen角色标记。Qwen与Mistral原生角色封装不同，保留该跨模型适配差异，不把结果差异只归因于权重。
- sink4/recent64与system保护取并集，floor精确比例预算；2模型×16题×2预算×2保护模式=128预算评估。逐格保留infeasible；分别报4工程/12DEV可行数量，不通过选择长段落让保护“可做”。
- USE_TORCH/TF/FLAX=0，离线本地tokenizer/config，120秒内部/150秒外部、96编码、2048输入token、16MiB metadata、32文件/32MiB归档、0网络/权重/GPU/模型前向。模板/摘要/编码/边界错误停止；预算不足是预期可记录状态，不等技术失败。

该CPU结果只回答“输入和预算能否按约定表示”，不产生工程通过证据，也不决定新模型任务支持。Qwen旧14条重核仅为前端回归，不新生成这12DEV回答。

## 后续分阶段协议与决策

| 阶段 | 输入与上限 | 通过/失败后的动作 |
| --- | --- | --- |
| S1 CPU前端/预算（下一实际任务） | 上述2模型、4工程+12DEV、96编码、128预算评估，0生成 | 技术错误停；预算覆盖保留，输出冻结所有model-specific ids/保护集合 |
| S2 Mistral Full-only（另冻、未启用） | 同12DEV，最多2工程×3路径6答+12Full；greedy128，0压缩/封存 | 实际权重/32Full/张量字节与三路径先通过；Full任务≥6/12、格式≥9/12、错误0、截断≤1，否则停止该适配，不换提示/模型 |
| S3 条件级compact工程与DEV（另冻） | 仅已冻结且满足预算/工程覆盖的条件；每次12DEV/单预算，最多48压缩主+16工程回答，Full共用不重复生成 | 同条件native/custom、位置/gather/字节必须核验；保护无可执行工程覆盖则unverified，DEV不可运行，不借用无保护证据 |
| S4 独立组描述性复查（尚未注册） | 保留原48train文章组待全局去重/来源范围和模型前置条件完成后使用 | 所有case保留，先固定完整样本/方法/预算/seed/输出上限/统计方案，不能看到效果后改样本或继续补到显著 |
| S5 成本模式（独立协议，尚未实现） | 审计模式与单分支模式输出透明性先比；预热、同步和测量时点固定 | 释放reference前后peak/额外buffer/阶段时间单独测；不拿加载wall/dummy timing当性能 |

S3工程case范围与每条件要求必须由S1输出后另冻结，不能因4工程池里出现更长题便自动替换旧工程验证或称新条件已过。当前dispatcher/选择器仍固定28层/4KV-head/1/2；Mistral和3/4都需要版本化适配与真实工程验证，不是改config即可迁移。

S4原草案的2任务×2模型×48组/2预算/3随机seed是未来天花板，不是当前执行队列。BoolQ尚未完成来源/全局分组时不能声称2任务确认；是否先做SQuAD-only独立组复查须新scope声明，只能支持同任务跨文章/模型结论，不能追改旧跨任务协议为已完成。旧QA16 gate=false不会因新描述性协议而变true。

## BoolQ新线索及采用边界

作者[固定README](https://github.com/google-research-datasets/boolean-questions/blob/90af34107399cc7a446b373dc4ee35b8001da7c2/README.md)含title与GCS链接，原metadata GET/public HEAD两403失败保持。现核到[google/boolq数据卡](https://huggingface.co/datasets/google/boolq/blob/main/README.md)和[HF转换提交](https://huggingface.co/datasets/google/boolq/commit/8ab2d3e9ff5449d3957950129cea176fe214d884)：字段只投影question/answer/passage，未输出title；有固定parquet摘要/大小线索，未下载或逐行验证。publisher命名空间和历史校验值不是作者原JSONL字节一致性的实测证明。

这意味着不能把HF副本悄悄替换为“作者原始源已恢复”，也不能在缺标题时仍宣称跨任务文章去重。继续暂停BoolQ正文准备；若采用新分发，先有明确source amendment、row/标签校验、标题恢复或分组单位变化与独立性限制，再决定新CPU获取协议。浏览器工具无法打开HF API/部分固定raw端点只记工具访问限制，不当服务器新的403实验。本轮未重试旧GCS、修改认证、取第三方镜像或下载parquet；已通过的20BoolQ软件用例仍不是数据/任务支持证据。

## 分析口径和成题判断

主要按context group配对，分别报告格式、任务EM/F1、完成率、joint交付、预算不可行与工程未验覆盖；保护与对应无保护列任务损坏/改善和格式修复，不以总分代替逐例变化。截断/N/A的原始值保留，严格比较分母与Full正确未评估数、覆盖损坏范围并列；范围不是置信区间，未知语义不能硬填false。多seed/预算/模型共享来源组，不当新的独立样本。正式区间/多比较规则须输出前注册，当前公共core未提供风险认证；48组也不是功效证明。

阶段性可做判断：已有明确工程问题和通过范围内验收的原型，值得继续补独立实证，但“系统已打通”不等完整硕士论文或发表创新成立。如果Mistral/新任务缺支持，诚实报告适用边界；若始终只有既有小集复现和脚本整合，停止扩大贡献表述，与导师收缩工作范围。无效应或方向不一致也保留，不用增加prompt/model/预算搜索逼出正向结果。

下一条具体操作：实现CPU preflight及独立偏移/预算回读，运行前另存source SHA与实际execution snapshot，服务器单次新目录，0权重/GPU/网络；当前没有可执行runner或GPU命令。不要重跑已通过DEV验收、旧工程/旧CPU报告，不恢复停止的控制器/guard/A队列。STATUS/WORKLOG/HANDOFF与来源矩阵同步；本轮0新run，112run2888主与索引743ee544…保持，旧4PID退出，GPU当前空闲状态本轮未查询。


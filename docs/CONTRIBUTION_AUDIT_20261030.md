# 当前系统与实证路线的贡献差异审查

审阅开始2026-10-30，文档收尾2026-10-31（Asia/Singapore）；文件名沿开始日期。输入是已完成的[48组结果](SQUAD48_EVIDENCE_CONCLUSION_20261030.md)、[错误分型](SQUAD48_ERROR_ANALYSIS_20261030.md)和[章节证据映射](THESIS_EVIDENCE_MAP_20261030.md)。本次重新读取原文和固定公开源码，区分“文献已有”“本项目已实现”和“未能确认”。不是作者结果复现或穷尽式查新。

**判断：当前成果具有可复核的工程与案例价值，但尚未建立足以单独支撑新方法/新基准论文的差异贡献。接受系统/实证型硕士路线，并不自动解决这项差异不足。继续增加相同类型的退化结果，不能补上这个缺口。** 这是基于下列近邻的项目判断，不是对学院毕业要求的代判。

## 覆盖到什么程度

| 近邻 | 本次核实的相关内容 | 对本项目主张的影响 |
| --- | --- | --- |
| [Pitfalls，ACL正式版](https://aclanthology.org/2026.acl-long.1926.pdf)及[固定代码](https://github.com/alexluchen/pitfalls-of-kv-cache-compression/tree/73079e1b3bf27cd182f680d7da5edd97b660bd82) | 多指令退化、指令泄漏和淘汰改动；作者IFEval入口分别计算strict/loose的prompt与instruction分数 | “发现裁剪破坏约束”“分别报告多个约束指标”“保护指令”不再作为新意 |
| [KVDiagnosis v1 §3及附录A.1](https://arxiv.org/html/2608.09412v1)与[数据合同](https://raw.githubusercontent.com/ChosenQC/KVDiagnosis/153699e227856b891b71beac8bd2a6922f181f79/docs/data_format.md) | 全量Full/压缩账本、四转移、显式N/A、版本/身份/覆盖验证；[发布检查](https://github.com/ChosenQC/KVDiagnosis/blob/153699e227856b891b71beac8bd2a6922f181f79/scripts/check_release.py)和[适配审计](https://github.com/ChosenQC/KVDiagnosis/blob/153699e227856b891b71beac8bd2a6922f181f79/scripts/audit_pyramidkv_adapter.py)有实际代码 | “统一账本/失败诊断/不删N/A/输入版本绑定/查适配错误”已有直接先例，不能用作独有贡献 |
| [Risk-Controlled v1 §3–4](https://arxiv.org/html/2609.27981v1) | 相对同请求Full的风险合同、独立校准/测试与不获认证时Full回退 | 本项目bootstrap不是风险证书；不能宣称首个可靠性合同或由CI直接选安全预算 |
| [NVIDIA kvpress固定版](https://github.com/NVIDIA/kvpress/tree/2d66e747719a7bf1b9276f2cae6d135b96b92fd7) | 评测CLI、context/question拆分与query-aware选项；[cache不变性测试](https://github.com/NVIDIA/kvpress/blob/2d66e747719a7bf1b9276f2cae6d135b96b92fd7/tests/test_pipeline.py#L181)；实际保留数有代码定义 | “支持多方法、query-blind前端、参考cache检查”不是空白，比较必须注明本项目只是独立适配 |
| [质量与系统性能联合基准v1](https://arxiv.org/html/2607.05399v1)及[固定实现](https://github.com/agrawal-nikita/Benchmarking-KV-Cache-Optimizations-across-Task-Quality-and-System-Performance/tree/925fadf54a351b389e26d15535c1129aaefe61e2) | 同时研究任务质量、TTFT、吞吐和实测cache大小；所读[Snap入口](https://github.com/agrawal-nikita/Benchmarking-KV-Cache-Optimizations-across-Task-Quality-and-System-Performance/blob/925fadf54a351b389e26d15535c1129aaefe61e2/kvpress/benchmarking_snapkv_kvpress.py)定义cache size、系统信息和OOM状态 | 泛称“统一质量与资源评测”已被覆盖；我们还未测纯推理性能，不能声称比该基准覆盖更完整 |
| [LYR–001作者先导研究](https://lyrebird.alirezaafshan.com/papers/learning-what-to-keep/)及[固定协议/代码](https://github.com/YesterdaysLemon/llm-research/tree/da616c39ba57eeb4d076b36ef320d603b3e9a258/experiments/E010-kv-policy-compression) | 作者明确讨论格式/检索/截断混淆，区分resident与GPU峰值，并提供对齐/预算检查与探索性后续协议；未同行评审 | “零严格得分不等完全遗忘”“格式与内容分开”“字节省不等显存省”也不是本项目首次观察 |

[TensorRT-LLM 1.4.0rc1官方开发指南](https://nvidia.github.io/TensorRT-LLM/1.4.0rc1/developer-guide/kv-cache-compression-development.html)另作工程规范参照：兼容性准入、提前拒绝不支持组合、不可变离线工件及分阶段验证已有公开规范。其范围含不同压缩/存储机制，不能拿它当本项目同任务的实验对照，也不能把通用fail-fast工程原则包装为新理论。

KVDiagnosis按v1预印本处理，网页中的未来会议页眉不是本次录用确认。Risk-Controlled本轮从正文/作者链接与限定标题搜索未定位可冻结的作者仓库，代码层未知，不能写成“作者没有代码”。LYR–001是作者自述的小型公开先导研究，其结果没有在本项目复现；作为相关先例使用，不以其页面代替同行评审证据。

## 逐条处理当前候选贡献

| 候选主张 | 判定 | 现在可以怎样写 |
| --- | --- | --- |
| 首次发现KV裁剪损害约束/安全 | 删除 | 明确作为已知问题的受限复查；JSON约束不是安全政策 |
| 首次把任务与约束拆分、用失败类别诊断 | 删除首创 | 保留本48组的具体事实和可复核分型，标探索性 |
| 首次完整账本、Full配对、N/A/版本审计 | 删除首创 | 作为系统必要设计及验收需求，引用既有工作 |
| group bootstrap或数值路径检查本身是方法创新 | 不成立 | 作为正确性/不确定性工具，写清分母与范围 |
| 本次28Full/GQA4适配、角色隔离和现场证据合同 | 工程实现差异已存在 | 可证明本系统如何工作；尚未证明它解决了既有工具不能解决的研究问题 |
| 原48预留组提供独立于DEV的描述性结果 | 保留为本项目实证 | 48组不是138独立样本；一模型/任务/预算/seed，精确去重不等语义或预训练独立 |
| 一个可复核的系统+48组案例已足够完整论文 | 尚未证实 | 需要具体可区分的问题与贡献，不能由代码量/run数或“可写六章”推出 |

本项目九类状态的**具体实现组合**与某个公开schema不完全相同，不等于组合本身已有研究新颖性。没有在选读文件看到同一字段名或同一JSON模板，也不能证明别人没有相应能力。尤其KVDiagnosis已有实现来源审计，LYR–001已有保护槽位装不下时的预算拒绝和模型对齐测试，不能将这些再列成“未解决的新问题”。

## 当前仍有价值的成果与实际缺口

可保留的是代码、输入/运行证据合同、多路径和真实KV核算、独立于DEV的48组结果、完整分母与错误流转，以及Mistral/BoolQ等真实边界。这些构成后续实验底座与技术报告，也能作为系统/实证路线的具体讨论材料。

**尚缺的是：一个已证实的问题缺口，以及本系统或分析相对最接近已有工具的实证增益。** 当前未证明新算法、未证明新的约束失效机制、未证明跨任务/模型规律，也未比较现有框架在相同研究需求上的不足和本系统解决程度。不能把“别人没有做我们这48道题”当作研究贡献。

若继续系统路线，需要围绕实际使用需求给出可证伪目标，并证明改动带来可测价值，而不只列通用工程特性。仅做合成坏输入测试也不自动足够：KVDiagnosis已经有真实适配错误审计，新的问题仍需具体实例和有效对照。当前没有找到一个可直接据此宣布成立的新空缺。

## 本轮范围与证据保存

- 重新核4个仓库HEAD，均与项目此前固定版本一致；另核作者页面直链的LYR固定commit。没有把重读旧版本称作发现了新版算法。
- 选读33个仓库文件与6个论文/官方页面，共39个来源；其中24个作者Python文件仅AST解析，未import或执行作者代码，未运行作者测试，未下载作者模型/数据集。
- 官方GitHub API blob与tree核对、Git blob SHA1及SHA256均通过。部分网页前端超时/cache miss，由同一官方API固定对象完成读取；不据网页渲染失败声称代码缺失。
- 原文/源码/元数据只在服务器`literature/20261030-closest-work-audit-v1`，归档51文件2924027bytes，manifest SHA `74239ef0f39ff4273c93ddfc5fef265bf54a29c9dc3431c333b2fec35b1981f9`。检索与阅读仅为限定范围查重，不证明不存在其他近邻。
- 本轮新增实验0、模型答案0、分词/权重/GPU查询0；累计120run3038主保持，原GPU和分型工件/旧gate不变。[审阅记录](reviews/20261030-contribution-audit.md)与[决策稿](CONTRIBUTION_SCOPE_DECISION_20261030.md)给出下一步边界。

结论是暂不扩同类退化实验、不按当前材料声称独立新方法或新基准；保留原型和全部实证。下一步先把研究问题与相近工作差异整理为可审阅决策材料，只有具体缺口成立时再注册针对性验证。本文不是对所有KV压缩研究方向的否定。

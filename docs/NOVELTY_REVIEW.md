# 条件约束保持：第二轮查重与静态核查

2026-10-29[投机交叉问题门槛](SPECULATIVE_DESIGN_GATE_20261029.md)：前轮单次审查结束，当前不推进模型/新算法。LAPS-SD已有长度+接受率与draft/verify成本调度；当前vLLM0.32.0 Adaptive Verification已有跨请求概率/成本预算，不能另称新机制。SPECTRE已有共享draft流量公平/回退，VTC及deadline适配仍是强基线。工程上基本接受率观测静态可用，不是只看全局计数；但完整回退/有效成本归因/固定模型兼容和强基线不足证据均未完成，不能宣布新漏洞或声称所有租户问题已解决。停止该自动队列，旧KV决策保持。

2026-10-29[收敛决定](RESEARCH_CONVERGENCE_20261029.md)：停止扩展当前KV安全宽泛算法主张，保留负结果/平台，尚无已确认题目；不把硕士论文无需发表理解成重复曲线已足够。对其他方向仅保留一个待证交叉问题：同token配额下，投机接受率差异的跨用户延迟干扰是否超出现有简单控制。Speedbumps未测连续批处理并不等于全域空白；Mistletoe/ADSD、VTC、FairInference、GRIEF已覆盖攻击/成本公平/逐token隔离/干扰的大部分泛主张。下一次单次来源与固定引擎审查未过，不启用实验、不自动改名，不恢复旧KV队列。

2026-10-29[E审查](E_NOVELTY_GATE_20261029.md)纠正旧版本遗漏：COMA是2510.22963v4，已覆盖受限不可信输入操纵共享压缩预算、可信规则丢失和隔离压缩。E宽泛新方法no-go；改为物理KV不足以自动立题。RobustKV虽只对importance manipulation做位置分配近似，也不能据这一个限制宣布空白。当前A搁置、D宽泛方法降级，E亦未通过；没有已确认新课题或新执行配置，本次0主要/工程输出。

2026-10-29新增[D门槛审查](D_NOVELTY_GATE_20261029.md)：MAGE已有安全记忆用于待执行动作审核，TRACE已有风险证据聚合，LRE已有廉价未知query的原文保留，StepKV/CommitKV已有步骤/生命周期KV机制。D当前宽泛新方法主张no-go；严格KV用途未否定，但只换下游guard、物理KV或预算口径不足以立题。未测简单基线，不宣称其全部解决；本次明确原文可回读/不可回读及持久/峰值KV、总读取/时延的比较要求。A搁置，旧工程失败与0新输出保持；E待直接重叠审查。

2026-10-28窗口结论：候选A当前组合no-go；候选C的泛缺证据拒答/答案证据分离已由直接近邻覆盖，公开结果重算没有推翻其结论。动作安全guard预算仅为待验证用途，须超过完整规则保护/窗口/整步保留/检索，不能只换下游数据。见[窗口结论](RESEARCH_WINDOW_20261028.md)；0新模型答案，没有新方法证据。

2026-10-28方法门槛更新：[候选A no-go](PREFIX_RISK_DESIGN_GATE_20261028.md)。补读通用LTT/Pareto方法后，按组约束/正常效用联合预算可直接归约，不能仅靠换安全指标或多个query提出新方法。原256输出不启动。继续只读审查Compression-Aware Abstention的标签/实际KV/公开输出；“高保留率缺关系证据时拒答”是作者已讨论限制，尚未转化为本项目的新问题或方法，不能直接宣称空白。

2026-10-28最新选题结论见[TOPIC_SURVEY_20261028](TOPIC_SURVEY_20261028.md)，优先于下列历史候选。风险预算/Full回退已有Risk-Controlled KV Eviction，逐请求混合风险不等于逐组/相关prefix风险的边界也由作者明确讨论；“发现平均掩盖子群”不能当首次。首选待验证问题是约束/正常效用双侧要求下可复用prefix的预算选择，只有超过逐组LTT/完整规则保护等直接基线才保留；未形成新贡献。条件绑定因旧负结果降为高风险备选；重复压缩/动态撤销/缓存历史/跨模型安全重用均有直接或强近邻。本轮0模型输出，无新算法或已启用矩阵。

2026-10-28补读：[SystemCheck/Pitfalls与LongBench来源审查](runs/20261028-systemcheck-source-audit.md)已核查25文件与12AST。Pitfalls正式版附录I已含长TREC分类能力/防泄漏联合评测、长度分组和Full失败，不能将这套组合或“从IFEval换成长TREC”作为新贡献。SystemCheck是角色改编，不是天然长前缀数据；固定539/541题与标注差异见run。下一步仅CPU取得官方TREC原始文件并审上下文依赖、标签和前端，尚未形成新研究差异或执行模型。

日期：2026-10-27（Asia/Singapore）。范围：各层 Full Attention 的普通 Transformer，先研究 KV 位置裁剪。没有启动模型、测试、训练或性能实验，没有复制旧 nano-vllm。本文区分文献事实、源码观察、研究判断和待验证假设。

时序说明：本文主体记录实验授权前的静态查重，不代表当前运行状态。用户随后明确授权，首轮自建预实验已完成，见 [20261027-pilot](runs/20261027-pilot.md)。文献作者实现与报告未因此自动视为已复现。

## 当前判断

2026-10-28更新：实验后研究收敛见[RESEARCH_RESET_20261028](RESEARCH_RESET_20261028.md)。当前数据未建立安全特异绑定损坏；停止AccessDenied模板模型/提示搜索。新增近邻[KVDiagnosis v1](https://arxiv.org/html/2608.09412v1)（2026-08-10预印本）及作者仓库fixed `153699e227856b891b71beac8bd2a6922f181f79`，已读总体矩阵/Full配对/失败诊断/干预及限制相关节、README。它覆盖C→W记录与证据/预测/访问测量，所以“通用失败诊断＋恢复干预”也不能作为本题新贡献。本轮只核对源码文本/AST与旧证据，不代表作者结果复现；不以预印本文稿未来会议页眉认定录用。

下一步只保留标准测量校准提案（待CPU数据/检查器预检，模型执行锁定）；不是把IFEval换成新benchmark就获得创新。更窄的条件依赖/安全额外损失需另有匹配对照、强基线和独立查重差异，目前没有支持新贡献的完整证据；下文“有条件保留”为此前研究假设，不是已验证结论。

宽泛题目“KV 压缩削弱约束”已有直接论文；“保护规则 token”“公平分配 span 预算”“按语义单元保留”“恢复缓存分析原因”均不能单独当作创新。上一轮提出的成组保留也要降级为待比较的候选，不能预先命名为新算法。

暂时保留的窄问题是：在控制普通检索、多跳关系判断、位置与保留字节后，裁剪是否额外导致条件权限的适用对象错配？完整规则保护是否仍不足？该问题有验证价值，但查重只支持“本轮已读材料尚未直接覆盖整套设置”，不支持“首次”“已有稳定效应”或投稿承诺。

若错误与普通关系推理同步退化，应报告为一般关系保持问题在权限任务上的表现；不能硬解释为独立安全机制。若公平裁剪或完整规则保护已经解决，则放弃当前复杂方法主张。

## 检索与证据等级

检索组合包括 KV cache/compression/eviction 与 binding、relational、instruction dependency、access control、authorization、permission、negation、scope、multi-hop、graph。检索到的综述站点只作线索，以下结论以作者论文、ACL Anthology、官方仓库和模型配置为依据。

“正文”指阅读了相关方法/设置章节，不等于所有附录或代码都已审计。“仓库”不等于结果可信性审计或代码可运行性验证。

| 工作与版本 | 本轮阅读深度与已覆盖内容 | 对本题的约束 |
| --- | --- | --- |
| [Pitfalls](https://arxiv.org/abs/2510.00231v2)，2026-05-13 v2；[ACL 正式版](https://aclanthology.org/2026.acl-long.1926/) | 正文相关章节、作者代码：多指令退化、泄漏、顺序偏置、白名单与公平淘汰；附录讨论自动 span 识别 | 现象、规则保护、公平配额与自动找 span 均已有近邻；其主要任务与主体—资源条件权限组合不同，但这种任务差异本身不构成方法创新 |
| [When Efficiency Meets Safety](https://aclanthology.org/2026.acl-long.1123/)，ACL 2026 | 官方摘要和前轮所读实验段：越狱与裁剪/合并/量化、Safe-CAM | 不能只跑 ASR 曲线；安全影响也不一定单调变坏。本轮未审计 Safe-CAM 实现 |
| [AnchorKV](https://arxiv.org/html/2606.17872v1)，2026-06-16 v1 | 方法相关正文：离线 key 空间方向，修改 FastKV 的 TSP 评分 | “加安全评分”已有；其 TSP 与本题缓存裁剪阶段不同，不能强行混成同一基线；未确认作者代码入口 |
| [Safety Tax 作者仓库](https://github.com/aryan-cs/kv-cache-safety/tree/e05417187deac170edc65bf7bde0144c25b604a4) | README、LaTeX 相关段与依赖文件：安全/能力对比、策略保护、缓存 patching | 上述分析方法已有。README、LaTeX、此前 SSRN 摘要存在统计/评判器描述差异，不引用未经统一的具体恢复率，也不把摘要数字当本题先验效应 |
| [TableKV](https://aclanthology.org/2025.trl-1.13/)，TRL workshop 2025 | 10月27日后续补读6页正文（此前仅摘要）：比较query-aware Finch与query-agnostic Ada EA，含Qwen2.5-7B-Instruct | 结构化输入+KV/EA并非新切口；作者完整代码仍未审计，不声称排除方法重叠 |
| [StepKV](https://arxiv.org/html/2609.22158v2)，2026-09-22 v2 | 相关正文：step 效用结合 token 重要性，面向多步 agent | 给 token 增加语义组/步骤重要性并非空白；本题暂不做 agent 轨迹，仍需比较静态组评分 |
| [CommitKV](https://arxiv.org/html/2608.07855v1)，2026-08-08 v1 | 方法相关正文：commit 前后删除效应、休眠/完成信息、联合退休测试 | “删除影响+联合测试”已有；多轮与动态约束扩展不宜作为轻易获得的新贡献 |
| [V-Steer](https://arxiv.org/html/2607.26228v1)，2026-07-28 v1 | 方法/附录相关正文：用 attribution 选择 head，编辑缓存 V 强化指令层级；[作者仓库](https://github.com/cindy2000sh/v-steer)入口 | 编辑 V 强化约束与自动 span 发现均有邻近方法；此工作不是缓存减量方案，若后续比较须明确预算与编辑效应 |
| [OrgAccess](https://arxiv.org/abs/2505.19165v3)，2025-06-17 v3 | 官方摘要：角色权限、组合/冲突权限的合成评测 | 条件权限/组合规则任务不是新提出的评测主题；本轮未审计数据或代码 |
| [ACCESS DENIED INC](https://github.com/DrenFazlija/AccessDeniedInc)，[ACL Findings 2025](https://aclanthology.org/2025.findings-acl.684/) | 作者 README：合成企业资料、访问规则、正常与越权请求、自动/人工评分 | 允许回答与禁止披露的双侧评测已有；可作为外部任务迁移候选，未下载数据或验证本地适配 |
| [Role-Conditioned Refusals](https://aclanthology.org/2026.findings-eacl.316/)，EACL Findings 2026 | 官方摘要：基于 Spider/BIRD 的 RBAC SQL、允许/拒绝、验证器与 LoRA | 不能把“权限场景+安全/效用平衡”本身包装为贡献；与 KV 裁剪的交互仍待核查 |

## 新意风险表

| 候选主张 | 判断 | 必须新增的证据 |
| --- | --- | --- |
| 裁剪后不遵守规则/泄漏 | 高度重叠 | 不宜作为论文中心结论 |
| 固定保留 system 或规则，其他 token Top-K | 高度重叠 | 只能作为强基线 |
| 加一个安全方向评分或放大 V | 高度重叠 | 不优先做 |
| 按句子、实体、步骤分组，或在组间分预算 | 高风险 | 超过已有公平、分组和步骤评分的实质差异；仅换组名称不够 |
| 控制内容检索与普通关系判断后，权限绑定出现独立的裁剪敏感性 | 有条件保留 | 反事实配对、同构非安全对照、跨模型与明确效应量；目前无实验支持 |
| 关系成组保留优于完整规则保护与公平裁剪 | 待验证 | 等字节、相同可用元数据、oracle/实际关系提取分离；无有效上限就不开发复杂方法 |

## 可复现实现的静态核查

通过 `git ls-remote URL HEAD` 取得阅读时的提交；通过固定提交 raw URL 读取源码，仅在内存中查看，未克隆、安装或运行。

| 项目 | 阅读时提交 | 核查程度 |
| --- | --- | --- |
| NVIDIA/kvpress | `2d66e747719a7bf1b9276f2cae6d135b96b92fd7` | 读 base_press、scorer_press、snapkv_press、pipeline、utils 相关函数与 pyproject |
| alexluchen/pitfalls-of-kv-cache-compression | `73079e1b3bf27cd182f680d7da5edd97b660bd82` | 读 README、`kvpress/kvpress/presses/snapkv_fair_eviction_press.py`；其他策略未全面审计 |
| aryan-cs/kv-cache-safety | `e05417187deac170edc65bf7bde0144c25b604a4` | 读 README、`docs/latex/main.tex` 相关段与 pyproject；未审计生成循环与干预实现 |

具体观察与影响：

1. [ScorerPress 固定提交](https://github.com/NVIDIA/kvpress/blob/2d66e747719a7bf1b9276f2cae6d135b96b92fd7/kvpress/presses/scorer_press.py)：`compression_ratio` 是删除比例；沿 KV 长度维 Top-K，再对 K/V 使用相同索引 gather 到较小张量。是实际张量裁剪，不只是置零 mask；能否降低实测峰值/延迟仍须实验。需额外记录每层、每 KV head 的原位置索引。
2. [SnapKVPress](https://github.com/NVIDIA/kvpress/blob/2d66e747719a7bf1b9276f2cae6d135b96b92fd7/kvpress/presses/snapkv_press.py)：默认观察窗 64、pooling kernel 5；GQA 的 query head 评分在所属 KV group 内平均。不能把 query head 数当物理 KV head 数。保留预算必须覆盖观察窗，不能以很小的预算破坏其保护假设。
3. [BasePress](https://github.com/NVIDIA/kvpress/blob/2d66e747719a7bf1b9276f2cae6d135b96b92fd7/kvpress/presses/base_press.py)：attention forward 完成后修改缓存，返回原 output。由此推断：同次完整 prefill 的 logits 不是压缩影响的充分测量点，后续 query/decode 才使用改过的历史缓存。该推断未做运行验证。
4. [Pipeline](https://github.com/NVIDIA/kvpress/blob/2d66e747719a7bf1b9276f2cae6d135b96b92fd7/kvpress/pipeline.py)：默认把 context 包装为 user 消息，先压缩 context，再追加 question；question 起始位置沿用原 context 长度。不能直接把这个默认模板当“system 权限规则”实验。需要保留角色的前端、不可变分支缓存、逻辑位置与物理长度检查；也不能把 query-aware 与 query-blind 结果混报。
5. [Pitfalls 公平 SnapKV 源码](https://github.com/alexluchen/pitfalls-of-kv-cache-compression/blob/73079e1b3bf27cd182f680d7da5edd97b660bd82/kvpress/kvpress/presses/snapkv_fair_eviction_press.py)：支持两个相邻 span，span 内各自用观察窗评分，再按长度分配 Top-K 配额；要求完整 attentions 与 eager。不是仅给原 SnapKV 加配额。离散、非相邻关系组要标成扩展；应分开比较作者实现与“固定原评分、只改配额”的消融，不能悄悄替换。较长上下文的完整 attention 有明显内存成本，不应预设单卡可跑。
6. kvpress 该提交自报版本 0.5.5，要求 Python >=3.10、Torch >=2.3.1,<3、Transformers >=4.56.0,<5.3 等；Safety Tax 该提交要求 Python >=3.11、Torch >=2.4,<2.7、Transformers >=4.44,<5。范围有交集并不证明兼容；不合并两仓库环境作为默认方案。

## 模型架构核查

已读取 [Qwen2.5-7B-Instruct 的固定版本 config](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/a09a35458c702b33eeacc393d103063234e8bc28/config.json)，HF 返回版本 `a09a35458c702b33eeacc393d103063234e8bc28`：`Qwen2ForCausalLM`、28 层、28 query heads、4 KV heads、hidden size 3584、`use_sliding_window=false`、最大位置 32768、BF16。配置含数值 `sliding_window=131072`，但开关关闭；不能只看这个非空字段误判架构。当前配置与纯 Full Attention/GQA 范围相符，实际后端仍需初始化后核查。

按 head_dim=3584/28=128、K/V 均 BF16 推算，每 token KV 为 `2 × 28 × 4 × 128 × 2 = 57,344` 字节，即 56 KiB。4,096/8,192 token 对应 224/448 MiB；这是 batch=1 的理论缓存量，不含权重、激活、临时张量、生成后缀与元数据，不是显存测量。

直接读取 Llama-3.1-8B-Instruct config 返回 401，未获取模型配置或权重；不绕过访问控制、不认定已具备运行权限。第二模型族尚未固定，不用旧 Qwen3.5 或滑动注意力模型临时补位。

## 尚未完成与检索限制

- TableKV正文已于后续多事实检查中补读；完整代码、权限基准任务与许可证、V-Steer/StepKV/CommitKV 的公开实现仍待核查，故方法重叠尚未全部排除。
- RoleKV 搜索线索的 OpenReview 页面要求验证，本轮未取到正文，不以标题认定相关或不相关。
- GitHub API 返回 403 rate limit，改用只读 git 协议取得 HEAD；后半程 web 工具出现传输错误，部分官方页通过普通 HTTPS 读取。没有把失败请求当成功证据。
- 未下载模型/数据、未创建环境、未执行源码、未复测文献结果。验证的只是公开证据、源码路径与配置；效应是否存在须未来获明确实验授权后按 [验证协议](VALIDATION_PROTOCOL.md) 检查。

## 多事实后续补充（2026-10-27，已授权实验阶段）

[Expected Attention](https://arxiv.org/abs/2510.00636) 与 [KVzip](https://arxiv.org/abs/2505.23416) 是适合query-blind方向的相关对照。本轮将固定kvpress提交的EA评分主体纳入工程检查（两处imports/Qwen2 helper适配；统一anchor、预算/gather另行实现），不是完整系统复现。KVzip官方及kvpress入口已查看，其重构评分/可变预算/mask流程未复现，不能把本轮对照称完备。

新多事实Full门槛失败，故没有压缩效果新证据。结构化组装或规则保护仍只是对照，不能因加入EA代码便升级为方法贡献；详见runs/20261027-scale-queryblind。

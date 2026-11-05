# 文献与查重

## 2026-11-01：初始化与请求成本的固定源码映射

[范围审阅](STARTUP_REQUEST_SCOPE_REVIEW_20261101.md)只读安装vLLM0.32.0/XGrammar0.2.8/llguidance1.7.6：实际结构化验证已在InputProcessor.params.verify→SamplingParams._validate_structured_outputs路由，manager注释的旧Processor方法名不作运行证据；backend validator可能转换schema，manager首请求可能lazy构建factory，然后再排队compile_grammar。账本需覆盖这些阶段，不能只从compile函数计时或把所有准备当预热。

旧事件表明X导入开始时组合5秒只余1.908293秒，没有语法编译样本，不能由此评价编译时限。仅提出新的初始化/请求工程契约，非新研究贡献。source archive literature/20261101-startup-request-scope-review-v1：12源快照/AST28/旧账本，18文件272016bytes/manifest8ba1b4a0…，无作者代码执行或新实验，旧结果不改。

## 2026-11-01：llguidance 1.7.6 byte契约与XGrammar导入源审

[审查报告](LEGACY_BACKEND_SOURCE_AUDIT_20261101.md)固定v1.7.6 tag至0384f3f6aab6cebe8abf9b74db0079b96f5837ef；[特殊token说明](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/docs/special_tokens.md)、[Python binding](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/python_ext/src/py.rs)、[TokTrie decode](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/toktrie/src/toktree.rs#L510)明确FF标记路径。安装wrapper/stub blob匹配，但native二进制构建commit未独立证明；预测原id255解码为空，未运行验证。内置byte是262词/EOS261，不是原257词的替代。X导入静态链包含Torch/线程设置/TVM-FFI/Transformers，未定位真实慢点，不据源码含JIT归因。

6官方源与14安装/项目快照仅服务器literature/20261101-legacy-backend-source-audit-v1，25文件334142bytes，manifest4b90869d…逐hash回读；0新实验／作者代码执行。只是入口契约审查，不新增模型安全／资源隔离贡献。

## 2026-10-31：结构化输出版本与输入冻结

[CPU协议及现场预检](STRUCTURED_RESOURCE_CPU_PROTOCOL_20261031.md)补充了实现差异：[llguidance changelog](https://github.com/guidance-ai/llguidance/blob/3d698ee07b3a67b0aef50fb6058612e8fd30aca2/CHANGELOG.md)记录1.9.x加入Rust取消，但最新Python stub及两binding未见对应入口，不能凭原生API文档推定Python可直接用。本机现有1.7.6有fuel、无已见取消；vLLM0.32.0限制<1.8。现有XGrammar0.2.8没有最新dynamic参数，不能替代XGrammar-2动态模式。

公共语义小样本来自[官方JSON Schema Test Suite固定commit](https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/8cab295687d150de3900a160c6ad002b53ddb30e/tests/draft2020-12)，8文件各第一个同时有valid/invalid的原组，8schema45标签，未按后端结果选样。源与选择仅服务器literature/20261031-structured-resource-preflight-v1，41文件607993bytes／manifest18cfd4bb…；20环境快照、13官方blob和选择规则独立回读，未执行作者代码。有限标签不证明完整语言等价，schema原样且XGrammar须strict_mode=false以保持原语义。N1仍未定题，无真实资源效应结论。

## 2026-10-31：新问题与结构化输出资源生命周期

完整判断及固定版本见[新问题筛查](NEW_PROBLEM_TRIAGE_20261031.md)。保留 N1 为有界实证候选，尚无新颖性或实测效果；暂停以泛 KV 约束保持为主线。关键近邻：[vLLM 编译超时报告](https://github.com/vllm-project/vllm/issues/54003)、[scheduler deadline PR](https://github.com/vllm-project/vllm/pull/45172)、[可杀 regex worker PR](https://github.com/vllm-project/vllm/pull/52119)、[llguidance 协作式取消与预算](https://github.com/guidance-ai/llguidance)、[GRID 集成 RFC](https://github.com/vllm-project/vllm/issues/50966)、[JSONSchemaBench](https://arxiv.org/abs/2501.10868)、[XGrammar-2 v4 JIT](https://arxiv.org/html/2601.04426v4)。不能把已知缓存耗尽、超时或子进程方案当新贡献。

源审固定 vLLM 2b009fc6…／XGrammar ca1acf28…／llguidance 3d698ee0…／GRID 088be818…，仅文本阅读；PR 当前补丁和 head 元数据分别保存，不冒称全部源码 Git blob 固定。来源只服务器 literature/20261031-new-problem-triage-v1，31 文件 564110 bytes／manifest 1fc87993…，24 成功来源 SHA 回读、9 raw 超时／网络失败保留；web-only 阅读另列。未执行作者代码，未测资源效果，不新增实验。

## 2026-10-31：解码目标与KV候选

[研究问题重定](RESEARCH_QUESTION_REDEFINITION_20261031.md)与[有界草案](DECODER_OBJECTIVE_SCREEN_DRAFT_20261031.md)完成。H1格式修复与H2泛parser-aware KV不作主创新；仅保留H3待筛查假设：同一生成前缀下，全词表/通用Top-K KL是否会给等预算真实KV候选排出与局部合法token目标不同、且损伤合法语义决策的顺序。三token构造反例及标准KL分解已独立复核，但不是真实KV证据；尚无新颖性或可发表/毕业结论。下一步先实现CPU有限语法/稳定KL/候选掩码正确性入口并独立核验，再另冻12个新开发组的query-known同前缀logit诊断。108向量草案未实现/未执行，不是108独立回答；禁止复用Full suffix KV、原48调参或把局部mask当全序列条件分布。含Top128/256及直接masked-KL组合对照，无信号即停，不扩seed/预算救回。

[PASK v2](https://arxiv.org/html/2608.28276v2)已有parser角色/KV持久性；[Behavior-Preserving v1](https://arxiv.org/pdf/2610.06479v1)已有输出KL及附录B Full-TopK128/256重归一化，support受限KL不是新概念；[Grammar-Aligned v4](https://arxiv.org/html/2405.21047v4)区分本步mask与全字符串条件分布；[结构/语义gap v1](https://arxiv.org/html/2609.23742v1)已有格式合法仍语义错误；[XGrammar2摘要](https://arxiv.org/abs/2601.04426v1)仅作引擎线索，未集成。作者代码/强简单组合与更广检索仍待审，有限检索不证明研究空白。

原文与算术证据仅服务器literature/20261031-decoder-aware-candidate-v1，10文件2266407bytes，manifest ea36b38a02db149812649eace16c321e92786a7da17fb4eaa00f086e717f2963。0新实验/forward/回答/分词/权重/GPU；累计120run3038主及f3e6a039…索引、原GPU194与分类20工件不改。旧QA/Mistral false及旧16/保护/3/4/BoolQ停止保持。代码配置文档同步服务器，GitHub未配置，当前无运行任务。

2026-10-31最新（审阅始于10-30）：[近邻贡献审查](CONTRIBUTION_AUDIT_20261030.md)、[范围决策](CONTRIBUTION_SCOPE_DECISION_20261030.md)、[审阅记录](reviews/20261030-contribution-audit.md)与[readiness](CONTRIBUTION_AUDIT_READINESS_20261030.json)完成。重读六项主近邻及TensorRT官方工程指南，固定5仓库/33文件+6论文官方页面，39源/24作者Python仅AST；4HEAD仍是此前固定版本，LYR沿作者直链commit。Pitfalls已有指令退化；KVDiagnosis已有全量Full配对/四转移/N/A/版本发布检查及真实适配来源审计；kvpress有context/question拆分和cache不变测试；质量/性能联合基准及LYR先导已覆盖资源核算、格式/内容/截断混淆。Risk-Controlled代码未定位保持未知，不据缺页断言无代码；LYR未同行评审、KVD未来会议页眉不当录用证据。本轮判断：保留已验原型和48组受限结果，尚未建立独立新方法/新基准贡献；通用账本/双指标/配对/预算检查不能当首创，六章可组织不等论文贡献闭合。系统/实证硕士候选保留，具体贡献仍待重定，不能代判毕业认可。暂不追加同类退化GPU实验，下一步先明确可证伪的问题缺口和最接近实现的实证增益，不据错题调prompt/样本/预算。来源原文源码只服务器literature/20261030-closest-work-audit-v1，51文件2924027bytes，Git blob/SHA核验通过，作者代码/测试未执行；部分web缓存失败改读同官方API，39源请求+9元数据成功，无模型/数据集下载。只读文献审阅不新增实验，累计120run3038主/f3e6a039…索引与原GPU/分类工件不变；0新模型回答/分词/权重/GPU/依赖/服务，旧自有PID退出。旧QA/Mistral false、旧16/保护/3/4/BoolQ停止保持。代码配置文档同步服务器，GitHub未配置，当前无运行任务。本条取代下方历史待办，原实测结果不撤销。

2026-10-30[方向判断补核](ANSWER_FORMAT_FEASIBILITY_20261030.md)：本轮仅重开官方摘要/版本，Pitfalls ACL2026已有多指令退化与淘汰策略修正，KVDiagnosis2608.09412v1已有逐源Full配对和适用状态，Risk-Controlled2609.27981v1已有相对Full的效用损失/有限样本风险校准。没有新增全文/作者实验复现或全面新颖性通过。新QA+JSON DEV出现同预算格式/任务权衡，但不能把裁剪有害、指令保护、配对报告/风险算法单独当首创；建议保留系统/实证路线而非新方法小论文。单模型16题/一预算一seed及1截断，自动确认关卡false，独立/长上下文/安全主张未建立。

2026-10-30执行边界补记：[任务CPU预检](runs/20261030-answer-format-task-preflight.md)取回4份既定源，数据SHA95aa6a52…、4854279bytes与固定Git blob匹配；Python/JS/LICENSE长度及blob也一致，作者函数仍未执行，原CodaLab原件未取得。新独立scorer24预定用例与6数据用例通过，全部34726答案source slice核验。此为项目适配验证，非复现作者性能/新颖性验证；原来源索引保留准备时事实不追改，当前证据见readiness。公开数据污染/短段落及近重复语义边界保持，不据此主张安全或长上下文结果。

2026-10-30[新任务来源审查](ANSWER_FORMAT_TASK_SOURCES_20261030.json)：SQuAD官方页/1606.05250v3摘要和作者gh-pages固定e0c66cfe…树元数据；dev-v1.1 blob e9a3f913…/4854279bytes，正文/SHA256/样本数未取。静态阅读BiDAF作者仓库49004549…附v1.1 Python评分副本（SHAf5a673db…），不能声称已与不可达CodaLab原件匹配；作者网站JS含不同空答案/空白边界，不当同一评分器。RFC8259相关JSON/Unicode段与数据CC BY-SA 4.0/仓库Apache-2.0来源分开登记。只新增阅读+JSON的项目适配契约与禁用CPU方案，不称新基准/算法、原官方测试或安全实验；旧公开数据可能预训练污染，文章分组只防项目内部共享。未运行作者代码或新增实验，旧查重否定结论保持。

2026-10-30[一页选题收敛](THESIS_CONVERGENCE_20261030.md)：本轮复核Pitfalls ACL2026正式入口摘要、KVDiagnosis2608.09412v1与Risk-Controlled2609.27981v1的arXiv摘要/版本，未新增正文/作者代码复现。前者已研究指令退化与规则保护，后两者已有配对诊断及风险校准；因此建议系统/实证路线不能称首个评测基准、新诊断理论或新校准方法。用户接受明确问题的系统或实证研究，不等于重复曲线自然有贡献；按工程需求、独立验证与适用边界落实，原论文数字不作本项目结果。

2026-10-30[取消记账门槛](CANCELLATION_ACCOUNTING_GATE_20261030.md)：新直接近邻Retire2610.01160v1（10-01）§3–6/§7.1/AppA.3已有过时计算停止/输出权威/KV交接及pin配额，不等金额/TPM账本；GRIEF2605.11202v1 §3/§4.2/AppA.1–A.2已有Cancel/Disconnect trace与干扰确认。Sorami作者README固定blobc49b6f96…已有close/no-read/drained和网关测量，但指标明确非GPU时间/账单，canonical report工具不可达、raw不取。取消不走finished统计已公开issue55634/open未合并PR55940，源码静态结构确认不能当新发现；未应用PR/跑测试。LiteLLM预算文档及main limiter blob14b08a09…显示预留/partial usage结算/取消槽释放，非完整路径或部署安全验证。13固定vLLM0.32安装blob匹配，来源/阅读限制见新JSON。泛取消成本/简单补统计新方法no-go，实际配额绕过未建立，0新模型或实验。

2026-10-30[共享控制器调查](CONTROLLER_HISTORY_AUDIT_20261030.md)补读TTA2308.08505v1 §3/§5.5–5.6/§6相关段、RTTDP2410.04682v3 §3.1–3.2/§5.4：顺序、正常恢复、非i.i.d.热身/现实攻击假设与简单防御已有，不能再泛称首次持久投毒。APEX2610.07780v1 §4.3/§4.8/结论（PDF交叉核对）已有删失生存反馈，部署参数固定，online动作不等于共享参数在线训练；OSD ICML2024与OnlineSPEC ICML2026正式入口仅摘要，draft学习对象不同，未声称审完证明/实现。固定vLLM0.32.0估计器/构造/新增结束请求/预算及测试段已审，状态跨请求保留仅结构事实；官方458334f...10-28 warmup/JIT相关patch补查，预热暂停必须排除。来源范围与blob见新JSON，不执行作者代码或复现数字；没有确认新颖性。

2026-10-29[后续调查初筛](NEXT_RESEARCH_LEADS_20261029.md)：重读固定vLLM0.32.0 acceptance_estimator.py:340–451（共享slope、按位置intercepts、跨请求统计/refit），不等于已验证投毒。补读Test-Time Poisoning2308.08505v1与Realistic TTA Poisoning2410.04682v3摘要，承认在线投毒已有通用近邻；OpenReview PDF验证页未绕过。vLLM官方GHSA-8wr5-jm2h-8r4f已含并发/取消组合故障且列修复版本，不能当新发现。OWASP官方RAG指南已有按权限隔离、失效与级联删除；SAFE-KV2610.15186v1仅摘要/因果闭包段，非prefix后缀修复已有。Alignment Collapse Under KV Cache Quantization2606.09864已v2，仅读摘要/版本，不将普通量化安全曲线当新题。三条为待查线索，未复现或判定创新。

2026-10-29[投机源码/文献门槛](SPECULATIVE_DESIGN_GATE_20261029.md)补齐：LAPS-SD正式IJCAI2025入口已有自动抽取全文，可与2505.17074v1交叉核对，补上此前PDF失败缺口；长度+接受率估成本、已获服务含draft/verify早已存在。SPECTRE2605.08151v1 §3.2/§4.4/附录A已有共享draft公平和回退；FairBatching2510.14392v1 §3–4、Kairos2605.02329v1 §3补读。GitHub固定vLLM v0.32.0 commit5df63a7203cdb9328d824a27b682e77c7b9928be只读22文件，当前Adaptive Verification已按每请求/位置概率和实测成本分配验证预算，且有per-request detailed统计；源码位置/阅读深度/限制见报告及JSON索引，未执行或复现。泛预算新算法no-go，未测跨用户残余问题不等于现有基线已充分解决；当前不进实验。

2026-10-29[收敛审查](RESEARCH_CONVERGENCE_20261029.md)补入跨方向一手来源：Speedbumps2610.10929v1（batch=1，连续批处理/其他用户影响留作未来工作）；Mistletoe2605.14005v1与ADSD2607.21804v1已有接受率崩溃，ADSD §6已提在线监测/关闭投机；VTC OSDI2024 §3.1/4.2/附录B.2已有自定义及profiled成本；FairInference2609.18112v1 §4.1/5.4–5.7/6/9已有逐token延迟公平及明确假设；GRIEF2605.11202v1 §4.2已有跨请求干扰/共享engine阻塞。阅读范围/链接和未审项均在报告，不宣称复现或全面查重。IJCAI2025具体投机调度PDF官方入口读取失败，仅有检索摘要。当前不能以回答正常但内部浪费、低接受率拖慢自身、吞吐公平不保尾延迟或合法输入影响其他用户这些泛表述立题；一个更窄的投机验证成本/简单控制边界仅待源码门槛审查。

2026-10-29重要版本修订：[E审查](E_NOVELTY_GATE_20261029.md)确认CompressionAttack2510.22963已更新为[COMA v4](https://arxiv.org/html/2510.22963v4)（2026-06-19）。§2–5直接研究共享预算下不可信输入影响可信规则，§7含无压缩控制/关键token移除与Isolated Compression防御；旧v1摘要不足以支撑E候选差异。RobustKV正式ICLR2025 PDF §5的重要性攻击为人为分配淘汰位置的近似评估，不能与实际输入操纵混淆。作者固定README及阅读范围见新报告；未执行代码/复现数字，不据仓库名称推定正式录用。E宽泛方法no-go，物理KV的剩余差别未建立创新。

2026-10-29补查：[D差异审查](D_NOVELTY_GATE_20261029.md)记录MAGE2605.03228v1（安全shadow memory＋动作前审核，§4.2/§4.3.3/§6.2.3）、LRE2606.20954v2（query-blind廉价原文保留，§3/附录C）、TRACE全文Reader、StepKV/CommitKV步骤机制、CoLaGuard latent安全推理及REALM2026精确读取预算审查。版本/阅读深度/原始入口见新文档；未执行源码或复现性能。MAGE是此前候选说明遗漏的直接基线，现据此将D宽泛方法降级；不声称严格KV用途已被完整解决或全域查重完成。

2026-10-28补查：[公开拒答结果与候选边界](ABSTENTION_SOURCE_FINDINGS_20261028.md)加入Does Accuracy Equal Evidence? (EMNLP2026)、Error Certificates、TRACE、Defensive M2S、StepGuard、StepSafe、ToolSafe及Shortcut Sensitivity近邻。答案/证据差距、及时干预、分散证据聚合均不能泛称空白。动作guard用途仍待固定Full/NoHistory检查，尚非创新；本轮[结论](RESEARCH_WINDOW_20261028.md)。

## 2026-10-28：Governance Decay与本方向的重合度

用户截图来源：[Governance Decay，arXiv2606.22528v2](https://arxiv.org/html/2606.22528v2)，Shiyang Chen；v1为2026-06-21，v2为2026-06-27。本轮读官方HTML §2–9，未审作者代码或复现实验；截图与论文内容仅作为研究材料。

判断：上位问题高度重合，技术操作层不同。论文研究agent harness的文本历史摘要/截断/消息淘汰，测量上下文治理规则丢失后的工具调用违规；本方向研究普通Full Attention模型内部实际分层分头KV位置删除及固定实际KV字节预算。论文虽提及KV eviction相关工作，其API实验不能当实际KV裁剪或本项目模型架构的验证。

作者提出ConstraintRot、Compaction-Eviction Attack与Constraint Pinning，包含规则存在/不存在/压缩/固定保护对照，以及正常允许动作、反复压缩和多种文本压缩策略。Pinning独立保护规则并在摘要后原文重放、检查；与规则KV保护的理念重叠，但重放重新编码，不等价于保留原KV。主网格1323 episodes中0%→30%违规为作者报告，非本项目测量；近期上下文操作者冒充在压力测试中仍击穿pinning，不能将主网格0%解释成普适保证。威胁模型重点是会被harness压缩的非不可变system渠道规则，不能将所有约束等同于system文本。

选题影响：不能再声称首次研究“压缩丢规则/保护规则”，也不能把正常效用或多轮压缩说成此文未涉及。与[The Pitfalls of KV Cache Compression](https://aclanthology.org/2026.acl-long.1926/)直接KV近邻合看，单纯“把摘要换成真实KV并保护规则”不足以支撑创新。需要具体、可证伪且完整规则保护等强基线解决不了的问题。项目当前TREC只支持格式损伤/恢复个例，尚无一般安全或新方法证据；证据充分性/拒答候选也尚未确认。本次0模型输出、无新实验启动，不改变旧gate。

2026-10-28启动补查：[LTT v5 §2.4](https://arxiv.org/html/2110.01052v5)多风险intersection-union检验、[Pareto Testing v1 §4–5](https://arxiv.org/html/2210.07913v1)约束/成本选择、[CompilerKV v1 §4.4](https://arxiv.org/html/2602.08686v1)输入风险门控已覆盖候选A的重要组成，因此当前主张否决。数学/文献对应见[启动审查](PREFIX_RISK_DESIGN_GATE_20261028.md)。[Compression-Aware Abstention v1](https://arxiv.org/html/2608.29934v1)已包含真实压缩KV拒答训练/评估及针对性删除控制；[作者源码固定1426730a](https://github.com/mali-kh/compression-aware-abstention/tree/1426730aaf29edf48e91930d14d3b47b73f8e584)14文件/10AST核验，不运行作者代码。标签对冗余/关系充分性的限制须与[Sufficient Context v3](https://arxiv.org/html/2411.06037v3)及KVDiagnosis共同审查，尚无新贡献。

2026-10-28选题再调研：[候选问题报告](TOPIC_SURVEY_20261028.md)。新增重点[Risk-Controlled KV Eviction v1](https://arxiv.org/html/2609.27981v1)已覆盖风险目标/有限样本校准/Full回退；其分组及相关采样边界只能支持待验证候选，不能据此宣称首次。补核[FlowKV v2](https://arxiv.org/html/2505.15347v2)、[执行状态遗忘v1](https://arxiv.org/html/2609.04875v1)、[缓存历史依赖](https://arxiv.org/abs/2610.05833v1)、[跨模型安全重用](https://arxiv.org/abs/2610.15721v1)、[WitCert v3](https://arxiv.org/abs/2607.28699v3)、[CompressionAttack v1](https://arxiv.org/html/2510.22963v1)、MiKV及量化对齐摘要，阅读深度与机制区分见报告。作者KVzip README和KVDiagnosis fixed README只读核查，没有执行作者代码或新推理。

2026-10-28补充：固定[SystemCheck ed829f6](https://github.com/normster/SystemCheck/tree/ed829f6ac7cd4e09f7161fe7dffbebdd220eb024)、Pitfalls73079e1和[LongBench源码2e00731](https://github.com/THUDM/LongBench/tree/2e00731f8d0bff23dc4325161044d0ed8af94c1e/LongBench)，25文件/blob与12AST完成；CPU只加载现有tokenizer，没有判分器/模型执行。S-IFEval约束移system不产生长前缀，数据有改编/删除，具体逐key核对见[本轮记录](runs/20261028-systemcheck-source-audit.md)。[Pitfalls正式版](https://aclanthology.org/2026.acl-long.1926.pdf)附录I已含LongBench TREC长上下文分类/防泄漏及Full失败，不能把这一联合评测称新贡献；TREC官方首行/标签包含评分也不能替代完整回答约束判分。下一步仅冻结TREC原始文件和CPU可行性。

更新：2026-10-27，已完成两轮查重、部分正文和固定提交的源码静态阅读，未克隆代码、下载权重/数据或复现实验。下面论文结论均为作者报告，不是本项目测量；检索不能证明候选题目无人研究。最新证据等级、版本、重叠判断和读取失败记录见 [NOVELTY_REVIEW](NOVELTY_REVIEW.md)。

后续状态：用户已授权本会话实验，使用服务器已有权重完成自建短任务预实验，见 [本轮记录](runs/20261027-pilot.md)。这不是上述论文作者代码/数字的复现，作者结果仍需单独核查。

| 工作 | 链接 | 接手时核对 |
| --- | --- | --- |
| SnapKV: LLM Knows What You are Looking for Before Generation | https://arxiv.org/abs/2404.14469 | 观察窗口、逐头位置选择、缓存预算与基线实现 |
| When Efficiency Meets Safety: A Benchmark Security Analysis of KV Cache Compression in Large Language Models | https://aclanthology.org/2026.acl-long.1123/ | 已覆盖的裁剪/合并机制、安全指标与攻击类型 |
| AnchorKV: Safety-Aware KV Cache Compression via Soft Penalty with a Refusal Anchor | https://arxiv.org/abs/2606.17872 | 安全感知保留的近邻方法；不可直接重复 |
| The Pitfalls of KV Cache Compression | https://arxiv.org/abs/2510.00231 | v2：2026-05-13；已覆盖多指令退化、system prompt 泄漏、顺序与淘汰偏置，提出白名单与公平裁剪，是直接近邻 |
| The Safety Tax of Cache Compression，作者仓库 | https://github.com/aryan-cs/kv-cache-safety | 包含安全/能力退化对比、policy-pinned 保留和 causal patching 入口；不能把这些宽泛思路当作新贡献。网页/预印本版本信息待统一 |
| CommitKV: Lifecycle-Aware KV Cache Compression via Commit Transitions for Multi-Turn Agents | https://arxiv.org/abs/2608.07855 | 2026-08-08 v1；以工具调用前后删除效应区分休眠与完成信息。动态约束候选须与该生命周期方法区分；本轮仅摘要 |
| Steering Instruction Hierarchies at Inference Time | https://arxiv.org/abs/2607.26228 | 2026-07-28；推理时 KV 干预与指令层级的邻近工作；仅核对入口，完整方法与压缩设置待深读 |
| TableKV: KV Cache Compression for In-Context Table Processing | https://aclanthology.org/2025.trl-1.13/ | TRL workshop 2025；关系信息已有近邻，本轮官方摘要，全文/代码待核查 |
| StepKV: Step-Aware KV Cache Compression for LLM Agents | https://arxiv.org/abs/2609.22158v2 | 2026-09-22 v2；读相关正文，step 效用与 token 评分结合，不把语义组保留单独当创新 |
| OrgAccess | https://arxiv.org/abs/2505.19165v3 | 2025-06-17 v3；条件/组合/冲突权限已有评测；本轮官方摘要 |
| ACCESS DENIED INC | https://aclanthology.org/2025.findings-acl.684/ | 作者仓库 https://github.com/DrenFazlija/AccessDeniedInc ，已读 README，未下载数据或运行 |
| Role-Conditioned Refusals | https://aclanthology.org/2026.findings-eacl.316/ | 2026-03；RBAC SQL 与允许/拒绝权衡；本轮官方摘要 |

上表 CommitKV 和 V-Steer 的“仅摘要/入口”描述是首轮记录；2026-10-27 已补读相关方法正文，最新深度以 NOVELTY_REVIEW 为准。Pitfalls 作者代码入口已核实为 https://github.com/alexluchen/pitfalls-of-kv-cache-compression ，正式 ACL 入口为 https://aclanthology.org/2026.acl-long.1926/ 。

## 本轮核查与选题含义

- Pitfalls 作者全文入口：https://starai.cs.ucla.edu/papers/ChenArxiv25.pdf 。已查看多指令与白名单/公平裁剪部分。公平裁剪按 span 长度分配预算、保持相同保留率；附录也讨论自动 span 识别，不能将“自动找约束”单独包装成创新。
- AnchorKV v1（2026-06-16）正文：https://arxiv.org/html/2606.17872v1 。基于层特定 key 空间的离线方向修正 FastKV TSP 选择评分，重点为越狱安全与正常任务取舍。不能直接将“安全方向加分”作为本项目新方法。
- ACL 2026 的 When Efficiency Meets Safety 已覆盖多模型、不同压缩机制与越狱攻击，并提出 Safe-CAM；仅测 ASR 变化不足以支撑本题的新意。
- 助手提出的候选切口为条件规则中主体—对象—条件—权限关系的保持，须用允许/禁止配对与等预算成组对照验证；尚未完成该窄问题的全面查重，未声称首次。

## 独立实现候选入口

- SnapKV 作者仓库：https://github.com/FasterDecoding/SnapKV 。首轮只读页面；本轮静态核查的是 kvpress 中的实现，不能称已验证作者原版。
- NVIDIA kvpress：https://github.com/NVIDIA/kvpress 。2026-10-27 静态阅读 commit `2d66e747719a7bf1b9276f2cae6d135b96b92fd7`，核心路径与依赖见 NOVELTY_REVIEW；未安装或运行，不宣称环境兼容已经通过。
- 不从用户旧 nano-vllm 复制任何代码或文件；Qwen3.5 Hybrid 不进入当前实验范围。

## 必须补充

- [ ] 核查安全约束保持、system token 保护、多轮与长上下文的最新工作。
- [ ] 核查候选实现对纯 Full Attention 模型的支持、真实物理 KV 整理与位置编码语义，不再以适配旧混合架构为目标。
- [ ] 记录每篇的版本、威胁模型、基线、代码入口、可运行状态和与本题差异。
- [ ] 找到相似方法时先更新选题，不把“未检索到”写成“首次”。

## 多事实阶段补充（2026-10-27）

- [Expected Attention](https://arxiv.org/abs/2510.00636)：面向未来query分布估计重要性。已纳入kvpress固定commit评分主体并做Qwen2工程检查，非完整作者系统复现；许可与适配见scripts/vendor/NOTICE.md。
- [KVzip](https://arxiv.org/abs/2505.23416)、[官方仓库](https://github.com/snu-mllab/KVzip)：query-agnostic重构方向对照；已查看入口/kvpress实现，尚未复现，不报告其性能。
- [TableKV正文](https://aclanthology.org/2025.trl-1.13.pdf)已补读：实验比较Finch与Ada EA，包含Qwen2.5-7B-Instruct；不能以表格/JSON事实加KV裁剪作为新意。完整源码仍待审计。

## 前端审计后：公开测量入口核查（2026-10-27）

- [RULER官方仓库](https://github.com/NVIDIA/RULER/tree/c3f5e3b4f87f97e048793bb510a3a6b19a46bf3a)：固定main提交，读NIAH/任务定义/README与Apache许可，源码留服务器只读审计。可用作直接检索能力控制，不是权限/安全测试；README标main legacy并提供rulerv1-ns/rulerv2-ns新版入口，未运行正式基准。
- [OrgAccess官方evaluation](https://github.com/respailab/orgaccess/blob/c65ef95f7a8821098906012c4236a4fcd8144f9b/evaluation.py)：MIT；Senior_Software_Engineer示例label=full而rationale说rejected，并有placeholder predictions。代码语法检查通过，未执行。只说明该示例的具体冲突，不外推整个HF数据集质量；下一步先审easy真实数据标签及partial判定原义。
- [AccessDeniedInc官方grade](https://github.com/DrenFazlija/AccessDeniedInc/blob/1a43c47a3d6619d2bc6a0e05899dab900760ecdc/scripts/grade.py)：MIT；已读README/question_prompt/questionnaire/grade，自动评分依赖抽取答案块并含未知/人工类别，不能替代全文泄漏扫描或将未知行从分母排除。尚未下载/运行正式数据。
- 固定源码审计记录`results/20261027-public-source-audit-v1/`：12文件全部获取/摘要、6Python AST检查，不代表可运行性/结果复现；详细边界见runs/20261027-frontend-audit。

## 2026-10-28：实际数据与控制运行补充

- [OrgAccess固定GitHub easy快照](https://github.com/respailab/orgaccess/blob/c65ef95f7a8821098906012c4236a4fcd8144f9b/data/easy-00000-of-00001.parquet)已在服务器下载并读取：3,238,846bytes、38,280行，和此前HF卡片行数不一致，不混报。原first32用于不重抽的label一致性检查；未获取当前HF数据。原permissions/query下593组存在不同标准标签，含role/timestamp仍592组，例117/433行full/partial反映rationale中的隐含biometric状态，不能当原输入可判定的唯一gold。本轮暂停该快照的正确性门槛，不声称整个OrgAccess所有版本有同样问题。
- 旧版RULER生成函数在服务器按AST提取复用数字/needle分支，Apache许可与源文件保留。16种子两干扰规模32题正确值包含32/32，非官方整套/最新版pipeline复现；轻量适配与结果见runs/20261028-benchmark-baselines。严格数字独占格式指标和正常自然语言复述query+value分开报告。

## 2026-10-28：AccessDenied与下一候选架构

研究收敛新增来源：[KVDiagnosis v1](https://arxiv.org/html/2608.09412v1)、[作者固定仓库](https://github.com/ChosenQC/KVDiagnosis/tree/153699e227856b891b71beac8bd2a6922f181f79)覆盖Full配对失败记录和多种诊断，进一步限制通用归因主张。后续校准拟参考[IFEval固定作者源码](https://github.com/google-research/google-research/tree/e6890f85757dd84e27ca6df2dd30651dafad28e0/instruction_following_eval)：strict逐指令/整提示判分与loose分开；本轮只AST及接口核查，未运行检查器/数据集。Pitfalls已有多指令跟随研究，校准仅为有限复现，不当新颖性证据。具体事实/推断/未验证项见RESEARCH_RESET_20261028。

后续真实运行更新：Mistral fixed c170c708完整13文件已取得并和官方摘要一致，291weight tensor全BF16、运行时32Full层/三缓存路径检查通过；原24发展任务严格8/0/2，同事8最终块披露、缺失另4次禁用值。已在第二模型族实际运行，但质量失败，不能称第二族验证了压缩效应/方法，未跑确认/裁剪。此结论仅限固定受控适配与原生前端，不外推Mistral整体能力。停止该分支模型/提示搜索，先收敛任务，见runs/20261028-mistral-full；下段候选“未取权重”为历史状态。

独立族后续核查：[Mistral-7B-Instruct-v0.3固定配置](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/blob/c170c708c41dac9275d15a8fff4eca08d52bab71/config.json)为32层/32query/8KV、sliding_window=null；不能以早期Mistral滑窗描述替代此固定版本。[固定README](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/blob/c170c708c41dac9275d15a8fff4eca08d52bab71/README.md)声明Apache-2.0并同时提供mistral-inference/HF system+user例子，也说明无专门moderation机制；不据此推断本任务更强或已部署安全。当前只完成metadata、meta结构与native tokenizer核查，未获权重/任务成绩。原生system内容合入INST、system-only模板仅<s>，具体适配边界与失败修复见runs/20261028-mistral-candidate，不当第二模型族性能复现或新颖性证据。

本节后续实测更新：Qwen3-8B b968826d已完整校验/加载，36层Full Attention、Q/K norm走原生Transformers；原24发展集严格8/8、7/8、3/8，门槛失败。源policy明确要求plain-text thought process，故native enable_thinking=false仍产生62–94token的解释；唯一同事禁用薪资仅在块外，8个最终块均正确拒绝，不能称原应用交付泄漏。该结果是同一Qwen家族的开发比较，不是完整AccessDenied复现、独立确认或新颖性证明。官方[固定模型说明](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/README.md)与权重摘要保存服务器，具体见runs/20261028-qwen3-access；下列“未加载”描述是此前配置核查时点。

- [AccessDenied固定HF前端](https://github.com/DrenFazlija/AccessDeniedInc/blob/1a43c47a3d6619d2bc6a0e05899dab900760ecdc/scripts/huggingface.py)实际将query块从源prompt移除后置于原生user，其余政策/身份/context在system；不能凭渲染文件看似单段文字就认定为单user输入。原CSV为U+001E分隔，seed0 main_run3500行；薪资规则本人/HR/主管可以从可见字段验证。本轮显式身份24请求为受控改编，不称正式基准成绩。
- 作者prompt声称只向用户发送brace答案块；全文raw禁用值扫描与应用实际交付分开。本次8个同事失败都在最终块，非只在解释中。新模型资格不能由此自动确认，详见runs/20261028-accessdenied-pilot。
- [Qwen3-8B固定配置](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/config.json)已核对model_type=qwen3、36层/32query/8KV/head_dim128、关闭sliding_window，符合当前Full Attention范围；HF元数据gated=false。只读配置，未获取权重/加载/验证遵从，不能称更强或第二模型族；现Qwen2专用manual Q/K评分须再审Q/K-normalization等差异后才能适配。

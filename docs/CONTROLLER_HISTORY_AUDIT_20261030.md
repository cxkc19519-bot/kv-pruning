# 共享接受率控制器：状态生命周期、查重与最小识别设计

执行更新八（2026-10-30）：[默认图尺寸profile验证](runs/20261030-controller-profile-validation.md)完成2工程回答/64tokens及110raw timing；最终N1直接采样、成本整表独立exact复算和token兼容通过，verify预算成本不再全平台。旧397向量新表N1 CPU重放common/A/B仍全部选4，仅反事实；无本轮真实预算/用户损害/创新结论。draft小差落在测量波动内，JIT/离群样本保留，不报延迟。结束当前固定配置筛查、暂不继续本候选GPU；下一条仅只读审第2线索取消记账的具体契约/执行方/近邻，尚未开始。以下未执行profile计划为历史。

执行更新七（2026-10-30）：[成本profile审查](CONTROLLER_COST_PROFILE_AUDIT_20261030.md)确认原工程capture[5,10]将verify1..5同桶、draft N1由N2补表，原始timing未留存。不能外推默认配置或将dummy计时当完整真实请求代价。10源码blob匹配；默认图几何仅推导未实测，公开熵标签不能保证本模型逐位置qmax覆盖敏感域。新增1CPU run、0回答；下一条只实现禁用2工程回答raw-profile验证方案，未执行，不扩历史/并发矩阵，不宣称损害或创新。

执行更新六（2026-10-30）：[真实自然历史小试](runs/20261030-controller-natural-history.md)完成原30主请求/六探针对照。A/B自然refit并改变θ/预测，但预算都4、admitted28/accepted25、输出相同。N1成本平台使该负载分配饱和；397记录向量仅36unique，离线N2回放无变化，uniform例子的潜在3/8翻转不是正常输入/GPU证据。未发现本配置损害，不否定整个假设；当前不扩模型，下一条仅离线审成本profile/热身及正常请求可达敏感域，尚非论文/攻击结论。v1解析失败与修正v2原始均保留。

执行更新五（2026-10-30）：[真实worker v5工程通过](runs/20261030-controller-worker-v5.md)，固定Triton/命名扩展RPC验证64项FullAttention cache spec及所列空闲控制器状态原址恢复、学习终点与探针token重放、冻结更新；v3/v4失败均保留。phase95为人为工程fixture，不是自然历史影响证据，也不证明整服务/KV/RNG恢复。下一条实现禁用自然历史提案观测钩子/透明性gate后才小筛查，真实损害/创新仍未知。

执行更新四（2026-10-30）：[配对模型与worker记录](runs/20261030-controller-worker.md)。独立环境/原生估计器此前通过；本轮draft/target tokenizer完全一致。两次真实worker初始化失败（eager配置冲突、默认FlashAttention2可变长度图guard），0答案/0 RPC，完整worker状态/真实历史损害仍未知。固定Triton候选仅静态/CPU能力审查、禁用提案未执行；不把该失败当研究假设no-go。旧准备状态以下均为历史。

执行更新二（2026-10-30）：[CPU v2](runs/20261030-controller-history-cpu-v2.md)在原输入/seed/界限下54/54通过，完成自建CPU公式/状态关卡；v1失败保留。真实GPU/异步/完整服务恢复与真实请求损害未验证。只读运行核查和后续条件见[准备清单](CONTROLLER_RUNTIME_PREPARATION_20261030.json)，本轮未安装环境或启动模型；以下“revision2未执行”等均为历史。

执行更新（2026-10-30）：[CPU预检v1](runs/20261030-controller-history-cpu.md)已实现并运行，32通过/1失败/21未执行；整体未通过。失败为我方要求所有无观测尾部案例的共享slope都改变，但源码可拒绝负slope更新。归档独立复算定位后按协议停止，revision2修正准备但未执行，恢复等剩余检查未测。以下“runner未实现/0新run”为本审查时点历史，当前以新run记录/STATUS/HANDOFF为准；无模型或真实影响证据。

日期：2026-10-30（Asia/Singapore）。用户明确从第一条调查线索开始。本轮完成源码/文献审查及禁用的CPU预检提案，没有运行CPU实验、作者测试、模型或攻击。前轮泛预算算法no-go、A搁置和旧guard工程失败不变。

## 本轮判断

**共享且跨请求保留的学习状态这一结构性前提成立，值得继续做有边界的机制预检；尚未发现真实攻击、正常用户损失或已成立的新贡献。** 不能仅因它与TTA投毒类似就宣布新意，也不能仅因存在通用TTA论文就断言这个具体控制问题已解决。

调查问题限定为：在相同正常探针请求、无前序请求残留计算的条件下，受限前序请求流是否通过共享校准状态，改变正常探针的验证预算并产生实际效率损失；在冻结/干净恢复/来源隔离等简单基线下是否仍存在有意义的权衡？不重新提出接受率预算算法，不声称目标LLM权重发生变化。

当前允许继续准备CPU代数/状态预检；不进入模型实验或新方法开发。CPU提案[controller-history-preflight-proposal-v1.json](../configs/controller-history-preflight-proposal-v1.json) execution_enabled=false、runner_implemented=false，尚非运行结果。下一步具体实现该预检，不再无界泛搜候选；通过后才另立真实模型方案。

## 固定来源及生命周期

官方release API本轮仍报告latest稳定版本v0.32.0（2026-10-18）。主要来源固定commit **5df63a7203cdb9328d824a27b682e77c7b9928be**。[来源索引](CONTROLLER_HISTORY_SOURCE_20261030.json)记录5个文件及上游变更核查。只读获取；除估计器外，其余按相关构造/调用/删除/测试段审查，不声称全仓审计。

| 阶段 | 固定源码位置 | 已确认事实 |
| --- | --- | --- |
| 创建 | [speculator.py:250](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/speculator.py#L250) | 所审DraftModelSpeculator加载时创建一个OnlineAcceptanceEstimator，不是每个请求各建一个。仅讨论启用该估计器的路径，不能推广到带独立confidence head的所有drafter。 |
| 共享参数 | [acceptance_estimator.py:340](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/acceptance_estimator.py#L340) | 一个共享slope、按draft位置的intercepts；features/predictions另按请求槽存储。作用域是该worker/speculator实例；源码说各rank独立同样更新，不能叫任意副本间共享。 |
| 收集反馈 | [同文件:45](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/acceptance_estimator.py#L45)、[speculator.py:489](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/speculator.py#L489) | 标签只包含已接受位置和首个拒绝位置，且必须在实际admitted范围内；不把拒绝后的所有位置都标0。observe在下一次propose覆写features前执行。 |
| 更新 | [acceptance_estimator.py:329](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/acceptance_estimator.py#L329)、[同文件:405](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/acceptance_estimator.py#L405) | 每100次step调用重估，不是100个请求/100个token。统计按观测累积，没有所审实例内的租户维度；n/(n+50)阻尼、Newton系统L2=1e-3、非负slope/NaN防护已有。它们不是已证明的租户影响上界。 |
| 重估后 | [同文件:133](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/acceptance_estimator.py#L133) | 更新slope/intercepts后清info/grad/counts，拟合系数保留。L2加在Newton方程中，不能未经推导称为会把参数拉回干净状态的权重衰减。 |
| 加入请求 | [adaptive_verification.py:183](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/adaptive_verification.py#L183)、[model_runner.py:1200](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py#L1200) | 新请求的置信度槽置1并记录pending reset，不重置共享估计器参数；首步乐观初始化可能暂时掩盖历史影响。 |
| 结束请求 | [model_runner.py:1134](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py#L1134) | 所审remove/finish链释放请求状态，不重建估计器，也不清共享参数/尚未重估统计；请求结束不等于控制器遗忘。 |
| 影响决策 | [adaptive_verification.py:282](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/adaptive_verification.py#L282) | 根据滞后置信度、位置生存概率与成本曲线选择总预算，再分配验证槽。预测变化未必越过离散预算边界，越过边界也未必降低真实goodput。 |

### 不能省略的两个修正

**观测缺失只是候选机制。** 后部位置未被admit就没有标签，可能拖慢再校准；但正确的条件生存模型可以使用截断反馈，单纯存在删失不证明统计有偏或无法恢复。共享slope仍可随别的位置更新，所以没有后部标签也不意味着后部预测完全不动。上游测试已有“无观测位置intercept不动、共享slope可动”的案例，本轮仅阅读，未执行。

**JIT/预热是明确混杂因素。** 官方文件历史最新变更为[458334f00f7cbff7c8a1feae449656aa7343c476（2026-10-28）](https://github.com/vllm-project/vllm/commit/458334f00f7cbff7c8a1feae449656aa7343c476)，已审估计器/对应测试patch：固定accumulate kernel形状，并增加warmup清统计/预编译refit。该warmup不清学习系数，不是每请求隔离修复。不能用0.32.0某个分支首次refit编译造成的暂停当持续攻击，也不能只给干净分支使用该修复。未来实际运行需选定共同版本并核实预热后状态，不能混版本比较；本轮没有安装或应用patch。

## 查重结果与主张边界

| 一手来源及本轮阅读范围 | 已覆盖内容 | 本问题仍需证明的区别 |
| --- | --- | --- |
| [Test-Time Poisoning 2308.08505v1](https://arxiv.org/html/2308.08505v1)，§3/§5.5–5.6/§6相关段 | 共享在线更新遭输入投毒、顺序/正常样本恢复/非i.i.d.热身已研究 | 跨请求持续影响及恢复慢本身不是首次；这里标签来自真实target验证而非任意伪标签，影响目标为控制器决策成本，尚未实测 |
| [Realistic TTA Poisoning 2410.04682v3](https://arxiv.org/html/2410.04682v3)，§3.1–3.2/§5.4及相关段 | 已强调无实时权重、不可见其他用户数据等现实假设；阈值/EMA/恢复等防御已有 | 不能允许对外攻击者改系数、伪造accept标签或看正常探针后优化；白盒状态恢复仅用于研究归因 |
| [APEX 2610.07780v1](https://arxiv.org/html/2610.07780v1)，§4.3/§4.8/结论，交叉核对官方PDF | 已把accepted length作为删失生存反馈，按真实反馈选择深度；部署时网络参数固定，历史状态随请求变化 | 不能把删失反馈/生存建模当创新；不能因其叫online controller就断言它在线更新共享参数 |
| [OSD，ICML2024正式入口](https://proceedings.mlr.press/v235/liu24y.html)，摘要 | 已利用到达的用户查询持续更新draft模型 | 不是本次轻量控制器的同一更新对象；只读摘要，未判定所有安全评估覆盖 |
| [OnlineSPEC，ICML2026正式入口](https://proceedings.mlr.press/v306/qian26k.html)，摘要 | 已将验证反馈与在线学习、动态regret及draft演化联系 | 本轮未审完整证明/作者实现，不把它当已排除的安全近邻或直接迁移其保证 |

定向检索没有得到一篇可确认完全覆盖该固定估计器跨请求隔离问题的直接论文；这是检索范围内的结果，不是不存在先前工作的证明。通用TTA/在线学习迁移风险仍高，当前不提出新算法。APEX已有删失处理也不能自动证明这个共享在线校准器安全。

## 最小可证伪设计（真实模型阶段尚未启用）

因果链必须逐段成立：前序请求历史不同 → 持久控制状态不同 → 同一正常探针的预测/实际预算不同 → 正常用户真实成本变差。只证明参数改变，或把人为构造logits改动叫输入攻击，都不足以立题。

先不设计攻击文本，用固定正常工作负载的分布切换探测机制。设共同的干净、已预热检查点C；分别回放普通历史H0和不同分布历史H1，全部请求结束且GPU工作同步后，再运行固定探针P。探针不可用于选择H1；将来若研究攻击，开发/留出探针分开，并约束请求/token/时间预算。不同接受率下请求数、token数、执行步数、标签数不能同时自动相等，必须明示主预算及其他差异，不能写成全条件等预算。

必要对照：

1. **共享在线**：C→H0/H1→P。描述历史效应，尚不足以归因。
2. **冻结干净系数**：H0/H1都执行、都计入成本，但系数固定于同一个已热身C，禁用学习统计对后续更新的影响。若仍有差异，优先查缓存/预热/温度等混杂。
3. **共同干净恢复**：H0/H1结束后均恢复C的全部控制状态再P；不能只恢复θ却留下info/grad/counts与100步相位。恢复初始默认系数另列冷启动，不能和干净热身混称reset。
4. **状态移植归因**：在相同非控制器状态下分别移植θ与完整控制状态；可拆分待更新统计/相位和已拟合参数的作用。白盒操作仅诊断，不当部署攻击能力。
5. **来源隔离/简单稳健对照**：可信harness按来源独立校准，或限制每来源更新贡献；另考察现有阻尼/冻结/周期恢复的效用代价。不能将租户ID直接当任务分布，也不能只对“恶意来源”特殊处理而给普通用户冷启动。
6. **恢复观察**：固定后续正常请求/步数上限，记录是否恢复及未恢复的截尾，不跑到出现所需结论。至少跨越100步重估边界并报告真实观测数量；具体模型预算待实现/任务检查后冻结。

控制器完整快照至少包括slope/intercepts、info/grad/counts、step相位/重估计数；调用链另包括features/predictions槽、CPU/GPU置信度双缓冲、pending resets和stale索引。非控制器因素包括请求/KV/prefix缓存、成本profile、热身编译、采样参数/随机状态、批组成、模型权重、排队和GPU热状态。实际CUDA Graph张量恢复需保持地址/形状约束，未经实现核查不声称可无损恢复整个服务。

观测：每位置预测及可观测标签、标签覆盖率、预算/真实验证长度、正常请求完成代价/逐token时序与恢复轨迹。每步拟议数量不等于实际GPU验证成本；客户端chunk间隔不等于token时延。离线全深度反馈可作额外诊断，但包含线上未获得的标签，不能宣称它是免费部署防御。当前不估p99或SLO保证。

停止条件：无实际预算变化；同一干净恢复后仍有差异而无法定位；只见正常分布变化且无安全/性能实质；效果仅JIT/缓存/步相位解释；简单冻结/隔离既消除损失又无实质效用代价；现实受限请求不能改变状态。满足任一项则保留负结果，不改名扩大方法主张。发现真实影响后仍须重新查重，不能把工程确认等同创新确认。

## 下一步：只实现有上限的CPU代数与状态预检

禁用提案最多64 fixture、每例256次step、CPU运行60秒；K=4/maxreq=8只属合成工程fixture，不是模型实验参数。六类检查包括：独立dense线性系统与arrowhead更新、观测mask、无观测位置/共享slope、空轮次、99/100步清统计与保留系数、完整快照恢复及请求槽换序。比较采用float64 atol1e-9/rtol1e-8，仅CPU代数口径；不当GPU FP32/Triton等价。

预检须在服务器运行，按公共模板保留全部失败和来源摘要，失败即停，不自动重试；不执行作者代码、不加载模型、不联网或安装依赖。即使通过，也只证明自建参考的公式/状态实现，不证明真实输入可操纵、GPU实现正确、性能退化或新颖性。当前runner尚未实现/执行，无新run；下一条可直接实现该固定预检，避免重复本轮来源审查。

## 本轮执行边界

0新CPU实验run、0新主要/工程答案；无模型/数据下载、依赖/环境/服务操作，无GPU/模型进程探测，78run2702沿历史。误读方向内不存在的EXPERIMENT_TEMPLATE路径后已改读上级公共模板，不是实验失败；误猜PMLR liu24ai页面实际为其他论文，已改用检索确认的OSD liu24y正式入口，不将误页作为证据。未复制nano-vllm，未改其他方向。报告/来源索引/禁用提案与状态文档同步服务器；GitHub项目远端未配置，无push。

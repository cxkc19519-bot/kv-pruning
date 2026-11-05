# 研究问题重定：局部约束解码下的KV裁剪目标失配

2026-10-31最新：[H3固定12组筛查完成并停止当前候选](H3_SCREEN_DECISION_20261031.md)，[主记录](runs/20261031-decoder-h3-screen.md)/[readiness](DECODER_H3_SCREEN_READINESS_20261031.json)优先。先[共同batch工程](runs/20261031-common-batch-engineering.md)通过：2组Full+8候选18状态正反序36logits逐字节及KL精确重复、hook/nohook cache相同、实际mask/1008efficient/gather独立验证；这是新固定缓存流程，不救回原跨路径0.25/0.001 gate。随后原12DEV Full12/12通过≥10，8候选96+Full12共108向量全部完成。真实KV目标排序反转11/12已观察，但global/Top128/Top256/legal四目标所选均12/12保留Full正确决策，legal相对每基线0win/0loss/12tie，development_go=false。固定候选保真Snap10/recency8/六随机6/9/9/9/6/7，不能说裁剪完全无损；generic KL/TopK已选到正确缓存，无合法目标增益。独立stdlib复算384 KL/全部选择转移/Full支持/maps/masks/trace/4权重7metadata通过。当前H3停止，不扩题/seed/预算/模型/更难prompt救回，不以只排序不同承诺新颖性或毕业。原launcher real_KV_signal_observed=false为初始化未更新，semantic_closure明确真实反转true/实用go false，原manifest不改。工程worker1431879/validator1433053/launcher1431874与screen1450114/1451208/1450109全部exit0并核退出；GPU1收尾18MiB/0%。两阶段新增2GPUrun/144logits/172forward/13900输入token/28编码/0完整答案，累计132run3038主，新索引b0c4d8fd…；screen原164文件68140344bytes，加closure/derived166文件68159219bytes，原manifest256b9fd6…/derivedfbfa685d…全回读。系统原型/原48技术报告及旧QA/Mistral false/停止队列保持，代码配置文档同步服务器、原始仅服务器、GitHub未配置、当前无运行任务。本条取代旧H3筛查待办；新问题须独立需求和强近邻不足，不能改名重启。

日期2026-10-31。依据[上一轮查重决策](CONTRIBUTION_SCOPE_DECISION_20261030.md)，本轮不再以“压缩会破坏指令”立题。重新检索直接近邻并给出一个可证伪的窄候选；当前只完成原文审阅与合成概率反例，未证明真实KV中存在该问题或独立研究新颖性。

## 三个候选的去留

| 候选 | 本轮结论 | 依据 |
| --- | --- | --- |
| H1：加JSON约束解码或后处理，恢复格式 | 不作为主创新 | [结构/语义双轴研究](https://arxiv.org/html/2609.23742v1)已有语法合法但内容仍错的分析；合法格式本身不等可靠内容，旧48题不能因事后包装而改分 |
| H2：按parser结构角色保留KV | 宽泛表述否决 | [PASK v2](https://arxiv.org/html/2608.28276v2)已用parser转换/结构职责及校准策略控制KV保留，不能把语法感知KV称空白 |
| H3：自由分布目标是否会给实际局部mask解码选错缓存？ | 仅保留为小规模筛查候选 | 目标非常具体：比较同输入、同预算候选KV掩码在全词表/通用Top-K和当前合法token集合上的排序及决策是否失配；没有声称此前无人研究 |

优先H3是本项目推断：当前两条件joint都触底，而简单格式修复/结构保留都有直接先例，值得检查压缩选择目标是否匹配**实际部署的局部token mask**。不是由旧48组结果推导出H3已成立，也不将旧题重新调试为新证据。

## 正式问题与量

固定模型、完整可见前缀及语法状态。P是Full KV的下一token分布，Q_M是候选等预算KV掩码M下的实际下一token分布；A是语法引擎在**同一个生成前缀**允许的token集合，不能由gold或压缩结果选择。

```text
P_A(i) = P(i) / sum_{j in A} P(j), i in A
Q_M,A(i) = Q_M(i) / sum_{j in A} Q_M(j)
J_V(M) = KL(P || Q_M)
J_A(M) = KL(P_A || Q_M,A)
```

问题是：最小化J_V或通用Top-K近似，是否会在真实等预算KV候选中偏好更易改变合法语义选择的掩码，而J_A作出的选择更接近Full的局部受限决策？首先检查现象，不先开发新淘汰算法。

这里的P_A仅是**本步合法集合上的局部重归一化分布**，不是完整字符串在“最终满足整部语法”条件下的精确分布。[Grammar-Aligned Decoding v4](https://arxiv.org/html/2405.21047v4)已说明二者的差别。单个候选内，重归一化不会改变合法token之间的argmax顺序；候选问题关心的是不同KV掩码的评价/选择顺序。

[Behavior-Preserving KV Compression v1](https://arxiv.org/pdf/2610.06479v1)已有输出KL目标，并在实现中使用Full分布Top-K重归一化（prefill默认K128、generation默认K256，附录B/Table3）。因此“用KL”“限制support后再KL”都不能作为新点；实际筛查必须包含通用Top-K对照，后续方法还须对比直接把mask加入既有KL目标的简单组合，而不是只打attention弱基线。本轮未复现该作者算法或审计其实现代码。

PASK v2使用结构标签、任务误差敏感度与attention-output distortion等机制；本轮所审正文没有建立它与H3目标完全等价，也不能据未检出相同公式声称它不支持该能力。代码层和更广检索仍有不确定性。[XGrammar2](https://arxiv.org/abs/2601.04426v1)提供动态结构化生成机制，但本项目尚未集成或运行，不能假定兼容。

## 已核算的概率反例

允许集合A={合法A,合法B}，第三个token X非法，以下概率完全是构造值，不是模型logits。

| 分布 | 合法A | 合法B | 非法X |
| --- | ---: | ---: | ---: |
| Full P | 0.09 | 0.01 | 0.90 |
| 候选Q1 | 0.01 | 0.09 | 0.90 |
| 候选Q2 | 0.45 | 0.05 | 0.50 |

| 指标 | Q1 | Q2 |
| --- | ---: | ---: |
| J_V，nats | 0.1757779662 | 0.3680642072 |
| J_A，nats | 1.7577796619 | 0 |
| 局部受限argmax是否与Full一致 | 否，选B | 是，选A |

J_V偏好Q1，J_A偏好Q2。KL分解解释这一点：

```text
a=P(A), b=Q(A), Ac为补集
KL(P||Q)
 = KL(Bernoulli(a)||Bernoulli(b))
 + a * KL(P_A||Q_A)
 + (1-a) * KL(P_Ac||Q_Ac)
```

这是标准条件分解的应用，不是新定理。本例a=0.1，Q1的合法部分损伤被0.1加权，Q2的变化来自合法/非法总质量而非合法部分内部排序。已用独立算式复核数值、分解、全词表mask退化为原KL、单合法token时J_A=0三个对照。

**未满足的关键条件：Q1/Q2还没有被证明能由同一个真实模型、同一个输入、两个等物理KV预算掩码产生。** 反例只排除“两个排序必然相同”的一般性断言，不能证明实际压缩算法有缺陷、候选已经可发表或任务质量必然改善。

## 一次有否决线的后续筛查

[筛查草案](DECODER_OBJECTIVE_SCREEN_DRAFT_20261031.md)与[禁用配置](../configs/decoder-objective-screen-draft-v1.json)只定义下一交付，不是已执行或现成GPU命令。

先实现有限枚举语法/候选KV mask/稳定概率统计的CPU正确性检查，再另行冻结12个**新开发组**的同前缀logit诊断：Full加8个预定等预算候选，记录J_V、J_Top128、J_Top256、J_A、合法质量和局部argmax。不使用原48题救回结果，不增大旧题输出上限。

只在2个以上合法token的语义分支测排序，排除必然token的零KL假象。固定JSON wrapper前缀不含gold；每个候选都从裁剪后的prefix重新处理同一query+wrapper，不能沿用Full生成的suffix KV而偷偷保留上下文信息。诊断是query已知、同前缀的oracle比较，**不等于原query-blind选择器或可部署新算法**。

如果未观察到真实KV排序失配、差异没有影响合法决策、通用Top-K已经同样解决、或者直接简单组合无实用增益，则停止该候选，不扩模型/预算搜信号。通过小筛查也只是开发信号，需要新独立组、强近邻对照和成本验证才能谈论文贡献。

## 本轮交付与范围

五个固定原文快照与合成算术证据在服务器`literature/20261031-decoder-aware-candidate-v1`，10文件2266407bytes，manifest SHA `ea36b38a02db149812649eace16c321e92786a7da17fb4eaa00f086e717f2963`。限定组合检索未证明文献空白；检索误命中的grammar编译缓存、prefix复用驱逐和权重量化不混作近似KV裁剪证据。

本轮0模型forward/回答、0分词/权重/GPU查询、无作者代码执行或依赖安装，累计120run3038主和旧全部结果不变。H3状态是“值得一次正确性与小规模诊断筛查，尚未证实”，不是新题已定、旧48实验改判或新方法已实现。

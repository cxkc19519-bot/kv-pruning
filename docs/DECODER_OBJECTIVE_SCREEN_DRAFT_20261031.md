# H3：解码目标失配的有界筛查草案

2026-10-31最新：[H3固定12组筛查完成并停止当前候选](H3_SCREEN_DECISION_20261031.md)，[主记录](runs/20261031-decoder-h3-screen.md)/[readiness](DECODER_H3_SCREEN_READINESS_20261031.json)优先。先[共同batch工程](runs/20261031-common-batch-engineering.md)通过：2组Full+8候选18状态正反序36logits逐字节及KL精确重复、hook/nohook cache相同、实际mask/1008efficient/gather独立验证；这是新固定缓存流程，不救回原跨路径0.25/0.001 gate。随后原12DEV Full12/12通过≥10，8候选96+Full12共108向量全部完成。真实KV目标排序反转11/12已观察，但global/Top128/Top256/legal四目标所选均12/12保留Full正确决策，legal相对每基线0win/0loss/12tie，development_go=false。固定候选保真Snap10/recency8/六随机6/9/9/9/6/7，不能说裁剪完全无损；generic KL/TopK已选到正确缓存，无合法目标增益。独立stdlib复算384 KL/全部选择转移/Full支持/maps/masks/trace/4权重7metadata通过。当前H3停止，不扩题/seed/预算/模型/更难prompt救回，不以只排序不同承诺新颖性或毕业。原launcher real_KV_signal_observed=false为初始化未更新，semantic_closure明确真实反转true/实用go false，原manifest不改。工程worker1431879/validator1433053/launcher1431874与screen1450114/1451208/1450109全部exit0并核退出；GPU1收尾18MiB/0%。两阶段新增2GPUrun/144logits/172forward/13900输入token/28编码/0完整答案，累计132run3038主，新索引b0c4d8fd…；screen原164文件68140344bytes，加closure/derived166文件68159219bytes，原manifest256b9fd6…/derivedfbfa685d…全回读。系统原型/原48技术报告及旧QA/Mistral false/停止队列保持，代码配置文档同步服务器、原始仅服务器、GitHub未配置、当前无运行任务。本条取代旧H3筛查待办；新问题须独立需求和强近邻不足，不能改名重启。

2026-10-31。状态：**未实现/未执行，execution=false**。研究问题与直接近邻见[重定稿](RESEARCH_QUESTION_REDEFINITION_20261031.md)。原48组、旧QA/Mistral关卡和所有停止队列不修改；本草案不是自动启动许可或可复现的GPU命令。

## P0已完成：理论可能性，不是模型证据

三token构造中全词表KL与局部合法集合KL给出相反候选排序，并对应相反合法argmax。独立算式、KL分解及全词表/单token对照通过。没有真实KV掩码、模型logits或新增科学样本；公式本身是标准数学，不作为方法贡献。

## P1之前必须完成：CPU正确性与运行协议

1. 在所有合法候选上构造有限token-trie，不按gold裁词表；检查所有枚举输出均可达、非法路径被拒、EOS/UTF-8/跨token边界、空合法集和终止行为。不同标签不能仅假设都是单token。
2. 选择语义分支的共同前缀；区分局部mask分布与全序列grammar-conditioned分布。单合法token和全词表mask作为必需负对照。
3. 用logits的稳定log-sum-exp计算全词表/Top128/Top256/合法support上的KL，显式处理空集、零质量、NaN/Inf、极端小概率与并列，不用裁掉非法质量来掩盖数值错误。
4. 构造8个预先规定且同物理KV预算的候选：prefix-only Snap适配1、recency1、6个固定随机seed；sink4/recent64计费。所有掩码/seed都报告，不挑最好seed。最终精确seed、native边界与byte数须在真实logits前另冻。
5. 每个候选仅gather已有prefix K/V并重新处理完全相同的query+非gold wrapper；Full参考的query/wrapper KV不得注入裁剪分支。所有Full层、dtype、位置、gather、参考不变性要重新按新入口审计。
6. 规范化证据区分“同前缀一次logit诊断”“受限greedy决策”和“完整自由生成”；禁止把本次oracle排序当部署策略性能。新角色/runtime/输入协议与源码须另冻，现有工程证据不能自动复用。
7. 若库/API不适配，先停下记录；不在本草案下安装新依赖、下载模型/数据或放宽旧guard。

CPU代码与validator还未实现，当前没有新的实验输入或GPU runner。下一具体交付就是上述正确性入口和可复核有界协议。

## P1拟定范围：只回答“真实失配是否值得继续”

使用既有、已核28层Full Attention Qwen2.5-7B；12个新、固定开发上下文组，一个共享枚举schema，语义任务为从可见事实确定一个合法枚举值。避免可仅靠格式推断答案，位置/标签/干扰信息固定平衡；不凭Full正确或压缩效果挑题。输入/模板/语法/标签token化/选择器列表在任何模型结果前冻结。不调用原48预留题或旧16封存题。

Full与8候选最多形成108个同前缀logit向量（12×9），它们不是108个独立样本，也不自动计为108个完整生成回答。工程资源上限暂预留14次路径观测，具体调用数/forward/token/时间上限需执行协议另定。只检查有限枚举的首个可判别语义分支，不据一处logit推断长序列表现。初始范围不训练或设计新selector，不追加保护/新预算/第二模型。

预定目标：比较所有候选排序，以及按J_V、J_Top128、J_Top256、J_A分别选出的掩码是否保留Full合法argmax，并报告gold EM作为单独任务结果。所有选择目标不看gold；共同wrapper不是答案前缀泄漏。排序重复、ties、不可行、截断/未完成与错误单列；预留独立组只在后续协议定义，不将本12开发组当确认集。

## 开发筛查的停止线草案

- Full有限枚举任务若低于10/12正确，或工程/语法/物理预算失败，停止；不修题/提示让它过线。
- 至少3/12组出现J_A与未约束或通用Top-K候选排序实质差异，并至少2组体现为合法argmax保真不同，才值得考虑下一阶段。这是节省工作量的开发门槛，不是显著性、功效或总体可靠性保证。
- “不同”本身不证明更优：若J_A造成额外决策损伤，不能只统计修复；报告全部赢/平/输。如果Top128/256已消除差异，不把结果宣称语法目标特有优势。
- 如果观测只发生在必然token、特意构造的非法格式、极端数值病态或不等预算，否决。
- 若只改现有KL的support就能解释全部结果，不能称新算法；系统/实证价值还需真实场景、强对照与开销证明。后续方法比较至少面对直接masked-KL组合与PASK等近邻，不能仅靠弱基线曲线。
- 没有开发信号就结束H3，不自动扩样本/seed/预算/模型。存在信号才另冻独立验证与可部署成本方案。

当前只进行了原文和合成概率检查。以上P1未启动，不能据“草案待做”加载权重。

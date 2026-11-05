# KV 压缩与约束保持：精选阅读清单

检索核对日期：2026-11-03（Asia/Singapore）。按用户要求优先代表性主会论文，补充两篇与现有实现/风险控制直接相关的预印本。以下为基于作者摘要的中文概述，不是逐字翻译；相关性判断另列。只核对公开论文页面与摘要，不表示全文或实现已审计、结果已复现。性能数字均为作者在各自设置下报告，不能横向比较或视为普遍保证。

范围：原方向为普通 Full Attention Transformer 的 KV 压缩与约束保持；最新交接另外延伸到结构化输出后端，末两篇为该分支。当前执行断点仍是 2026-11-02 资源可观测性协议，本文不改变实验队列或停止决定。

## 1. The Pitfalls of KV Cache Compression

Alex Chen 等；ACL 2026 主会长文。

中文摘要概述：现有 KV 压缩评估常强调平均任务成绩基本不变，却较少检查多个指令并存时的行为。论文发现不同指令对压缩的敏感性差异很大，部分指令可能先被模型忽略；以系统提示泄漏为例，分析压缩策略、指令顺序及淘汰偏置如何影响泄漏和指令遵循，并提出调整淘汰策略来改善多指令任务表现。

阅读价值：与本方向最直接，优先阅读；用于理解为什么平均准确率不足，以及规则保护/公平淘汰已经有哪些先例。

[官方论文及摘要](https://aclanthology.org/2026.acl-long.1926/)

## 2. When Efficiency Meets Safety: A Benchmark Security Analysis of KV Cache Compression in Large Language Models

Xiaoxiao Ma 等；ACL 2026 主会长文。

中文摘要概述：在四个模型家族和多类越狱攻击上，论文发现压缩具有双面安全影响：淘汰恶意语义和离散压缩造成的梯度失配可能使部分攻击失效；另一方面，浅层激进的缓存合并可能破坏功能性注意力头，使人工设计的攻击更容易成功。作者提出结合历史信息、按注意力头反馈的 Safe-CAM 合并策略，在文中实验中恢复安全表现并兼顾正常任务。

阅读价值：避免预设压缩一定降低安全性；需要区分位置淘汰和缓存合并的机制。

[官方论文及摘要](https://aclanthology.org/2026.acl-long.1123/)

## 3. RobustKV: Defending Large Language Models against Jailbreak Attacks via KV Eviction

Tanqiu Jiang 等；ICLR 2025。

中文摘要概述：与直接识别或抵消攻击提示不同，RobustKV 通过删除缓存中的部分 KV 来削弱隐藏有害请求的影响。论文认为，越狱包装需要吸引足够的注意力，可能使其隐藏的有害问题获得较低的重要性；据此淘汰低排名 token 的 KV，可阻止模型给出有害问题的有效回答。作者在多种模型和攻击上评估防御、正常任务效用和自适应攻击。

阅读价值：理解 KV 淘汰如何成为主动防御，也为第二篇的双面效应提供具体方法背景。

[官方论文及摘要](https://proceedings.iclr.cc/paper_files/paper/2025/hash/38bbae17d60940f3ee14dfd1035d7542-Abstract-Conference.html)

## 4. H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models

Zhenyu Zhang 等；NeurIPS 2023。

中文摘要概述：KV 缓存随序列长度和批量线性增长。作者观察到少量 token 占据大部分注意力贡献，删除这些重要 token 会显著损害质量，因此提出在最近 token 与重度贡献 token 之间动态分配缓存的 H2O。论文将淘汰建模为动态次模问题，在给定假设下给出理论保证，并评估生成质量、吞吐和延迟。

阅读价值：注意力重要性淘汰的基础工作；用于理解累计注意力评分与近期窗口的组合。

[官方论文及摘要](https://proceedings.neurips.cc/paper_files/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract-Conference.html)

## 5. Efficient Streaming Language Models with Attention Sinks（StreamingLLM）

Guangxuan Xiao 等；ICLR 2024。

中文摘要概述：仅缓存最近 token 的窗口注意力，在文本长度超过窗口后可能出现质量崩溃。论文发现初始 token 即使语义不重要，仍会承担注意力汇聚作用；保留少量这样的 attention sink，再结合近期窗口，可以在不微调的情况下稳定处理很长的文本流。作者还研究预训练时加入专用 sink token 的效果。

阅读价值：理解 sink+recent 简单基线。稳定处理长文本流不意味着可以找回已经淘汰的早期事实，这一区别应在后续使用中明确。

[ICLR 正式论文](https://openreview.net/pdf?id=NG7sS51zVF)；[作者项目页](https://hanlab.mit.edu/projects/streamingllm)

## 6. SnapKV: LLM Knows What You are Looking for Before Generation

Yuhong Li 等；NeurIPS 2024。

中文摘要概述：论文发现生成期间，各注意力头关注的提示位置具有一定稳定性，而提示末尾的一小段观察窗口可以提前揭示这些位置。SnapKV 无需微调，依据观察窗口的注意力为各头选择并聚合重要缓存位置。作者在长序列任务中报告较低的缓存开销与更快的生成速度，同时保持接近完整缓存的成绩。

阅读价值：本方向核心基线；需要注意评分观察窗口能否看到问题，不能把不同 query 可见性当作同条件比较。

[官方论文及摘要](https://proceedings.neurips.cc/paper_files/paper/2024/hash/28ab418242603e0f7323e54185d19bde-Abstract-Conference.html)

## 7. Ada-KV: Optimizing KV Cache Eviction by Adaptive Budget Allocation for Efficient LLM Inference

Yuan Feng 等；NeurIPS 2025（初稿 2024）。

中文摘要概述：不同注意力头具有不同的注意力分布，但许多压缩方法为它们分配相同预算。作者推导淘汰前后注意力输出误差的上界，据此设计按头自适应的缓存预算分配策略 Ada-KV，可与已有淘汰方法结合。论文在 RULER 和 LongBench 的多项任务中，同时评估已知问题与未知问题的压缩场景。

阅读价值：区分“保留哪些 token”和“各头分多少预算”两个变量；为等预算对照提供基础。

[官方论文及摘要](https://proceedings.neurips.cc/paper_files/paper/2025/hash/a40ff56daab9f4808b1e18350c8a11ce-Abstract-Conference.html)

## 8. KVzip: Query-Agnostic KV Cache Compression with Context Reconstruction

Jang-Hyun Kim 等；NeurIPS 2025。

中文摘要概述：为一个具体问题优化的压缩缓存，复用于其他问题时可能明显退化。KVzip 不依赖未来问题，而是让原模型尝试从缓存重建原始上下文，以重建过程评估 KV 对的重要性，删除低重要性项。作者在问答、检索、推理和代码理解中报告 3–4 倍缓存缩减及约 2 倍 FlashAttention 解码延迟改善，并测试同一压缩上下文的多问题复用。

阅读价值：复用前缀、多查询与未知 query 场景的重要代表。

[官方论文及摘要](https://proceedings.neurips.cc/paper_files/paper/2025/hash/f4eaa4b8f2d08edb3f0af990d56134ea-Abstract-Conference.html)

## 9. Expected Attention: KV Cache Compression by Estimating Attention from Future Queries Distribution

Alessio Devoto、Maximilian Jeblick、Simon Jégou；2025 arXiv 预印本，本次未据官方来源确认主会发表。

中文摘要概述：按注意力压缩面临未来 query 不可知、FlashAttention 不显式保存完整注意力矩阵两项困难。Expected Attention 利用激活的分布特征，以闭式计算估计未来 query 对各 KV 对的关注程度，进而排序裁剪，尽量降低残差流受到的影响。方法无需训练，可用于 prefill 和 decode；论文同时发布包含二十余种方法的 KVPress 库。

阅读价值：与本项目已有 EA 评分实现直接相关；代表不读取完整 attention matrix 的评分路线。

[作者论文及摘要](https://arxiv.org/abs/2510.00636)

## 10. Risk-Controlled KV-Cache Eviction: From Memory Budgets to Risk Targets

Beomgu Kang 等；2026-09 arXiv 预印本，本次未确认正式录用。

中文摘要概述：平均质量下降很小，也可能掩盖少数请求的严重退化。论文将风险定义为相对同一请求的完整 KV，效用下降超过容忍阈值的总体概率。给定风险目标和置信要求，利用校准数据对保留策略进行有限样本认证；如果没有压缩策略通过认证，则回退完整 KV。实验表明相同风险合同在不同模型和任务上允许的压缩程度差异很大，经验退化率较低也不一定通过认证。

阅读价值：与“压缩后保持约束”的可靠性表述直接相邻；预印本身份与正式主会工作分开看待。

[作者论文及摘要](https://arxiv.org/abs/2609.27981)

## 11. XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models

Yixin Dong 等；MLSys 2025。属于最新结构化输出分支。

中文摘要概述：代码、工具调用等应用需要输出符合语法，但逐 token 的上下文无关文法检查会增加运行开销。XGrammar 将词表分为可预检查和需要运行时解释的部分，结合文法变换、持久化栈及与 GPU 推理重叠执行来加速约束解码。作者报告相对既有方案超过十倍的语法处理加速，并在 H100 低延迟推理场景中实现接近零的附加结构化生成开销。

阅读价值：直接对应当前审阅的后端。论文中的效率结果不替代本项目的语义一致性、取消或资源归还测量。

[官方论文及摘要](https://proceedings.mlsys.org/paper_files/paper/2025/hash/5c20ca4b0b20b0bd2f1d839dc605e70f-Abstract-Conference.html)

## 12. Grammar-Aligned Decoding

Kanghee Park 等；NeurIPS 2024。属于结构化输出分支。

中文摘要概述：逐步屏蔽不合法 token 虽能保证输出符合语法，却可能扭曲模型原有概率分布，降低输出质量。论文提出 grammar-aligned decoding 问题和 ASAp 算法，利用已有样本估计不同前缀未来完成为合法输出的可能性，在保证语法合法的同时，使采样对齐于原模型在语法约束下的条件分布。作者在代码生成和结构化 NLP 任务中评估质量。

阅读价值：区分语法合法、采样分布与任务质量；不把格式通过当成内容或权限正确。

[官方论文及摘要](https://proceedings.neurips.cc/paper_files/paper/2024/hash/2bdc2267c3d7d01523e2e17ac0a754f3-Abstract-Conference.html)

## 建议顺序

先读 1、2、6、8；再补 4、5、7 理解基线，3 理解安全防御，9 对照已有 EA，10 理解风险合同。如果重点转到最新结构化输出分支，先读 11、12。

本清单是精选入门阅读，不是完整查新结论。没有以搜索未命中证明研究空白，也没有据摘要声称具体方法已验证。

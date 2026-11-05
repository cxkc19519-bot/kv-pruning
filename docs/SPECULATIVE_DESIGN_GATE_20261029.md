# 投机解码跨用户干扰：源码与文献门槛结论

日期：2026-10-29（Asia/Singapore）。承接[收敛报告](RESEARCH_CONVERGENCE_20261029.md)规定的单次审查。只读官方来源，未导入/执行作者代码，未安装vLLM或启动模型/压测。下文区分源码观察、论文报告和本项目判断。

## 决策

**当前不进入新算法开发或模型实验。** “按接受率计量/分配投机预算”已有直接方法及实际实现；“相同token配额下跨用户尾延迟是否仍受损”保留为未测问题，没有证据支持它超出现有自适应验证、回退及公平调度的直接适配。此结论是不通过当前立题门槛，不是实测证明现象不存在，也不是声称现有实现保证了租户隔离。

| 门槛 | 本轮结论 |
| --- | --- |
| 新预算/成本感知算法主张 | no-go：LAPS-SD与vLLM Adaptive Verification有直接覆盖 |
| 跨用户实证课题的独立差异 | 未建立：吞吐优化不等于延迟公平，但尚无强基线不足证据 |
| 基本逐请求接受率观测 | 静态接口可用，未运行验证；不是只能读全局Prometheus |
| 每请求在线完全回退/租户公平对照 | 所审请求schema无现成控制；内部可扩展，但适配与正确性/成本未审清 |
| 固定Full Attention模型与本机实验栈兼容 | 未完成，不把官方示例当模型配置/硬件验证 |
| 总体执行决定 | 停止本候选自动推进，不写启用矩阵，不安装或运行模型 |

## 固定审查版本

通过GitHub只读连接器读取官方release API，报告v0.32.0为latest稳定release，发布时间2026-10-18T06:50:48Z；将tag解析为commit **5df63a7203cdb9328d824a27b682e77c7b9928be**后全部源码读取固定到该commit。递归tree返回truncated=false。此前搜索命中v0.28.0已解析，但本轮实质审查使用0.32.0，不能用旧版缺少功能建立创新。

[22文件来源索引](SPECULATIVE_SOURCE_INDEX_20261029.json)登记路径、Git blob SHA-1及固定URL。仅功能Markdown通读；代码按相关符号/段落审查，不声称22文件全部语义审计或全仓不存在其他功能。未克隆/执行代码，未将作者源码保存进本地项目，服务器环境未更新。

## 关键源码事实

| 能力 | 固定源码位置 | 实际观察及边界 |
| --- | --- | --- |
| 按批大小动态K | [speculative.py:491](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/speculative.py#L491)、[scheduler.py:1485](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/core/sched/scheduler.py#L1485)、[output.py:307](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/core/sched/output.py#L307) | 查询批中请求数，产出一个step级K标量；官方说明允许K=0。它不是按租户或接受率分组的独立请求K API。动态SD文档有方法/runner/DP限制，不能无条件推广到所有模式。 |
| 自适应验证预算 | [adaptive_verification.py:282](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/adaptive_verification.py#L282)、[同文件:392](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/adaptive_verification.py#L392) | 结合draft/verify成本表与接受概率选择全局draft验证预算，再按请求/位置生存概率竞争分配，可让不同请求保留不同长度。已覆盖接受率感知的共享验证预算，不能另称新算法。目标是预期接受tokens/成本，没有在所审函数中实施租户份额或deadline保证。 |
| 在线接受概率校准 | [acceptance_estimator.py:313](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/acceptance_estimator.py#L313)、[speculator.py:489](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/speculator.py#L489) | 从draft logits预测每位置接受概率，借验证结果持续校准；不是只依赖全服务平均接受率。未验证预测误差或对分布变化的鲁棒性。 |
| 实际runner接入 | [gpu/model_runner.py:1317](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py#L1317)、[同文件:1411](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py#L1411) | 存在预算选择、批压缩和GPU端重分配调用，非仅README提案。后端/Full CUDA Graph/LoRA/PP等限制见官方功能说明；这不代表在现有两张4090或既有环境实测可用。 |
| 每请求接受率/逐步数组 | [observability.py:50](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/observability.py#L50)、[stats.py:350](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/metrics/stats.py#L350)、[scheduler.py:2136](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/core/sched/scheduler.py#L2136) | summary/detailed可报告请求统计；detailed包含每步proposed/accepted数组。默认none；响应只支持单序列n=1，stream需最终usage chunk。schema为实验接口，必须固定版本。 |
| 请求身份与调度 | [chat protocol.py:269](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/openai/chat_completion/protocol.py#L269)、[同文件:388](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/openai/chat_completion/protocol.py#L388)、[scheduler config.py:159](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/scheduler.py#L159) | chat的user字段明确忽略；有request_id和priority，内置策略fcfs/priority，可指定自定义scheduler类。这些不自动构成可信租户身份、token配额或VTC公平保证。受控harness可映射身份，但未实现。 |

对应官方文档：[动态SD](https://docs.vllm.ai/en/v0.32.0/features/speculative_decoding/dynamic_speculative_decoding/)、[自适应验证](https://docs.vllm.ai/en/v0.32.0/features/speculative_decoding/adaptive_verification/)、[接受率统计](https://docs.vllm.ai/en/v0.32.0/features/speculative_decoding/acceptance_metrics/)。所审SamplingParams/chat请求schema未发现直接为一个活动请求设置draft K或“关闭其drafter”的内置字段；extra_args/自定义scheduler允许扩展，不能据此声称实现不可能或必须重写引擎。

**不要把三种控制混为一谈**：按批大小降低K、自适应减少实际验证槽、完全停止某请求的draft生成。自适应预算为0不证明draft成本为0：其成本目标仍包含draft_cost，runner中propose与验证裁剪为不同路径（[gpu/model_runner.py:2225](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py#L2225)）。本轮没有测试每种模式下的零预算行为。

**接受率可观测不等于GPU成本已归因**。请求数组是proposal/acceptance记账，不提供每个被裁剪后验证槽的独占GPU时间。自适应裁剪、grammar失效、异步和graph padding都会影响实际执行口径；要对齐有效GPU长度、真实批组成、同步边界和时间后再讨论成本，不据静态接口报告计数漏洞。客户端stream chunk一次可包含多个token，chunk间隔也不能直接等于每个token的生成延迟。官方per-request timing的TTFT从scheduled起算，端到端客户端TTFT还包含排队/传输，两者必须分别定义。

## 直接文献补审及强基线边界

| 来源、版本与阅读范围 | 对本问题的覆盖和未解决部分 |
| --- | --- |
| [LAPS-SD，IJCAI2025正式入口](https://ijcai.org/proceedings/2025/951)，自动抽取全文相关§2–5；交叉核对[2505.17074v1](https://arxiv.org/html/2505.17074v1) | 结合长度和接受率估执行时间，已按包含draft/verify的已获服务时间调度。正式页自动抽取可能丢公式；§3为batch=1建模，目标平均请求延迟，不直接等同连续批处理租户尾延迟保证。此前PDF失败的阅读缺口已由官方全文/作者预印本补上。 |
| [SPECTRE，2605.08151v1](https://arxiv.org/html/2605.08151v1)，§3.2/§4.4/附录A相关段 | 已处理共享draft服务流量，周期安排普通请求防饥饿；已有一token回退和远端超时熔断。是远端draft/target部署，不等同同一target批的接受率攻击；不能声称投机中的跨流量干扰/公平完全未被研究。页面v1元信息与正文展示日期不一致，本报告按arXiv版本标识引用，不推定额外修订。 |
| [FairBatching，2510.14392v1](https://arxiv.org/html/2510.14392v1)，§3.1–3.4/§4及相关段 | 按请求SLO slack和成本选择批容量与成员，已有预算/尾延迟联合机制；prefill/decode资源公平不是租户身份公平。没有因此证明其投机适配已解决本问题。 |
| [Kairos，2605.02329v1](https://arxiv.org/html/2605.02329v1)，§3相关段 | 用耗时profile及TPOT slack安排批处理，泛SLO感知调度已有；需适配可变验证长度，不能照搬普通一步一token模型后宣布保证仍成立。 |
| [VTC，OSDI2024](https://www.usenix.org/system/files/osdi24-sheng.pdf)，本轮复核§3.1/§4.2相关段 | 自定义服务成本已存在。h(np,nq)与含接受率轨迹/实际执行的状态不同；扩展计数后仍须说明服务定义和界限，不能直接继承原证明，也不能称改计数是新框架。 |
| [FairInference，2609.18112v1](https://arxiv.org/html/2609.18112v1)，承接前轮§4.1/5.4–5.7/6/9阅读，本轮复核入口/定义 | 逐token隔离已经是目标，存在decode批耗时与prefill负载等假设。引入投机多token提交和变化批形状须重新核查适用范围；本文没有证明它失败或证明无需适配。 |

Speedbumps仅batch=1的限制仍成立，但不是正面新颖性证据。已有预算优化、成本计量和延迟隔离分属不同目标，并不逻辑推出它们的组合保证；反过来，也不能把尚未做组合评估直接称为新的安全漏洞。

## 为什么停止本轮推进

本次最重要的修订是补入**当前实际发布的自适应验证**作为强基线，而非再设计一个接受率预算算法。基础观测有现成入口，故不是工程上完全做不了；但当前未形成超出直接适配的机制性差异，且尚未固定可运行Full Attention模型/后端组合、逐请求完整回退对照和有效执行成本口径。按前轮门槛，不转入模型筛查。

对所有机制都简单加租户权重/低接受率阈值，只能先算工程基线。若以后重新提出此题，须具体指出在现有adaptive verification、逐请求回退与VTC/deadline适配后仍存在什么可证伪失败，以及怎样公平计量回退代价；不能以默认未开启优化、user字段未实现身份或只看全局指标造一个弱基线。

本候选的单次审查队列到此结束，没有自动下一实验，也不立即换名制造新候选。已有KV平台与A搁置/旧guard失败保持；四方向目录不变。此报告不评价整个资源隔离方向已无课题。

## 执行记录

0新主/工程输出、0新实验run；无权重/数据/依赖/服务操作、无GPU或模型进程探测，历史78run2702不重算。22官方文件只读获取及定向审查，未运行作者测试。两次批量网页读取发生连接错误，后续单独重试官方页面成功；不计模型/实验失败。文献正文数字均为作者报告，未复现。

仅更新本方向文档并同步服务器，采用旧SHA保护；GitHub连接器仅读公开作者资料，不等于项目文档已提交。项目远端未配置，本轮无push。

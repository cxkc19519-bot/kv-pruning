# 控制器成本表与正常负载敏感域审查

执行更新（2026-10-30）：[默认图尺寸验证已完成](runs/20261030-controller-profile-validation.md)，两工程回答/64tokens、110原始profile样本、N1直接采样及native曲线/整表exact复算通过。实际最终图[1,2,4,5,8,10]，verify1–5不再全平台；draft N1/N2小差在波动范围内，不作性能结论。旧397特征代入新表的N1后验重放仍全部选4，不是本轮引擎真实预算。当前固定配置筛查结束，暂无本候选新GPU队列。以下为此前离线审查快照，其中默认图/runner“未执行/未实现”以新运行记录为准，不重复方案。

日期：2026-10-30，Asia/Singapore。接续[自然历史筛查](runs/20261030-controller-natural-history.md)，本轮只读源码、公开文献及已有结果，执行一次服务器标准库 CPU 审计；没有导入 vLLM/torch、加载模型、查询 GPU 或产生回答。

## 判断

上轮六探针预算与输出相同的记录成立，但成本平台受到我方沿用的工程配置限制。不能据此推出单请求天然不敏感，更不能推出共享历史已构成攻击。先修复测量覆盖与原始证据，再决定是否值得做新的历史影响筛查。当前没有通过门槛的论文主张。

| 问题 | 已确认的证据 | 结论边界 |
| --- | --- | --- |
| 为什么验证预算1–5同价？ | 指定 capture `[5,10]`；native table 将未直接测量的小 token 数向上映射到首个图桶5 | 是本配置的成本构造，不能外推默认配置 |
| 为什么 draft N1/N2完全同价？ | 原全部9个 profile 点均为2个 dummy 请求；draft 曲线仅收 FULL 图样本，只有 N2 键 | N1由N2补表，未独立实测N1代价 |
| profiling 是8192上下文吗？ | 请求8192，但 max_model_len512；图的 promised query5 将实际 context 截至507 | 原正常回答 prompt+output 上界仅60–94，与合成 profile 场景不同；未量化偏差 |
| 能复核原计时中位数吗？ | 原结果留有最终成本表，没有逐点 `forward_ms`/`drafter_ms` 数据 | 能解释构造，不能追溯离散度、JIT污染或成本准确性 |
| 开原生计时器包住 generate 就够吗？ | 完整计时事件仅在 `_dummy_run` 结束；真实 `sample_tokens` 不完成对应事件链 | 原生 profile 不是完整请求/验证周期计时 |
| 高熵公开任务能替代真实低 qmax 证据吗？ | 公开熵/平均置信度指标与本模型对的逐位置 draft 最大概率不同 | 尚无匹配正常负载进入决策敏感域的证据 |

## 固定来源与成本构造

审查固定 vLLM 0.32.0 commit `5df63a7203cdb9328d824a27b682e77c7b9928be`，10份安装文件的 Git blob 均匹配官方固定源码；详见[来源索引](CONTROLLER_COST_PROFILE_SOURCE_20261030.json)。不是对当前整个上游版本的全面审计。

[`adaptive_verification.py`](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/adaptive_verification.py) 188–254：每个形状5次测量，按 key 求 median；target 使用所有样本，draft 只使用 FULL 图样本。80–128：先做单调上包络，再在图桶范围向上查桶，尾部插值/外推。最终表是工程估计，不等同每个输入都实测，也不是完整请求延迟。

原 profile 请求 token 数为 `[5,10,15,20,40,80,160,320,512]`；最后一点因 AR 每请求额外槽位，实际510。每点 N2，每次 collection 共45个 dummy step。对应 context 为 `[507,507,504,502,492,472,432,352,257]`。这些是固定源码和配置的独立标量重建，原运行没有归档逐次形状/计时可作运行时交叉核验。形状5分成两请求2/3个 target token，图描述允许最大 query5，实际 seq_len509/510；形状10分成5/5，seq_len512/512。不是“一个8192上下文的真实用户请求”。[`model_runner.py`](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py)、[`input_batch.py`](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/input_batch.py)

固定源码的 balanced 默认候选推导为 `[1,2,4,5,8,10,16]`；在本 max_num_seqs2、decode width5、FULL_DECODE_ONLY 条件下，预计实际 decode 图为 `[1,2,4,5,8,10]`，profile13形状×5=65次；预计新增 N1 直接测量键。**这里只推导配置与覆盖，不预测实测成本必然分离或预算必然改变。** 尚未构造默认配置引擎核验。默认也仍有桶化和单调包络。不得通过挑图尺寸制造 crossover。 [`config/vllm.py`](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/vllm.py)、[`cudagraph_utils.py`](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/cudagraph_utils.py)

## 热身与计时覆盖

初始化源码先执行 kernel warmup，再 capture/profile；StandaloneAR 的 `capture()` 为 pass，target 图与 draft eager 路径应分开报告。源码顺序不能证明所有 lazy/JIT 编译已排除；前轮出现过编译诊断，不能将其解释为持续用户损害，也不能倒推出原成本已准确。仅保存最终表不足以判断五次重复是否稳定。

[`StepTimingCollector`](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/async_utils.py) 的完整 forward_end/drafter_start/drafter_end 链由 `_dummy_run` 调用。真实 execute_model 有 forward_start，但真实 sample_tokens 不完成这条链。dummy profiling 覆盖 target forward 与 draft propose，未覆盖真实 target sampling、observe_verification/refit、record_confidences 发布及调度等。不能通过打开 collect 包住 llm.generate 就声称得到完整真实阶段成本。

官方[功能说明](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/features/speculative_decoding/adaptive_verification.md)和[估计器文章](https://github.com/vllm-project/vllm-project.github.io/blob/main/_posts/2026-10-14-adaptive-verification-online-estimator.md)已经讨论成本、并发和校准随负载改变。发现 profile 简化本身不构成新方法；10-28 warmup/JIT修复先前仅审相关 patch，本轮未升级环境或应用补丁。

## 公开正常负载证据

- [When Does Better Acceptance Pay? v3](https://arxiv.org/html/2610.24993v3) §6.1/附录F：其任务熵来自 target 原始T=1分布、top64下界，并沿轨迹/请求聚合；不是我们固定0.6B draft每位置 qmax。引擎与 drafter 家族也不同，不能转用阈值或推定尾部分布。
- [SpecKV v2](https://arxiv.org/html/2605.02888v2) §4.1–4.2：Llama3.2 1B→3B、RTX3090、HF手写greedy流程，使用每步聚合置信度/熵。[作者仓库](https://github.com/Amorfati123/SpecKV) README与Phase3 notebook已读；notebook读取CSV并计算 mean/min，不提供本模型对有序位置向量和相关结构的证据。没有下载CSV、运行notebook或复现数字，读到的notebook outputs为空。
- [SPEED-Bench 数据卡](https://huggingface.co/datasets/nvidia/SPEED-Bench) 提供任务/熵类别及提示结构，未提供本模型对的逐位置qmax。throughput最短1K输入超出现有512上下文，部分公开行标为placeholder；未下载数据、执行准备或改任务截断。

即使知道 Shannon 熵较高，也不能推出 qmax 低到我们的边界：V=151936，top概率0.5、其余均匀时H=6.65875nats；417个token均匀时H=6.03309nats、qmax≈0.002398。前者熵更高而最大概率大约高208倍。这个数学反例只用于辨析指标，不是模型观察或正常数据支持。

前轮简化等feature/N2/冷系数下 qmax≈0.0024045 的边界仅对其限定切片成立，不能当任意位置向量的必要阈值。已有397个真实向量的复制N2计算也仅为离线反事实，不是实际batch模型实验。正常请求能否进入真正有决策变化且有可用性意义的区域仍未知。

## 已完成与下一步

CPU run：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-cost-profile-audit-v1`，PID745113，0.043秒，16项manifest复核通过且PID退出；旧自然历史v2 manifest不变。新增1run、0主/0工程回答；累计91run2732主要输出，含历次失败/CPU/重复控制，非独立统计样本。原始只服务器，详见[运行记录](runs/20261030-controller-cost-profile-audit.md)。本轮未查询GPU及他人进程，历史资源状态不当作当前测量。

已准备[禁用的两回答测量提案](../configs/controller-profile-validation-proposal-v1.json)，runner尚未实现，也未执行：保留模型/backend/精度/长度/种子，仅移除工程图尺寸覆盖，先验证默认配置推导，再原样留存每个profile形状、上下文、顺序、原始CUDA计时及最终曲线/表。预定最多600秒、2条32token工程回答、0主历史请求；初始化profile最多2块/130样本，异常或漂移即停。两回答与已存探针token必须一致。

后续首先实现透明观测，独立复算中位数及补表，确认N1/N2真有直接采样；原成本表准确性和真实周期成本仍须另证。即使新成本表有区分，也不自动证明历史损害。若新表仍平台、差异处于重复测量离散度内，或真实输入分配仍饱和，按结果停止；不扫图尺寸/模型/提示救回，不直接扩历史/并发矩阵。只有另有固定公开正常负载的决策敏感性及匹配成本预测，才考虑新的配对损害协议。A搁置与旧guard失败保持。

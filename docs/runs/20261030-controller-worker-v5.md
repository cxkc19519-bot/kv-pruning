# 真实worker控制器恢复检查通过

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；服务器原始日志UTC/Unix。
- 授权：本实验会话已有许可，用户本轮“开始下一步”继续固定Triton工程关卡。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-worker-engineering-v3`、同级`20261030-controller-worker-engineering-v4`、`20261030-controller-worker-engineering-v5`。
- 问题：固定配对Full Attention模型在真实MRV2 worker中能否完成空闲控制器快照、原址恢复、跨重估重放和冻结更新。
- 来源：自建工程诊断。v3/v4失败保留，v5通过；新增3run、0主要答案、6工程答案共192tokens。累计88run2702主要输出，工程答案单列。

## 可复现条件

- vLLM0.32.0/固定commit `5df63a7203cdb9328d824a27b682e77c7b9928be`，无上游源码修改、无nano-vllm复制，本方向无Git远端。
- 沿用独立`.venv-controller-history`：Python3.11.13、Torch2.13.0+cu130/CUDA13.0、Transformers5.19.0、Triton3.7.1，197包锁不变，无新增依赖/权重/系统驱动改动。
- target Qwen3-8B b968826d9c46dd6066d109eabc6255188de91218；draft Qwen3-0.6B c1899de289a04d12100db370d81485cdf75e47ca，沿上轮完整文件校验/相同tokenizer。实际64项KV cache规格均FullAttentionSpec，对应两套固定配置36+28层。
- 单卡物理GPU1 RTX4090/SM89、驱动580.178.04；加载前均18MiB/0%，GPU0有他人进程，仅查询未操作。
- BF16/TP1、K4、adaptive verification开启、local argmax reduction关闭、Triton attention、CompilationMode.NONE/FULL_DECODE_ONLY/capture[5,10]；max_model_len512、max_num_seqs2、max_num_batched_tokens512、gpu_memory_utilization0.9，prefix cache及async scheduling关闭。
- 每次最多600秒/6工程回答，supervisor660秒并仅管理该次新建进程组；temperature0/top_p1/seed42/max_tokens32/ignore_eos=true/generation_config=vllm。所有回答按预定固定长度结束，不把finish_reason=length当工程错误或任务能力分数。无安全/正常能力/性能评测数据。
- [v3提案](../../configs/controller-worker-engineering-v3-proposal.json) SHA `70d6e89fdeafd599a042b3c0265d8f3837411319adca1f3b78301b4c1d2d66a6`，执行runner SHA `d0e8d73b116f678b927896fc0435c7e584a7f59d4c4b3d5194836bd80c20611a`，helper SHA `a0ce2f669ea1313f04de99383d01c636900fb54532a0faf6678a933cc3d5e1ba`。
- [v4修正](../../configs/controller-worker-engineering-v4-correction.json) SHA `290344ddf33e96a2e76d1091143819d234fef58fbfb1670ef8463e49244b63c7`，执行runner SHA `56b155599261f6f7dee8a69a3c9a37df56e89d67fbfc00025b69b0de3ba2d7a3`，helper同v3。
- [v5修正](../../configs/controller-worker-engineering-v5-correction.json) SHA `b18fd17b04f5ce2cd653325c2b0d2b9e366aa498b6d113478a249d1d9c001b1d`，执行[runner](../../scripts/controller_worker_engineering.py) SHA `14a8e5961b65413d1ad99de4b63d0ab333b58406dd45a87b57a44376500d5efc`，[helper](../../scripts/controller_worker_state.py) SHA `ae0edd47557034c168aa4287d4ba36e3f112252d008d2ad9388c476ccd52895e`。

v5实际命令（已执行，不在同目录重复运行）：

```bash
CUDA_VISIBLE_DEVICES=1 VLLM_USE_V2_MODEL_RUNNER=1 VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_ALLOW_INSECURE_SERIALIZATION=0 VLLM_NO_USAGE_STATS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONPATH='/home/user/jhk/project/Directional Exploration/kv-pruning/scripts' TRITON_CACHE_DIR='/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-worker-engineering-v5-cache' .venv-controller-history/bin/python scripts/controller_worker_engineering.py --config configs/controller-worker-engineering-v5-correction.json --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-worker-engineering-v5'
```

启动器另将新venv/bin前置PATH；三次完整命令、环境、PID、GPU前测、returncode在`results/20261030-controller-worker-engineering-v{3,4,5}.launch.json`，console为同名前缀`.console.log`。没有启动HTTP推理服务/tmux/定时任务。

## 失败与修正

1. v3 49.454秒、PID700382/EngineCore700707，0回答/0 RPC。Triton通过此前FlashAttention2能力guard，但启动预热自动调用FlashInfer随机采样器；生成的Ninja文件未转义源码路径`Directional Exploration`中的空格，报缺失`/home/user/jhk/project/Directional`。失败build.ninja已服务器归档，SHA `67fe0b22845bb2090c53deb0c12c97df07d7f38b5a58686d4eac857c823a08da`，原自动缓存`/home/user/jhk/.cache/flashinfer/0.7.0.post1/89/cached_ops/sampling`保留，未删除/修改库文件。
2. v4 68.890秒、PID702218/EngineCore702561，0回答/0成功RPC。按官方[VLLM_USE_FLASHINFER_SAMPLER=0](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/envs.py)选择原生采样路径；保持Triton、自适应验证和greedy参数。引擎/图/预热成功后，函数型RPC被默认IPC序列化器拒绝；未开启pickle fallback。
3. v5使用官方[worker_extension_cls](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/worker_base.py)注入`ControllerHistoryWorkerExtension`，以命名`controller_history_control`调用，仅发送字符串/简单参数和小摘要，快照留worker内部；VLLM_ALLOW_INSECURE_SERIALIZATION显式0。未改变attention backend、模型、精度、恢复断言或输出上限。62.240秒、PID704223/EngineCore704575，成功15次RPC和6条工程回答。

三个涉及配置/调用的上游文件（envs.py、worker_base.py、topk_topp_sampler.py）官方固定blob与安装文件另行核对一致，审计保存在v5 `named_rpc_sampler_source_audit.json`。服务器未装rg，一次只读搜索失败后改用Python定向读取，无新实验/重跑。

## 结果与独立复核

- inspect确认MRV2 GPUModelRunner、StandaloneARSpeculator、估计器和adaptive manager存在，64 cache spec全FullAttentionSpec、请求map为空、cost_tables已建立。
- 17个张量/CPU-GPU缓冲被保存：估计器slope/intercepts/features/predictions/info/grad/counts，adaptive confidence/capacity/logits/query位置，两个stale槽各CPU/GPU，以及speculator confidence。另保存phase/refits/frozen、stale_idx/pending_resets/batch_budget/cudagraph_limit、空闲request槽位顺序与cost tables。
- 每次RPC要求frontend无未完成请求、worker两个请求map空；先同步copy stream/events和GPU，restore原址copy并重录已完成copy events，保留地址。它是**空闲控制器状态**检查，不是模型/KV/RNG或整台服务checkpoint。
- 两条32-token暖机后自然phase24/refits0；先编译empty refit并完整恢复phase24共同状态，再**人为设phase95作为工程fixture**。主快照digest `feffd3683a0e31443efef54af47de046bf326697582b70ab0f6aa4ddd06be126`。
- mutation使状态摘要改变；phase95主快照四次恢复摘要和全部地址exact，另一次预热后的phase24恢复也exact。freeze开关实际经过true→restore false；并未逐一故障注入所有标量，不能称穷尽字段/故障覆盖。
- 同一32-token探针跨重估至phase3/refits1；加入不同history后完整恢复，再探针的32个token及学习状态digest完全一致。学习终点digest `938e01e8e9b5fcf38527940bc9744b7916bc4000ed34b9d4da452b41a8eaceb6`，slope0.2298435569、intercepts约[0.342086,-0.209066,0.402304,0.271455]。该变化受人为phase95fixture影响，不是自然历史攻击结果。
- 冻结分支仅禁止训练统计/重估，预测及服务继续；探针后learning digest、phase95/refits0不变，token亦相同。没有声称冻结全部per-request buffer，也没有逐步证明完整异步缓冲轨迹相等。
- 6条均32tokens、192总tokens，标签分别warmup_probe、warmup_history、probe_original、intervening_history、probe_replay、probe_frozen；原始和重放输出“1,2,…,14”在token层完全一致。不是一般生成质量、无偏采样或非投机Full基线一致性测试。
- 独立程序重新解析6行/15RPC，检查长度、四次主快照恢复、地址、refit终点、学习摘要和冻结摘要；`independent_verification.json`通过。原manifest工件逐份SHA核验，后加诊断/closure保留，v1–v4失败不覆盖。
- JIT/加载/capture/同步跟踪全算在工程用时；没有测正常用户延迟、吞吐、损害或新颖性。短单请求、单worker、同步调度不能推广到动态batch/多worker/异步调度。
- 自有PID700382/700707/702218/702561/704223/704575均/proc核验退出，收尾GPU1 18MiB/0%、GPU0 605MiB/2%及他人PID690133未操作。v5日志KV cache约4.45GiB/18,224tokens、capture约0.11GiB，只描述当前配置分配，不当性能结论。

| 工件 | SHA256 |
| --- | --- |
| v3 manifest / closure | `c4ac5fbc6f3755ac7d5baae629bed49b207beafa613dccdda5359f0c7214c16f` / `8192e0ba5b0807c76554d028e652d0f5ceefc4b7665b570c021a9d261195854b` |
| v4 manifest / closure | `841f9aab230d150f63856b1aba096e1260dd970324d122f36dd7e7ca5741c1e7` / `67a77d5f5c76da9c5f3aca2d39015f44c6068f80e0b6e5fee6d452162d6af896` |
| v5 manifest | `c7bfa2d3c18810b2f7f167c713d45644e2022a39511a390db400fbc2fe222340` |
| v5 summary | `ed94a507e47ac585b1d59dd619e598e70454265ef183cfe658e50368e2fa738f` |
| v5 execution snapshot | `f64cda9b79a5635bf82626e65b19fc20178a34c60bfb56fbd7e0402383a75552` |
| v5 engineering answers | `a92d384710d4a45438cd55b76f294489bf14177db6266a92162b102f5c0caaf6` |
| v5 independent verification | `c3463be6b0c439be38d112fe8f6c8ce917009a40a7ce4a547adeed8fdf099e15` |
| v5 closure | `ba5178f2a0178d9de696a2d4d4eaf86ef503c35ea7afd39d8a7f9bd404029a5e` |
| results/20261030-run-index-controller-worker-v5.json | `24e49635b6845bafc7680a0356e020ae9088c78c2779d50d9e29f1266bd4a746` |

## 解释与下一步

直接观察支持本次固定worker配置/空闲控制器恢复可用；**未验证自然请求历史造成预算变化、正常用户成本损害、攻击或新贡献**。历史假设仍待测，旧KV/guard/A决定不变。

准备[禁用自然历史提案](../../configs/controller-natural-history-proposal-v1.json)，SHA `d5dac66847f89c1d7974d7def42a95c5d6b8c824a07137101a5a7101016e72ec`，runner未实现/未执行。两类固定历史各6请求×64tokens，学习/冻结分支及baseline/完整恢复同探针：最多30主要＋2暖机＋2插桩工程回答，共34/1856生成tokens/900秒。所有分支同一真实暖态、保留pending stats/自然phase，禁止再强设95或注入合成标签；若六历史不能自然过refit则报告不足并停，不增量凑结果。

下一条先按固定源码实现有界逐步预算/接受率观测钩子，最多两条32-token探针对比hook off/on的token与学习终点，工程通过才主筛查；全量保存0效应、改善/恶化/失败。参数变而预算不变不等于有意义损害；同步观测有开销，下一小试只判机制，不能据计时宣称延迟攻击。未来性能测试另需无观测热态控制及误差/公平基线。

本轮STATUS/WORKLOG/HANDOFF/PLAN/README/运行清单/审查入口与根ENVIRONMENT更新同步服务器；代码配置文档同步，原始与环境只服务器，GitHub项目仍未配置远端。

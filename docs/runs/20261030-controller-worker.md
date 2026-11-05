# 配对模型准备与真实worker初始化失败

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；原始时间字段为服务器UTC/Unix。
- 授权：专用实验会话既有许可，本轮用户“开始下一步”继续模型准备和有界正确性检查。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-draft-v1`、同级`20261030-controller-worker-engineering-v1`、`20261030-controller-worker-engineering-v2`。
- 问题：固定小草稿模型与目标模型是否tokenizer一致；真实MRV2 worker能否初始化并进行完整控制状态恢复。
- 来源：固定作者实现工程检查，非新方法。draft准备通过；两次worker初始化失败，均0主要答案/0工程答案/0 worker RPC。累计85run2702主要输出，未进入历史影响小试。

## 可复现条件

- 本方向无Git仓库/远端；无nano-vllm复制。vLLM0.32.0固定commit `5df63a7203cdb9328d824a27b682e77c7b9928be`；沿用独立环境197包锁，不重新安装依赖。
- Python3.11.13/Torch2.13.0+cu130/CUDA13.0/Transformers5.19.0/Triton3.7.1；单卡物理GPU1 RTX4090 SM89，驱动580.178.04。两次加载前均GPU1 18MiB/0%、GPU0他人任务约605MiB，未操作他人进程。
- target：Qwen3-8B `b968826d9c46dd6066d109eabc6255188de91218`，36Full配置；draft：Qwen3-0.6B `c1899de289a04d12100db370d81485cdf75e47ca`，28Full配置。未声称64层运行时cache检查通过，因为RPC尚未执行。
- [固定draft文件清单](../../configs/controller-draft-pinned-v1.json) SHA `0b8c7063e4b63d541ff2b1d625349c6d340d1f3f852d8bd1fedfa8a6dfce6617`。官方[模型API](https://huggingface.co/api/models/Qwen/Qwen3-0.6B?blobs=true)当次sha等于固定revision，所用8项文件条目转录到清单；不是原始HTTP响应归档。服务器直读HF Network unreachable、镜像metadata HTTP403，保留失败说明；备用ModelScope运输的全部字节必须匹配官方LFS SHA256/git blob。
- draft [准备脚本](../../scripts/prepare_controller_draft.py) SHA `906549ff2346ec8f2b1d296729c5e6624a6d0f4be63d8e141019824892e7678e`；900秒上限，实际137.375秒，8文件共1,519,193,708bytes，含权重1,503,300,328bytes，只服务器。未加载模型。
- draft权重SHA `f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`；config SHA `660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd`。四份tokenizer文件与target逐字节相同；get_vocab映射、全部special token/id、chat template、8个固定多语言/代码文本、thinking开关两种模板编码全相同。实际tokenizer长度151669，两模型配置vocab_size均151936；不混同两者。
- 无评测数据/安全打分。工程提示为数数/短GCD代码，固定temperature0、seed42、max_tokens32、ignore_eos=true，最多6条工程回答（上限192生成tokens），不以固定长度工程输出评价能力/安全。
- worker统一BF16、TP1、max_model_len512、max_num_seqs2、max_num_batched_tokens512、gpu_memory_utilization0.9、K4、adaptive verification开启、local argmax reduction关闭以保留draft logits、greedy draft、prefix cache关闭、async scheduling关闭、generation_config=vllm。加载/验证每次600秒，supervisor660秒并只管理其新建自有进程组，无后台服务/API端口/tmux。

已执行命令（不能对原结果目录重复执行）：

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv-controller-history/bin/python scripts/prepare_controller_draft.py --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-draft-v1'
```

worker原始命令与环境分别在`results/20261030-controller-worker-engineering-v1.launch.json`、`v2.launch.json`；console是同名前缀`.console.log`。均使用CUDA_VISIBLE_DEVICES=1、VLLM_USE_V2_MODEL_RUNNER=1、HF离线和独立Triton缓存；v2另将新venv/bin加入PATH。v1运行当时源码snapshot，v2命令为：

```bash
.venv-controller-history/bin/python scripts/controller_worker_engineering.py --config configs/controller-worker-engineering-v2.json --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-worker-engineering-v2'
```

## 结果与失败证据

1. **v1，我方配置错误**：15.612秒，PID693490，eager=true使CUDA Graph关闭，而adaptive verification要求FULL类图。配置校验即失败，未加载权重/启动worker RPC。原协议[配置v1](../../configs/controller-worker-engineering-v1.json) SHA `8638964089715db2d580db0cd1e4ec51a4cfa8ffe6f53038df72152f976cfd31`、当时runner SHA `993dd320bbd1c76e8fa0db42c90cf262b29c6067e883eca3fc853c826de55878`均归档。不能称模型/研究假设失败。
2. **v2，实际后端能力不满足**：保留v1失败后，按固定源码validator纠正eager，保持模型/精度/输出上限/恢复断言，用新目录。[配置v2](../../configs/controller-worker-engineering-v2.json) SHA `32365267b1ead6db96c0d947d602642b612beecb8253e0c092e3ecdbf05b60af`；CompilationMode.NONE、FULL_DECODE_ONLY、capture_sizes[5,10]，EngineArgs预验证通过。runner执行snapshot SHA `e01e186ba9fe6a89299addeff7a8338e548f8c37836f5f63ec6a95cd287db9e4`。

v2实际使用MRV2、自动选择FlashAttention2，日志显示两套权重加载（68.67/6.61秒）、模型加载统计16.38GiB（不是整进程峰值）。随后初始化profiling KV cache时失败：`Adaptive verification replays decode cudagraphs whose per-request query lengths vary up to 5, but FlashAttentionBackend allows none.` 总94.104秒，主PID695039、EngineCore695383退出。0生成/0 RPC，因此FullAttentionSpec64层、往返恢复、跨refit重放、冻结对照均**未执行**。脚本实现不能当已验证接口。

源码依据：官方[config/vllm.py](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/vllm.py) blob `f27c8418ab4df614a32affb9b34a30ac6f734604`，安装文件blob一致，3013–3017要求full graphs；[adaptive_verification.py](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/adaptive_verification.py) 478–502另外检查最大query宽度。这是两个不同条件，不能以配置验证代替实际attention后端检查。

本轮遵循v2失败停止，不再进行模型/后端尝试。后续仅只读源码/CPU import：FlashInfer的设备端/CPU query长度不一致支持在所审实现限SM100家族（此机SM89），不是补一个nvcc路径即可解决。新venv确有`site-packages/nvidia/cu13/bin/nvcc`与headers，本轮未修改CUDA_HOME或安装cubin。Triton builder声明AttentionCGSupport.ALWAYS、设备端/CPU query长度不一致支持true；CPU类能力检查exit0，**不代表实际模型kernel/图已通过**。诊断留`backend_readonly_audit.json`、`backend_followup_readonly.json`、`triton_capability_readonly.json`。

- draft PID690691、两个worker主PID及EngineCore /proc均不存在；收尾GPU1 18MiB/0%、GPU0 605MiB/2%，compute PID690133为他人，仅查询。
- 各run原始manifest逐项SHA核验通过，另存closure并哈希console/launch/后加诊断，不覆盖原manifest；失败源码、输入、日志完整保留。

| 工件 | SHA256 |
| --- | --- |
| draft manifest | `668db6f02b7a61ff5fee908c3392dd82bb23fd84775f7fa01dff1c8fe7d00848` |
| draft summary | `de6dba0f36407c76753cd681112fbef3539ae426dce400531e2cd94afaefd958` |
| draft closure | `45b846e61a6dd7fb54a91020914a1e4f987414093f3a8ade31e4a25a804d40a6` |
| worker v1 manifest | `35c86de97787fee788f9495d11c091d4c58b0ab696c2289d84436968c68c9e71` |
| worker v1 summary | `8666b6f7b7b960b8761dd1dbfa34418378c643ebf3eb2b4468701f5abc71b3da` |
| worker v1 closure | `ac2b0e6d320d6b48e78d9725c31a9bc132fa211771175478bfd82a59cd3f458f` |
| worker v2 manifest | `5599495954e176cfabc27662bd18bd6d7fc0bf88d8bdc0e69673eb25e4bd0a44` |
| worker v2 summary | `6da6195be48daa44ca350b71462acd31fb22834901ceeae53ba97678a53507a9` |
| worker v2 closure | `757a11352b2fce80f95b4bc243a293c3c7b6ac531512762fd20a6177356cde8f` |
| 累计results/20261030-run-index-controller-worker.json | `0a349addb86238ee098b1912f26a71f5a2ecd337c738810937316b4e227287c2` |

## 解释与下一步

直接观察：配对权重/分词器准备完成，所用自动后端无法初始化自适应验证。未知：完整worker恢复、自然请求影响、正常用户效率损害、创新性。此失败不否定共享历史假设，也不构成新漏洞。

[可信worker状态代码](../../scripts/controller_worker_state.py)保存估计器、adaptive GPU/CPU双缓冲/相位/待重置列表/cost/batch metadata和空闲槽位顺序；要求frontend无未完成请求、worker两个请求映射为空并同步copy stream/events。快照留worker、只返回小摘要，原址copy后重建已完成事件；尚未在真实worker调用。代码mutation fixture未逐一改变全部标量，不能把“全字段覆盖”的计划措辞当实测覆盖。

已准备[禁用v3提案](../../configs/controller-worker-engineering-v3-proposal.json)，SHA `70d6e89fdeafd599a042b3c0265d8f3837411319adca1f3b78301b4c1d2d66a6`：只显式指定TRITON_ATTN，保持v2其他条件与6答案/600秒界限；当前未执行，不能直接宣称兼容。最新runner仅新增attention_config传递，v1/v2执行源码snapshot不覆盖。下一条先核对源码/模型/提案SHA和GPU，验证显式Triton后端能力，再在新v3目录完成同一worker门槛；失败停，不关闭adaptive来冒充成功，也不扫模型/精度/后端矩阵。通过后才制定历史影响配对筛查。

STATUS、WORKLOG、HANDOFF、PLAN、README、运行清单、审查入口及根ENVIRONMENT已更新并同步服务器；模型/原始日志仅服务器。GitHub项目无可核验远端，未同步GitHub。

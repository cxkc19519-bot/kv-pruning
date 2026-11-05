# 自然历史配对筛查：控制器改变，探针预算未改变

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；原始时间为服务器Unix/UTC。
- 授权：用户本轮“开始下一步”，继续本实验会话的有界配对筛查。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-natural-history-v1`及同级`20261030-controller-natural-history-v2`。
- 问题：前序请求全部结束后，固定两类历史是否经共享在线学习状态改变相同正常探针的验证预算。
- 来源：自建机制诊断。v1因我方解析断言失败，0主请求；修正v2完成30主请求（24历史+6探针）、2暖机、2插桩工程回答。两run合计38回答/1984生成tokens，含4暖机/4工程；累计90run、2732主要输出。重复固定请求不当独立统计样本。

## 可复现条件

- 沿worker v5固定环境/模型：独立197包锁，Python3.11.13/Torch2.13.0+cu130/Transformers5.19.0/vLLM0.32.0/Triton3.7.1；作者commit `5df63a7203cdb9328d824a27b682e77c7b9928be`。
- target Qwen3-8B b968826d9c46dd6066d109eabc6255188de91218；draft Qwen3-0.6B c1899de289a04d12100db370d81485cdf75e47ca；相同tokenizer、64 FullAttentionSpec已审。无nano-vllm复制、无权重/依赖/上游源码改动，无Git远端。
- 物理GPU1 RTX4090/SM89、驱动580.178.04，单worker/单请求、同步调度；Triton attention、native sampler、命名worker扩展、pickle fallback关闭，BF16/TP1/K4、FULL_DECODE_ONLY/capture[5,10]，max_model_len512/max_num_seqs2/max_num_batched_tokens512/gpu_memory_utilization0.9。没有实际N=2模型试验。
- [原提案](../../configs/controller-natural-history-proposal-v1.json) SHAd5dac66847f89c1d7974d7def42a95c5d6b8c824a07137101a5a7101016e72ec。历史A为1–60整数列表，B为短GCD函数；每学习/冻结分支同一提示重复6次、每次64tokens。同一1–30整数列表探针32tokens；temperature0/top_p1/seed42/ignore_eos=true/generation_config=vllm。输入≤256tokens；固定长度请求仅为实验负载，不代表真实用户分布/正常质量评分。
- 六条件：baseline、A学习、B学习、A冻结、B冻结、B历史后完整恢复；全部来自同一空闲暖态，完整保留pending统计和自然phase，不仅恢复θ。两条32token暖机后phase24/refits0；只在测量前预编译refit并完整恢复暖态，未沿工程phase95或向主分支注入合成标签。
- 上限每run900秒、30主+2warm+2工程=34回答/1856tokens；每条trace≤512事件、全run≤12000。supervisor960秒且只管理自有新进程组。所有输入、顺序、code/hash和阶段启用快照服务器归档；旧禁用提案是历史输入，不因false而重复运行。
- [worker observer](../../scripts/controller_history_observer.py) SHA `5079c7cd9e81f2980f5cd01654b15532ee935103e821b899667167d2ea912a8c`，基于固定原生get_num_tokens/reallocate_drafts/estimator.step透明封装，每次原方法只调用一次、不改变返回值。预算、实际cap、验证raw sampled/rejected/删失counts/phase均记录；同步CPU观测有开销，不能报告延迟损害。
- [runner](../../scripts/controller_natural_history.py)：v1源码SHA `4adb9d54b26a54220d7f4f6cc0646525d08657d2549112af3488d1a870f590c6`；v2执行SHA `4f1742c0a68de5a1df73fb95b0a968c37b0976d5e40d8be29cd1a5f2d09a2057`。复用已通过helper ae0edd47557034c168aa4287d4ba36e3f112252d008d2ad9388c476ccd52895e，原生三文件blob核验通过。

已执行v2命令（勿原目录重跑）：

```bash
CUDA_VISIBLE_DEVICES=1 VLLM_USE_V2_MODEL_RUNNER=1 VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_ALLOW_INSECURE_SERIALIZATION=0 VLLM_NO_USAGE_STATS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONPATH='/home/user/jhk/project/Directional Exploration/kv-pruning/scripts' TRITON_CACHE_DIR='/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-natural-history-v2-cache' .venv-controller-history/bin/python scripts/controller_natural_history.py --correction configs/controller-natural-history-correction-v2.json --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-natural-history-v2'
```

启动器另将新venv/bin前置PATH；实际launch/console在`results/20261030-controller-natural-history-v{1,2}.{launch.json,console.log}`。无HTTP推理服务/tmux/定时任务。

## 失败、校正与工程门槛

- v1 56.144秒，PID721027/EngineCore721350，2warm+2工程/128tokens后stop，30主请求全部未跑。原解析器误要求trace全部为budget→allocation→verification三元组；原生完整prefill没有draft_tokens，跳过预算/分配但仍调用observe_verification。不是钩子或研究假设失败。
- 留存22事件原trace、失败、源码/manifest；固定model_runner.py 1312–1320、1436–1439、2228–2230解释1个leading prefill verification+7个decode三元组。新解析器后验复核原日志，8step/28admitted/25accepted通过，写parser_failure_diagnosis.json；v1仍标failed，不追改成成功。
- [v2修正提案](../../configs/controller-natural-history-correction-v2.json) SHA `9b30eb8b6d2fb442566dc0bdb6e870f2875b8f75c32ff747977500b1be12dcf6`：仅修正prefill解析/逐步phase检查与指标命名，不改observer、输入/顺序/模型/上限/判据。新目录重做同一钩子门槛，未根据主结果换条件。
- v2 95.302秒、PID724185/EngineCore724527。先2warm，再从同一恢复状态hook off/on各32tokens：输出和全部学习状态digest exact，工程门槛通过后才归档main_execution_snapshot并开启30主请求。34回答/1856tokens恰好，0未完成/未执行条件，无运行错误。

## 结果

两类历史都自然跨一次refit：A有90次验证调用、结束phase14/refits1；B有96次调用、phase20/refits1（共同起点phase24/refits0）。冻结分支训练计数/相位/系数完全保持共同状态，恢复对照回到原学习状态。

| 条件 | 探针前slope | 历史后refits/phase | 最大置信度差（相对baseline） | 探针decode预算 | admitted/accepted | 输出 |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 0.5 | 0/24 | 0 | 7步均4 | 28/25 | 32tokens |
| A学习 | 0.11340979 | 1/14 | 0.53264222 | 7步均4 | 28/25 | 同baseline |
| B学习 | 0.40662524 | 1/20 | 0.04608721 | 7步均4 | 28/25 | 同baseline |
| A冻结 | 0.5 | 0/24 | 0 | 7步均4 | 28/25 | 同baseline |
| B冻结 | 0.5 | 0/24 | 0 | 7步均4 | 28/25 | 同baseline |
| B后完整恢复 | 0.5 | 0/24 | 0 | 7步均4 | 28/25 | 同baseline |

每探针另有1个无draft的prefill验证调用，共8step；35个decode target query位置不含prompt prefill，不能当整请求计算成本。42次探针预算选择不等于42个独立样本。A历史后intercepts约[1.32995,-1.05459,1.37474,1.27068]，B约[0.59565,-0.05963,0.78501,0.51569]；共享状态/预测确受真实历史影响，**本轮没有预算、accepted数或输出损失**。

### 独立复核与成本区间诊断

- [stdlib独立审计](../../scripts/analyze_controller_natural_history.py) SHA `4e7a85fec536962249cb09bf43d4fdc6e17b58dbe4f450641de73a6e5b92465e`，不导入Torch/原生预算代码。31份trace、397个预算决策逐个按保存的CPU cost和survival product重算；428次verification的删失观测counts、phase/refit从共同/前一请求状态独立递推，全部exact。6探针token exact、冻结和完整恢复对照、hook透明性复查通过。
- 保存的native cost表：draft_N1/N2均55.00313568ms；verify[1..5]均16.25702477ms，verify[6..10]均16.31232071ms。**这是本引擎用于决策的profile数据，不是本研究测得的正常用户延迟，也未证明profile准确性。** N1可选0..4draft对应总1..5位置，分母相同；记录中正survival分数增加目标，因此始终选4，解释了本轮分配不敏感。
- [全部真实feature回放](../../scripts/controller_selector_sensitivity.py) SHA `b18d26db8325db83f60c97fd29d54c9e464ebc5f4c2d085bf03220aa51f34dc1`：保留全部397向量、仅36独特向量，不挑样本；feature最小−0.237654，对应draft max-q≥0.440865。用common/A/B三套真实系数重算，N1全4；将同一向量复制成N2的离线counterfactual全8，0决策差异。**没有实际batch2 logits/分配/输出/性能证据。**
- 另一个人为uniform-logit例子可令N2的common/A/B预算为3/8/3，但其feature≈−11.931并未出现在这些自然请求里，不能当正结果救回。
- [简化成本域解析](../../scripts/controller_cost_domain.py) SHA `feaa57e0ed34dc3f10e61533482a22ea6798b5299934cfe85c04958ebfb67db7`，在“两请求完全相同、四位置同feature、冷系数”的proxy下解3/8预算边界：预测p≈0.0386421、feature≈−6.02801、max-q≈0.00240450；实际最小max-q约是其183倍。它不是任意非均匀位置的必要阈值/真实流量频率，只说明不能凭uniform反例立即启动GPU batch2。
- 两轮console有_rejection/_resample/_accumulate/_refit等真实推理JIT警告；再加同步trace开销，本试验用时不作延迟/吞吐结果。未把编译暂停当攻击。

## 工件与收尾

| 工件 | SHA256 |
| --- | --- |
| v1 manifest | `131ca4e6677aebee8cf84f77bbf11504ccdf1c098ca5dcb88ced078e61e49145` |
| v1 closure | `64ed260ae995c3345682615c93b1cac19533c599c88f6700dd878011dca08246` |
| v2 manifest | `f802fb66a3e8f54f666af88bc534249dd4ac493ba80829778835b421ad73f7df` |
| v2 summary | `764c6e3fdfe8f722d62eec31d640046cad62c237af89f91a33cb9ca59f05c46f` |
| v2 answers | `4514367ba33f78574e62b215b550bd7c036cd79df4ca1c2b7d5f933baf69b30a` |
| v2 execution snapshot | `42ec070cdd3a5a12e9647e07ebfd2ae4f502db6234ec82c1ba6a9bda6c27994d` |
| v2 main execution snapshot | `b07842e27311d611a0430d02ec271f478a62a4b85d624140a098dd9ec955f049` |
| engineering gate | `3fa16dbe27e8d8dbd80a7d305c4b13238412ca7a6a83329e5699338931135b6d` |
| independent analysis | `4e6e3277f388992f24273e747c72f640ffcfad1460d68ca1c7add9799d8ed54c` |
| real feature selector replay | `ac21b80389427802aaab1eac8fcb8ebf24f9fbae3d0e12db2e14b53a1aefef37` |
| cost sensitivity domain | `9629c563901ffbe274e0bdde0ed100d9334354ee1ab2623abe9a3ee8ae9be959` |
| v2 closure | `602b723bd642de7ef856dce22f31f240471cf000e84a807cc1455ff18ab85c16` |
| results/20261030-run-index-controller-natural-history.json | `a57ff7b742d63673321a26af9ad16df328e0585a72977e51c48b2212e5442808` |

原manifest逐项核验，失败/修正/trace/输入/source/后验分析均只服务器，额外文件由closure覆盖，不覆盖v1或worker旧manifest。自有进程组721027/724185空，主PID及EngineCore均退出；收尾GPU1 18MiB/0%，GPU0 605MiB/2%他人PID729245仅读未动。无服务/依赖/权重/驱动变化，本地只代码配置文档。

## 解释与决策

**只确认真实历史会改变共享校准状态和预测；没有在这组请求上发现可用性损害。** 当前短单请求/成本平台区间小试结束，不自动扩prompt/seed/历史数量/预算/模型/batch，也不以人为uniform反例宣称漏洞。不能据此证明整个系统对所有负载安全，也不能用这些固定重复请求支撑论文创新。

下一条若继续，只离线审native cost profile的生成/热身可信度与公开正常负载能否覆盖敏感置信度域，给出新的可检验预测与停止标准后再判断是否值得真实batch试验；当前没有新模型执行队列。不能为了出现效应修改本轮cost曲线、挑低置信度样本后称独立确认、或把已有TTA/接受率预算机制另包装为新方法。A搁置/旧guard gate不变。

STATUS、WORKLOG、HANDOFF、PLAN、README、运行清单、审查入口及根ENVIRONMENT已更新同步服务器；项目GitHub无可核验远端，未同步GitHub。

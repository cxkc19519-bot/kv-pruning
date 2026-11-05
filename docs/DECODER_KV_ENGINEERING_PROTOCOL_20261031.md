# H3同前缀真实KV工程协议

2026-10-31。用户本实验会话“开始下一步”授权此工程检查。沿原生CPU冻结的新2工程组，仅使用`decoder_engineering_00/01`；新12开发组0模型调用。旧108向量草案仍禁用，不因工程检查自动启动开发实验。未修改旧QA/Mistral gate/旧HF角色规则，不从nano-vllm复制文件。

## 输入与运行时

Qwen2.5-7B-Instruct固定revision a09a35458c702b33eeacc393d103063234e8bc28，原4权重SHA，沿原6metadata及额外model.safetensors.index.json SHA。既有Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1/safetensors0.6.2/numpy2.1.2，BF16、SDPA、TF32关闭、seed20261030；加载后实际检查28 Full层/GQA4/head128、无滑窗与dtype。只用GPU1固定UUID GPU-4ce22e12-b5c0-e423-06c5-e858bb71daaa，启动前used≤128MiB/util=0，否则停止，不操作其他GPU任务。无安装/下载/新服务。

原生CPU的input/case/schema/独立验收文件逐SHA冻结。每工程组再用真实AutoTokenizer原chat_template复核完整native与native+wrapper，共4编码。只处理原prefix373与query+非gold wrapper suffix24；必须复算相同397个branch IDs，不把Full产生的query/wrapper KV注入裁剪分支。这里观测原始下一token logits与受限分支argmax，不生成完整答案、EOS或自由解码文本。

## 两组各7条归档分布

1. whole：397 token整段Full。
2. full_batch：prefill373后deep clone，再批量处理24后缀。
3. split_full_batch：prefix按128+245切分预填充，再处理24后缀。
4–5. recency：同一373 prefix缓存物理gather至186槽，分别独立clone后批量/逐token处理相同24后缀。
6–7. uniform_random：同预算随机掩码，同样批量/逐token双路径。

固定sink4/recent64共68槽，剩118槽收费；recency选择其余最近，随机从其余位置用Python Random(seed2026103101).sample，不按gold或logits择mask。六seed2026103101–2026103106在本登记先冻结，本工程只用首seed，其余是未来诊断候选而非本轮已测。当前两种掩码各层/head共用相同原位置；不是旧per-head随机方法或SnapKV复现。Snap前缀选择器与score-hook正确性尚未接入此新入口，未来8候选前须另验；不能借本工程声称所有选择器通过。

每次suffix clone不与reference共享存储；实际gather值逐tensor相等。缓存原始K/V已有RoPE保持，`position_ids`从原373起；`cache_position`从物理373（Full）或186（裁剪）起，mask实际长度对应物理缓存，逐token递增。批量/逐token路径都保留prefix每个值。reference全过程前后SHA相同。实际每层K/V形状[1,4,slots,128]/BF16，整prefix21389312bytes、半prefix10665984bytes；不能由此推整进程VRAM减半，工程保留Full reference作审计。

## 输出前冻结的数值门槛

两组各比较whole↔full_batch、whole↔split_full_batch、recency batch↔tokenwise、random batch↔tokenwise，合计8对。要求每对全152064维logits有限、max absolute error≤0.25、全词表KL≤0.001、合法{32,33,34,35}条件KL≤0.001，并且全词表/合法token的**全部并列argmax集合**相同。KL计算float64。此为新入口的数值工程标准，允许BF16批处理差异；不修改历史逐token等价关卡，也不是研究效应/安全认证。

任何门槛失败保留全部已生成工件并停止，不扫精度/后端/阈值救回。工程组gold只保存在既有来源，本轮不以工程答对与否调整任务；不把两组Full正确当12开发组支持证据。

## 独立复核与资源

原始Full prefix和两种物理gather的BF16字节、14条float32分布、每次forward输入ID/逻辑位置/物理位置/mask/cache大小及runtime/source/input/weights摘要只归档服务器。独立validator仅标准库，无Torch/NumPy/项目模块：从原始BF16逐head/原位置重建所有gather字节，重算shape/layout/bytes及reference hash；从二进制float32重算全部KL/argmax/门槛；核112次forward/2574 teacher-forced输入token、4编码和0开发调用，并重新hash4权重/7metadata。clone不共享指针的现场观测由worker断言，独立validator不冒称可从离线字节证明CUDA指针关系。

唯一新run `results/20261031-decoder-kv-engineering-v1`，新登记`configs/decoder-kv-engineering-v1.json`须传自身SHA。源码/协议/输入在任何模型输出前固定并同步。最多112 forward、2574输入token、14条归档分布；中间forward虽计算末token logits，不作为独立样本或额外模型答案；0生成token。worker600秒，validator180秒，outer850秒，TERM自身进程组/5秒后KILL；≤64文件/128MiB。同步运行，无后台队列。模型load/文件hash/编码时间含worker上限。

Python audit拒绝外联、子进程、run外写入与非白名单模型文件读取，worker允许固定HF/Torch，validator禁止重型库。已知urllib3 2.3.0 `_has_ipv6`的精确固定源码/`socket.bind(('::1',0))`探测仅作为拒绝的本地能力probe单列（raise OSError，未实际bind），不放行任何网络；Python audit不覆盖全部CUDA/Rust原生文件IO，不称OS沙箱。父launcher的GPU只读查询及两个受限子进程是登记控制流程。

通过后只表示新入口这两组上的Full、clone、物理gather与位置/数值路径通过。H3目标失配、Full12能力、新算法与论文贡献尚未验证；下一步补Snap选择器工程及固定12组Full支持≥10/12，之后才另冻有界8候选配对筛查，所有输/平/赢与无信号停止线不改。

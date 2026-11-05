# 同前缀数值审阅结论与比较合同边界

日期2026-10-31。仅分析工程第一组的既有7分布/56 trace与已安装Transformers4.57.1源码，不追加模型/分词/权重/GPU。原工程v1/v2仍失败，H3与12DEV Full支持未测试。

## 已查明的事实

在记录的CUDA、非tracing、all-ones padding、DynamicLayer条件下，精确安装源码的shape标量重放显示：

| 调用 | 传入SDPA的mask | GQA处理 | is_causal |
| --- | --- | --- | --- |
| whole397 / prefix373 / split第一段128 | None | enable_gqa=true，4个KV头 | true |
| Full suffix24 / split第二段245及后缀 / 两裁剪batch24 | 显式4D | repeat_kv至28头，未启用GQA参数 | false，因果关系由mask表示 |
| 两裁剪逐token后缀 | None | enable_gqa=true，4个KV头 | false，单query只见已有键 |

56调用中51为None mask/原生GQA，5为显式mask/展开KV头，3为is_causal=true。此为**源码分支推导**，不是实际CUDA kernel记录；旧run没有保存最终4D mask/GQA参数或profiler事件，不能断言Flash/math后端切换已被现场观测。

原Qwen2Model把position_ids用于RoPE，物理cache_position用于构造mask；DynamicLayer顺序追加并按实际长度报告mask size。依精确causal predicate kv_idx<=q_idx，逐1287输入query行检查，在保存的参数和源码语义上，两裁剪路径都映射到同一保留prefix原位置+已见suffix集合，未发现明显位置/可见集合错配。**它不能排除未归档的实际张量mask或内核错误**。4份完整运行时源码/原函数提取与重放结果均保存在新服务器归档。

## 误差的量级

以下为同一个KV候选的不同执行路径；没有比较不同候选的H3排序。所有原logits确实落在BF16数值网格上，这不证明误差全部来自BF16。

| 路径对 | global TV | 合法四token TV | global KL | 合法KL |
| --- | ---: | ---: | ---: | ---: |
| whole / full batch | 3.64e-12 | 3.60e-12 | 7.08e-13 | 7.03e-13 |
| whole / split full | 4.81e-12 | 4.69e-12 | 1.25e-12 | 1.23e-12 |
| recency batch / tokenwise | 0.01672999 | 0.0004256675 | 0.0025013213 | 0.0000262600 |
| random batch / tokenwise | 1.46e-10 | 1.06e-10 | 2.74e-11 | 2.43e-11 |

TV定义为概率绝对差之和的一半，recency全词表约1.673%、合法集合约0.04257%；它与“误差词项原本合计约4%质量”是不同指标。其最大单token概率变化约0.0116973，全词表top概率约0.796907/0.789700；这不是只有低概率尾部的差异。Full/random虽然原始logit max超限，分布变化极小。softmax不变于共同logit偏移，但去除概率加权偏移后的max仍可较大，不应据此改判原门槛。

4对×2 scope的argmax均相同，概率margin均满足m>2||p-q||∞的充分稳定条件；这只描述当前已看过的8个比较，不是未见组的保证，更不证明KL排序稳定。独立validator用另一概率归一化公式重算8 scope、合法KL以Decimal60位交叉核验。

[PyTorch2.5.1数值说明](https://raw.githubusercontent.com/pytorch/pytorch/v2.5.1/docs/source/notes/numerical_accuracy.rst)明确数学等价的batch/slice计算未必逐bit一致；[同版本SDPA说明](https://raw.githubusercontent.com/pytorch/pytorch/v2.5.1/torch/nn/functional.py)指出后端选择会影响数值，math对half/BF16中间运算使用float。两份原文已固定抓取SHA。它们支持“执行路径是合理原因候选”，不能证明本例全部差异的因果来源，或为任意0.25/0.001超限背书。线性层GEMM形状变化、BF16累积/舍入及未记录的SDPA后端仍无法从当前工件单独区分。

## 下一阶段的比较合同要求

1. 先明确研究对象是固定生产式推理路径上的行为，还是对数学精确Transformer的逼近；两种主张需要不同证据。Full与裁剪使用相同query/wrapper IDs、同一预定suffix执行方式，不能按结果挑batch或tokenwise。
2. 添加不改变张量/参数的观测：传入SDPA的实际mask维度/类型、Q/K/V shape、enable_gqa/is_causal及kernel事件；旧trace只有外部请求。先用CPU stub核传参和恢复透明性，再另冻只含原2工程组的有界记录协议。**不把本次分支推导当现场后端测量。**
3. 若以后要求固定mask/GQA/SDPA后端，须作为新的明确数值参考实现，先解释对数学语义与成本的影响；不能声称仅凭切换配置就“修复”旧失败，也不能扫后端直到通过。本轮不选新后端或更宽阈值。
4. 数值容差应对应分布、合法决策及实际目标分数的重复性。原max-logit≤0.25/global&allowed KL≤0.001门槛继续false，不追改。不把这一工程例的最大差当所有新组/候选的误差上界。
5. 对候选排序要直接测目标J在预定重复路径上的变化；KL不是距离，不能套三角不等式把当前KL(P_path||Q_path)变成KL(Full||candidate)的分数误差上界。若报告“观察范围内排序不确定”，须区别于置信区间或认证。固定Full分布P时，分数差恰为sum_i P_i log(Q2_i/Q1_i)，但这并不能从现有单组给出通用常数。
6. 原12DEV不执行、不调题/seed/预算；Snap选择器工程仍待验证。现场记录与数值参考合同成立后，才能讨论工程重验、Full12支持与8候选筛查。没有由这轮计算建立新方法、新颖性或方向no-go。

## 执行与归档状态

[执行记录](runs/20261031-decoder-numerics-audit.md)/[readiness](DECODER_NUMERICS_READINESS_20261031.json)：计算worker和独立validator各exit0，但父launcher归档检查发现44文件>预注册40（4841616bytes<8MiB），最终exit1。原launcher_summary在检查前已写complete，不能据此忽略退出失败；新增closure明确overall failed_archive_file_count_cap_analysis_independently_verified，原manifest不追改，上限不更改、不复跑。

追加closure/derived后46文件4846935bytes，原manifest `a0dec76b627291963f2f0880d2698f37cfcefcbc995255322f849f46b2c4057e`，derived `75f431abb9ae396879950d7438f917a4d7743de4a529c54bafb36d73f1135876`；全部原文件与新来源逐SHA保留。此次独立计算证据仍可审阅，但不称整个注册run已验收通过。新增1个CPU run（归档资源检查失败），累计125run3038主。无新增模型/GPU/分词/权重动作，原工程结果与旧关卡保持。


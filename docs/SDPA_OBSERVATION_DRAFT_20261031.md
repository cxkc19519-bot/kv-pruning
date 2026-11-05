# 两工程组SDPA现场观测草案

2026-10-31。状态：**禁用、GPU worker/validator未实现、未执行**。[CPU记录器验收](SDPA_OBSERVER_READINESS_20261031.json)只证明stub合同，不能当真实Torch/profiler通过。[配置](../configs/sdpa-observation-draft-v1.json)冻结具体工作量，不是可运行命令或实验启动许可；授权仍来自用户实验会话指令。

## 唯一问题

先确认实际SDPA的mask是否None、Q/K/V形状、enable_gqa/is_causal，以及在marker显式父链下出现的backend operator与kernel原名，检验上一轮源码分支推导。不是切后端找更小误差、重做KV损害曲线或验证H3候选排序。只用原新2工程组，12DEV模型调用0。

沿固定Qwen2.5-7B/BF16/SDPA/TF32 off与seed20261030，4权重/7metadata/package版本须在新GPU登记重核；用原2工程组prefix373/suffix24、半预算186/sink4/recent64，recency与固定seed2026103101随机掩码，query+wrapper必须在每个分支重新处理，不能注入Full后缀KV。旧工程两run、原0.25/0.001 failed gate完全保持，观测完成不能晋升数值gate。

## 每组7条观测/负对照

| 路径 | SDPA记录+profiler | 用途 |
| --- | --- | --- |
| Full suffix batch plain | 关 | 透明性基线 |
| Full suffix batch observed | 开 | 与plain逐元素float32 logits完全相等、reference不变 |
| recency suffix batch plain | 关 | 透明性基线 |
| recency suffix batch observed | 开 | 与plain完全相等并记录参数/内核 |
| recency suffix tokenwise observed | 开 | 记录逐token路径 |
| random suffix batch observed | 开 | 记录另一个固定掩码 |
| random suffix tokenwise observed | 开 | 记录另一路径 |

两组共14归档末token分布；每组1次prefix加53次后缀forward，共108 forward/1082 teacher-forced输入token，0生成/完整答案。只有observed五条路径进入patch和profiler，每组51 forward×28层，两组共2856 SDPA事件；记录cap4096，不能代替108 forward调度上限。一个observer实例贯穿observed scope，call counter不重置，marker唯一。

记录器不读Tensor值、不clone/替换SDPA参数，不调用后端选择上下文；marker只是record_function。可通过observer.sink保留元数据，再在profile结束后读未聚合events，按显式cpu_parent归属kernel。无父链事件保留unassigned，不依据时间猜测。真实mask值本模块不采集，不能声称可见集合已经通过现场tensor验证。不能把profiler插桩称性能无开销；plain/observed同路径负对照用于发现插桩数值影响。

每组两个plain/observed控制要求logits tensor逐元素相等、reference hash一致且退出后原callable恢复；不以相同argmax/更宽tol替代。任何observer metadata/sink/marker错误、日志cap超限、恢复冲突、marker覆盖或父链/kernel证据不足都报告失败/未知，停止后续组；若profiling不支持，保持阻塞，不静默关闭profiler或切库/精度。保留原backend/operator/kernel原名，不能仅凭Python参数就宣称Flash/math已测。

## 执行前缺口

GPU入口与独立validator尚未实现。须另冻exact source/input/runtime SHA、当前GPU1空闲与包版本/权重、原生2输入HF再编码、profiling可用性、trace字段与独立重算规范；嵌套临时文件固定在run内，使用本次递归checked finalizer，先审cap后写complete，旧file-cap失败不追改。拟定worker600/verifier180/outer850秒、≤128文件/256MiB（包括raw profiler trace与全部快照），超限完整保留并failed，不自动调上限重跑。

新观测阶段若完成，只能说明记录到了真实参数/内核且通过同路径透明性控制；旧跨路径数值误差仍需解释，Snap selector仍待工程验证，Full12支持和H3均未测。没有自动12DEV队列，也没有从本草案启用第三次GPU。

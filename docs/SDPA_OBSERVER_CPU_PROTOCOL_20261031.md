# SDPA透明记录器与归档故障CPU验收

2026-10-31，授权实验会话用户“开始下一步”。本次只实现和验CPU软件，随后冻结禁用的2工程组现场观测草案。0Torch/Transformers/tokenizer/NumPy导入，0模型/权重/GPU/网络；所有stub dtype/device与profiler kernel名称都是构造值，不冒充现场观测。

## 记录器合同

`sdpa_observer.py`注入给定namespace的SDPA callable，原封不动转交`*args/**kwargs`（不补默认参数到原调用、不读张量值），只记录shape/stride/dtype/device及原参数存在性/顺序。SDPA的返回对象/原异常对象identity保持；异常trace会多一层wrapper，不声称trace文本相同。marker/sink/普通metadata错误单列不取代原调用结果；这些错误不允许未来观测验收通过。原模型异常包括BaseException仍重抛；marker不得吞掉它。

退出恢复原callable；嵌套同target拒绝；若其他代码替换target，记录冲突且不覆盖外来owner，正常body退出时抛恢复冲突。只支持单worker、eager、无并发调用/compile/graph；不声称性能透明或GPU数值透明已验。record budget溢出仍执行一次原call，停止追加记录并报错；未来GPU dispatcher须自身严格限制forward数，不能把日志cap当模型调用cap。

profiler inventory接受已供应的FunctionEvent-like对象，通过显式cpu_parent链归属marker；保留backend operator原名与kernel名/owner，不靠时间重叠猜测，不汇总可能重复的duration。孤立事件保持unassigned，循环/过深父链拒绝。已只读核对安装Torch2.5.1的FunctionEvent.cpu_parent/kernels/Kernel.name/device与profiler.events API源码，尚未运行真profiler。

## 固定24用例

O01位置默认参数、O02全keyword/显式mask/scale、O03六位置参数/GQA、O04原RuntimeError、O05原KeyboardInterrupt、O06 sink失败、O07 marker进入失败、O08 marker退出失败、O09原异常与marker异常同时出现、O10嵌套拒绝、O11外来owner冲突、O12 metadata属性失败、O13无marker/sink且毒化tensor-value API、O14记录cap2/原call3次、O15同instance顺序重入与唯一标记、O16重复参数交由原callable抛TypeError、O17合成profiler显式父链归属/孤立kernel、O18父链循环拒绝。所有TensorStub的cpu/clone/detach/numpy/to/float/item/iter/bool均禁止，未执行任何tensor算子。

A01准确文件数边界，A02文件数超限，A03字节超限，A04保留已有worker失败，A05嵌套文件计数，A06拒绝覆盖已有summary/manifest。`checked_archive.py`在写最终summary前计入summary/manifest自身字节与文件数，超限输出failed而不是先写complete再抛错；原始payload不删除。测试的故意故障不是当前run失败。独立validator不导入被测模块，逐24结果/状态、所有子归档的文件数/byte/hash重算；Python对象identity由worker现场断言，独立序列化审计不能事后证明对象指针关系。

## 冻结执行

新run仅服务器`results/20261031-sdpa-observer-cpu-v1`，六source与旧CPU审阅配置SHA先冻结、CAS同步及静态compile后执行。worker/validator各60秒，outer150秒（含TERM后5秒KILL自有进程组）；归档上限64文件/4MiB，含所有递归子fixture及最终summary/manifest。外层使用本轮checked finalizer；worker_manifest同样递归，旧超限run/source不追改、不复跑。父仅创建两个受限Python子进程，不联网或GPU查询。

通过只支持这24组stub/fault合同，原数值工程仍failed，不能借CPU传参identity推出CUDA数值不变或后端已观测。下一交付为禁用观测草案：实际GPU入口/兼容性/权重与版本pin须另冻，采用原两工程组，带同路径无记录负对照；0开发组，0新后端或阈值选择，不恢复12DEV队列。

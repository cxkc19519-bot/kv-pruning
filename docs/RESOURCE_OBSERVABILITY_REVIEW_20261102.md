# 资源可观测性审阅与自然执行小筛查协议

日期2026-11-02；用户“开始下一步”。本轮完成只读来源/环境预检、既有真实事件离线重算与独立验收，**0次新后端执行、0个新实验run**，累计147runs3038历史主回答不变。下一阶段[协议](../configs/resource-observability-natural-draft-v1.json)执行关闭、runner未实现，尚无资源/取消实验队列。

## 当前结论

已测小型schema调用的时间尺度低于旧外部采样分辨率，不能拿这些外部样本分摊单调用CPU/RSS，也未测过原池槽恢复。科学强对照仍不就绪：Rust/C取消能力已经存在，当前Python环境和构建工具不能直接代表它。仅凭旧版API缺失或调用方返回不能立题。

## 实际重算

输入为results/20261102-typed-object-semantic-v1的封存事件与/proc快照，原manifest494acca2…不改。独立stdlib脚本[verify_resource_observability_review.py](../scripts/verify_resource_observability_review.py)从原始事件再次重建694个选定调用跨度、250外部样本，并核官方6文件Git blob。

| 旧真实阶段 | 次数 | 最短/中位/最长（微秒） |
| --- | --- | --- |
| X schema compile | 3 | 314.336 / 424.854 / 449.025 |
| X matcher init | 21 | 12.469 / 14.914 / 33.043 |
| X mask | 323 | 8.775 / 9.479 / 60.768 |
| LL schema convert | 3 | 23.402 / 27.577 / 37.915 |
| LL matcher init | 21 | 100.834 / 129.306 / 267.039 |
| LL mask | 323 | 7.730 / 19.495 / 36.929 |

这些是包含事件记录开销的单次调用wall跨度，不是纯计算CPU或后端性能排行。SC_CLK_TCK=100即10ms/tick，原监督采样名义间隔10ms；694个区间没有任何一个包含两个外部采样点。每调用CPU不可识别，不能填0。process/thread clocks声明分辨率1ns不保证实际测量精度；未测原池、取消后存活或内存归还。

复核命令（实际已执行，无作者库导入）：

```sh
.venv/bin/python -I -S -B scripts/verify_resource_observability_review.py
```

## 强对照兼容性：本轮核对的事实

官方main重新解析为LL commit3d698ee07b3a67b0aef50fb6058612e8fd30aca2、X commitca1acf28bf35b9ba9092800b69aebc7d4ce1f7a7，与此前固定头一致。6份来源均成功获取/核Git blob，未执行作者代码。

- [LL原生取消说明](https://github.com/guidance-ai/llguidance/blob/3d698ee07b3a67b0aef50fb6058612e8fd30aca2/parser/README.md)：Rust opt-in/C handle提供协作取消，依赖调用、tokenizer callback、共享锁等仍有边界；当前源码不保证固定取消期限。
- 当前及最新已审Python stub未声明cancel方法；这只是这些接口文本的结论，不声称全仓不存在替代绑定。
- [X编译器](https://github.com/mlc-ai/xgrammar/blob/ca1acf28bf35b9ba9092800b69aebc7d4ce1f7a7/python/xgrammar/compiler.py)有dynamic compilation，已安装0.2.8无该参数。新[matcher](https://github.com/mlc-ai/xgrammar/blob/ca1acf28bf35b9ba9092800b69aebc7d4ce1f7a7/python/xgrammar/matcher.py)中time_threshold针对draft树遍历，不能泛化成compile/所有mask的取消时限。
- 当前PATH无cargo/rustc；vLLM要求llguidance>=1.7,<1.8和xgrammar==0.2.8。未安装、升级或构建，不在原环境盲升后声称兼容。
- 本次SSH session的cgroup无写权限，memory/pids为max、cpu.max不可写。未尝试改权限或写系统控制项，affinity和RSS观测不等于服务硬额度。

## 已冻结的下一阶段

自然观测校准，不发取消、不强制超时返回、不放大输入。一个真实ThreadPoolExecutor(max_workers=1)贯穿两后端和全部试次；每个backend在宽1/2/4上各执行B0单独基线，再提交A宽N与B宽1。共18 native job，另1个空时钟控制。A开始事件仅通知，不阻塞/人为sleep；B提交时A若已完成，记录“重叠未观察到”，不补跑或加宽救信号。

每job含raw schema解析、compile/conversion、新matcher与first-mask，核根token123被允许；request-local native对象离开body作用域后才记work_end，单列Future/caller接收。同一pool/slot/PID/starttime/native TID必须贯穿，不能换池报恢复。这个probe只完成first-mask，不冒称整条生成或取消后恢复。

计monotonic/process/thread clocks。线程CPU不含其他native helper，进程CPU含controller/观测开销；RSS仅在baseline前/配对完成后读当前值，与高水位/allocator retention分开。外部10ms sampler保留作存活/清理证据。19job/每job提交起5秒/worker135秒/总150秒，亲和性≤2，payload≤16KiB，最多1个同时native工作和2个pending native job，18 compile/18 matcher/18 mask，归档64文件16MiB。身份异常、功能失败、时钟回退、预算超限、清理失败或范围外访问立即停止、留删失/失败；不自动重试。

成功仅证明这套测量入口可用，不建立资源损害、SLO或创新。后续科学配对仍需实际可运行、范围公平的强对照。当前配置execution_enabled=false/runner_implemented=false表示实施后另冻source/input和执行登记，**不撤销本会话已有小规模验证授权，无需重复询问许可**。

## 归档与交接

原始仅服务器：

- literature/20261102-resource-observability-review-v1：17文件341609bytes，manifest635371e581a964d66205548f773f694b9369b7d7834b92c30f6226d475043dd4。
- literature/20261102-resource-observability-verification-v1：独立复核，manifestc0a5fc42c5287ca56d180ed0f5bb5f839b88ad26e8993b1d4fceb97bf5bab1cc。

旧typed correctness和旧45题失败保留；N1资源效果/新颖性仍未知，H3停止/泛KV暂停不变。收尾核验旧索引/运行/源码/运行库及旧4PID，无后台任务。STATUS/WORKLOG/HANDOFF/PLAN/README、协议和readiness同步服务器，GitHub未配置未push。

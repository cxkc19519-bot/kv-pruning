# 启动与请求预算边界审阅：分阶段契约 v1

日期：2026-11-01。承接[精确导入边界验收](runs/20261101-import-boundary.md)。本轮只读旧事件／源码与AST，未重新导入任何后端、提高旧阈值或启动实验。

## 决策

**原组合5秒覆盖冷进程导入，不能作为单次schema编译时限的实测结果。** 原冷启动gate继续false，旧异常／删失和139run索引不改。

新[契约草案](../configs/startup-request-contract-draft-v1.json)把一次性初始化、冷首请求、暖请求分开计时，同时保留全程资源账本。新范围下一次只允许检查库导入；启动单列30秒工程上限、launcher/复核/清理总45秒，未来单请求仍为5秒。这些是事前冻结的新范围工程界限，不是由已有测量证明的服务SLO，也不使旧冷启动检查变成通过。本轮草案执行关闭、runner未实现。

下一条先实现分阶段状态／时钟控制器及8项标准库验收。通过后另登记一个新进程的import-only启动检查；不在本轮跑启动，不重做FF差值，不以元数据扫描为由改上游或预热样本。语义域尚未解决，45标签请求仍禁止准入。

## 1. 旧证据复算：真正测到了什么

来源`results/20261101-import-boundary-native-v2/events.jsonl`和launcher summary，原manifest `a157377160cc84a8ea86455436c02b8e9d77e6236814bdc38166a28e064e918a`逐项核对。

| 已观测阶段 | 原单调时钟复算 | 能支持的结论 |
| --- | --- | --- |
| Torch公开导入 | 3.081376258秒 | 包含该导入的依赖及保护开销 |
| 两项线程设置 | 0.009987521秒 | 已完成，未重置组合时钟 |
| XGrammar开始 | 组合开始后3.091706737秒 | 名义5秒预算只余1.908293263秒 |
| 外部watchdog检测 | 组合开始后5.000740546秒 | 5秒目标被删失；约0.000741秒是轮询检测延迟 |
| 4秒附近栈 | Transformers→importlib.metadata包分发扫描 | 当时所在位置，不能分配全部剩余耗时或证明死锁 |
| schema编译／matcher／mask | 0调用 | 没有5秒schema编译成败样本 |

没有把未观测成本填0，没有估算“完整启动还需多久”，没有做缓存清理或热启动对照。旧实验只证明该配置没有在原冷启动上限内完成；它既不证明请求计算不可控，也不证明编译很快。

## 2. 源码映射：不能漏掉验证和懒初始化

以下是服务器**实际安装**vLLM0.32.0、XGrammar0.2.8、llguidance1.7.6的静态源；没有执行这些函数，不能冒称端到端服务复现。目录均相对既有site-packages。

| 源码位置 | 静态行为 | 新账本归属 |
| --- | --- | --- |
| `vllm/v1/structured_output/__init__.py:50–109` | manager初始化线程池及tokenizer等 | 一次性初始化；若实际在请求路径才发生，则须记入冷首请求 |
| 同文件`:126–187` | 首次需要时构造backend，然后向executor提交grammar创建 | schema-independent factory可显式前置，但实际lazy成本不能消失 |
| 同文件`:189–211` | 根据请求调用backend.compile_grammar | 请求工作，含队列前后的实际等待 |
| `vllm/v1/engine/input_processor.py:157、245`；`sampling_params.py:901–917、1218–1438` | params.verify路由结构化输出验证；显式后端或auto fallback | 验证和所有实际fallback都在同一请求账本中 |
| `backend_xgrammar.py:448–470` | JSON检查、解析并调用Grammar.from_json_schema进行转换 | 请求特定工作，不能在计时前以“验证”为名预先完成 |
| 同文件`:37–84、86–164` | tokenizer info/compiler factory与请求compile_json_schema、GrammarMatcher不同 | factory设置与schema转换／matcher准备分别计费 |
| `backend_guidance.py:164–206、373–386` | tokenizer factory、请求序列化、LLMatcher构造，以及validate_grammar | 后两者是请求特定准备；不能只计mask那一小段 |
| `structured_output/request.py:43–67` | Future就绪检查及结果读取 | 结果可用不自动证明取消后计算／池容量已回收 |

本机结构化验证已在SamplingParams路由；manager注释仍提旧`Processor._validate_structured_output`名称，不能将该注释当作实际调用证据。此次定位了新的实际位置。服务器无rg，首次文本搜索因缺命令失败，随后用标准库完成同范围静态检索；这不是新增实验run。

CPU库级适配器将来不执行完整vLLM InputProcessor／HTTP服务，所以其job时钟只能称库级请求计时；上述映射用于防止漏成本，不意味着已观测生产HTTP TTFT或引擎行为。

## 3. 新范围的两个时钟与三层准入

### 启动时钟与库导入就绪

新启动工程从父进程创建fresh worker前的单调时间开始，包含Python启动、worker pin检查、guard设置、Torch及XGrammar公开导入、线程设置和CUDA未初始化后验。30秒只作为有界工程检查；前置launcher校验另记并受总45秒约束，不从全程账本抹掉。

沿用已通过23项的软件边界、固定设备／命令pin与原环境，不自动禁用设备后端发现、猴子补丁包元数据、导入内部私有捷径或先加载Torch再启动时钟。查询1秒／输出界限和2CPU等原资源约束不变。RSS仍是观测值，当前无可写cgroup硬内存额度，不能声称多租户硬隔离。

完成只产生`library_import_ready`，不构造tokenizer/compiler factory、不喂schema、不编译测试集、不调用mask。检查工件可以证明该代码路径在那次worker中完成；worker退出后不能把该ready状态当作另一进程已经初始化。

### 后端factory与语义域准入

`backend_factory_ready`还要求同一进程内的request-independent tokenizer／compiler创建完成，以及对应语义域／词表契约已验证。仅imports_ready不满足这些条件。原257词表的LL byte255冲突仍成立；未定义新的共同域前不得用45标签继续执行，也不能通过本次预算分离绕过它。

若实际部署仍lazy创建backend，首次请求应包含这笔成本，单列cold-first-request。若显式在启动期前置factory，成本计入startup/factory账本并报告配置差异，不偷偷从两个阶段都扣除。任何schema特定工作都不能当作factory预热。

### 请求时钟

未来库级job在原始schema载荷提交、任何特定schema解析／验证之前启动5秒总时钟，覆盖解析、验证／转换、排队、实际lazy初始化、编译或LLMatcher准备和首次mask。队列转移、fallback和首次mask不能各获得新的5秒。后续mask须有单步watchdog和另行冻结的请求总上限；目前没有定义完整生成／HTTP服务协议。

这也是新范围：旧CPU配置的5秒是每public-call watchdog，旧导入工程另有组合冷启动5秒；二者都不等于已经实现了这里的请求端到端5秒。新契约没有宣称上游默认具有这些deadline。若库级adapter不执行vLLM的某个前置环节，须明确N/A及计时边界，不能据库级结果冒称生产入口全成本。

调用方超时、底层工作停止、原池容量恢复仍分别取证；共享等待者B仍需要的工作不能因A取消而被无条件杀掉。一次性启动、冷首请求和暖请求分别报告，全流程同时报告；不能只选暖请求遮蔽初始化成本，也不能重复累加重叠时间。

## 4. 实施顺序与当前停止边界

1. 实现状态和时钟控制器／独立validator，先做8个标准库合同：启动拒绝schema、启动超时阻止请求、imports-ready不等factory-ready、验证属于请求计时、阶段转移不重置deadline、caller超时不意味着work结束、scope改变失效ready、账本分开启动／冷首／暖请求。新登记、最多30秒、0后端调用，不重复原12observer或23boundary测试；若边界模块变更则23项证明需重验。
2. 通过后另登记一次fresh worker的import-only启动工程，使用新30秒启动范围／45秒总量，精确记录spawn和状态／PID/starttime及删失。该阶段不会通过原冷启动5秒gate，也不触发请求或自动队列。
3. 共同语义域与factory适配尚待独立明确；本轮没有选择替代词表或改45标签。请求级正确性及强基线研究准入保持关闭。

新状态／时钟合同与预算账本是正确测量的工程前提，不计作研究首创。N1是否具有实际服务问题及相对强对照的贡献仍未知；H3停止、原12observer通过、原冷启动和byte语义gate false全部保持。

## 5. 归档与收尾

本轮源快照12份、AST函数映射28项、旧事件账本仅服务器`literature/20261101-startup-request-scope-review-v1`。固定源码／旧结果回读，不执行import、schema或新实验，仍139runs／3038主回答，索引`e189878f…`不变。旧native-v2四PID现场均不存在，无后台任务。代码／配置／文档同步服务器，原始不回本地；无安装、驱动或系统策略改变，GitHub未配置未push。最终manifest和草案SHA见配套readiness。

最终18文件272016bytes，manifest `8ba1b4a0c55759baf7087714f55a364b82bba3cb6fd7c8cc4d4fb827690e5a90`、closure `20d21c7d94415f81f474a6dee14ca2b37bef637993f57aaec233aa6ebb5315cb`完整回读。新契约SHA `f4e7e758c4bb74aa57ec4ac2d1e17c20a2eac1fe0e66d16e11665364b2def707`，旧source/input/runtime及原run未改。[readiness](STARTUP_REQUEST_SCOPE_READINESS_20261101.json)明确新范围未实现、未执行及请求关闭。

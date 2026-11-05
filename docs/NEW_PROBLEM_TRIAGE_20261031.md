# 新问题筛查：从 KV 约束保持转向具体系统需求

日期：2026-10-31。性质：文献、公开问题与固定源码的只读筛查；不是新实验或正式定题。

## 决策

原 H3 停止，泛“KV 裁剪会损害约束／安全”继续暂停作为论文主线。已验证原型与原始结果保留。新筛四条线索后，仅保留 **N1：结构化输出任务取消后的资源回收与租户间干扰**，建议进入一次有界可行性验证；目前没有建立新方法贡献或完整实证贡献，不能据此承诺发表或毕业。

N1 的需求有公开证据，最直接的解决方案也已有实现。值得继续的问题是：**面对相同语义需求和明确服务预算，现有方案是否能让取消真正终止不再需要的工作，并及时恢复正常请求的服务？为此付出的拒绝率、启动成本和缓存复用损失是否可接受？** 这是待验证的系统问题，不是已经发现的新漏洞。

| 候选 | 当前依据 | 本轮决定 |
| --- | --- | --- |
| N1 结构化输出的取消、资源回收与隔离 | 编译超时报告、线程方案、可杀进程方案、原生预算与协作式取消存在不同资源契约 | 保留为有界实证候选，未定题；不能将“加超时／进程池／缓存上限”当作创新 |
| N2 分离式推理中取消与 KV 生命周期 | vLLM 已有取消时序问题；TensorRT-LLM 已提出故障注入框架并有草案实现 | 暂不优先：通用故障测试已有直接近邻，传输与多节点验证成本较高 |
| N3 权重／LoRA 热更新后的旧缓存复用 | vLLM 已有直接报告与持续更新的权重重载正确性 RFC | 不以“发现旧缓存／增加版本号”为主线，属于直接覆盖 |
| N4 batch 改变导致推理不确定 | 已有 batch invariance、LLM-42、CoRun | 不将此前数值调试改名为新的确定性推理研究 |

N2–N4 的决定是本项目的优先级判断，不是这些领域不存在其他问题。相邻目录只读查看，不删除、合并或改写其状态。

## N1：需求证据与最强对照

### 1. 已知问题，不再作为新发现

- [XGrammar 缓存耗尽公告](https://github.com/mlc-ai/xgrammar/security/advisories/GHSA-389x-67px-mjg3)：2025 年已经披露无界编译缓存问题，0.1.18 为修复版本。重新证明缓存能够占满内存不构成当前选题差异。
- [vLLM #54003](https://github.com/vllm-project/vllm/issues/54003)：2026-08-27 报告受影响版本 JSON／GRAMMAR 编译缺乏超时。它证明有人遇到需求，不是本项目复现；不采用报告中未经证明的复杂度结论。
- [JSONSchemaBench](https://arxiv.org/abs/2501.10868)：已有大规模 schema 覆盖、效率与输出质量评估。通用“比较几种结构化输出后端”已有先例。

### 2. 当前固定源码所能支持的结论

vLLM 固定 `2b009fc6d1493a9a1ad19f4d0c7230b7e6b7e63a`，XGrammar 固定 `ca1acf28bf35b9ba9092800b69aebc7d4ce1f7a7`。仅文本审查，不导入作者模块，不执行测试。

| 观测 | 可核对位置 | 结论边界 |
| --- | --- | --- |
| manager 创建线程池，异步分支提交 `_create_grammar` | `api_source_1.py:97`、`:198` | 证明该分支的提交方式；未测实际调度或退出时间 |
| regex helper 超时后 `future.cancel()`、`shutdown(wait=False)` | `api_source_0.py:83–98` | 不能由调用方返回推导正在运行的 native 编译已经终止 |
| JSON 分支直接调用 `compile_json_schema`；regex 分支通过 timeout helper | `api_backend_xgrammar.py:146`、`:164` | 限于已审函数，不声称全部入口都没有保护 |
| scheduler 等待 grammar 时检查就绪与异常 | `api_scheduler.py:3525–3537` | 此分支未见编译 deadline；未完成端到端 abort 路径审计 |
| vLLM 传入 compiler cache 上限，没有显式启用 dynamic compilation | `api_backend_xgrammar.py:216–224` | 不把 XGrammar 独立能力当作该 vLLM 路径已启用的功能 |
| XGrammar 可设置 cache 上限及 dynamic compilation | `api_source_2.py:107–154` | 缓存上限不直接等于整个编译过程的峰值内存／CPU 上限 |

这些源码位于服务器文献归档。固定源码入口：[manager](https://github.com/vllm-project/vllm/blob/2b009fc6d1493a9a1ad19f4d0c7230b7e6b7e63a/vllm/v1/structured_output/__init__.py)、[helper](https://github.com/vllm-project/vllm/blob/2b009fc6d1493a9a1ad19f4d0c7230b7e6b7e63a/vllm/v1/structured_output/utils.py)、[XGrammar backend](https://github.com/vllm-project/vllm/blob/2b009fc6d1493a9a1ad19f4d0c7230b7e6b7e63a/vllm/v1/structured_output/backend_xgrammar.py)、[compiler](https://github.com/mlc-ai/xgrammar/blob/ca1acf28bf35b9ba9092800b69aebc7d4ce1f7a7/python/xgrammar/compiler.py)。未审全部 C++／Rust 实现，不声称完成安全审计。

### 3. 已有方案必须纳入，不能只打旧默认实现

| 对照 | 已有能力 | 尚需实证区分的量 |
| --- | --- | --- |
| [PR #45172](https://github.com/vllm-project/vllm/pull/45172) | scheduler 侧编译 deadline、请求失败处理；2026-10-31 API 为 open、未合并，head `fa5b81388b5fd5d388671913bf35d1611b5f39e2` | 客户端／调度器返回错误与底层计算、内存、槽位释放的时间差 |
| [PR #52119](https://github.com/vllm-project/vllm/pull/52119) | regex 可终止 worker、并发池、超时 kill／join 与后续替换；open、未合并，head `a3a2d6567c0e5fc1f9c0df9261237f9249099dce` | 正常工作开销、序列化、共享缓存与请求主动取消；不能将其早期 fork 设计当作当前版本 |
| [llguidance](https://github.com/guidance-ai/llguidance/blob/3d698ee07b3a67b0aef50fb6058612e8fd30aca2/parser/README.md) | 原生 matcher 协作式取消；`ParserLimits` 有初始／逐步 lexer fuel 等预算 | 文档明确没有固定取消期限；不同阶段、依赖调用和缓存等待的实际回收边界仍未测 |
| [GRID](https://github.com/evolutionIdGmbH/grid/blob/088be8182e1a326523586af0c4f639afbb5fb6bc/docs/choosing-a-backend.md)、[集成 RFC](https://github.com/vllm-project/vllm/issues/50966) | 作者提出按输入触发的构建预算、确定性拒绝、未强制约束的可见记录；有 serving 和 single-flight 报告 | 仅审作者说明，未审完整预算实现或复现；其效果不能视为本项目结果，也不能忽略其近邻地位 |
| [XGrammar-2 v4](https://arxiv.org/html/2601.04426v4) | JIT 把部分 mask 构建移到运行时，跨 grammar 复用 | 阅读了方法 3.5 及相关上下文；独立动态模式需覆盖首次 mask 工作，不能仅测启动编译。尚未验证与上述 vLLM pin 的版本组合 |

PR 当前 files API 的补丁与 head 元数据分别归档，不能把在线补丁抓取等同于逐文件 Git blob pin。llguidance pin 为 `3d698ee07b3a67b0aef50fb6058612e8fd30aca2`，GRID pin 为 `088be8182e1a326523586af0c4f639afbb5fb6bc`。这轮未安装任一新依赖或测试其兼容性。

### 4. 可研究范围与不成立时的停止条件

建议暂用工作描述：**“面向共享 LLM 服务的结构化输出资源生命周期评估”**。不是最终题名，也不是宣称设计了一种新编译器。

应区分五个时刻／阶段：排队、实际编译、首次 mask、取消确认、实际工作终止与资源重新可用。若采用共享编译／缓存，还需区分“当前请求取消”与“其他仍在等待的请求仍需要该工作”；直接杀掉共用工作不自动构成正确回收。

最小实证应回答三个问题：

1. **取消生效了吗？** 分别记录调用方返回、底层 worker 停止、池槽可复用、内存回落；超时与主动取消分开。仅报 HTTP 错误时间不够。
2. **是否保护正常请求？** 在固定 CPU／内存额度下，对照独占运行与同预算共享运行的正常请求完成率和等待尾部；若测模型端延迟，须另立真实服务协议，不能由纯 CPU 测量外推。
3. **代价是什么？** 正常 schema 的拒绝率、接受语言／mask 一致性、冷暖缓存开销和复用损失必须同时报告；把语义范围缩小不能只报为“防护成功”。

下一步具体操作：先形成可执行的 **纯 CPU 可行性协议与兼容性预检**，绑定可用后端版本、最强对照、公开 schema 小样本、可审计的取消／计时方式及资源上限。先验证观测器能区分“返回”和“停止”，再考虑有界配对小试；不先实现完整服务平台。当前没有该候选的 runner、输入冻结或执行登记。

继续条件：在上述强对照和可比语义覆盖下，至少存在可重复、具有实际服务影响的不足，并能提出可测的改进；对系统／实证路线，贡献可以是明确问题、统一测量和可复现证据，仍需说明相比已有基准多回答了什么。

停止条件：强对照已经满足相同需求；差异仅来自旧版本、测量错误、关闭现成功能或不公平语义范围；只剩“给线程改成子进程”；或只能制造极端成本却没有实际服务影响。不以扩样本、换阈值或反复改名救回候选。

## 其他候选的直接近邻

- N2：[vLLM #46240](https://github.com/vllm-project/vllm/issues/46240)、[TensorRT-LLM RFC #18450](https://github.com/NVIDIA/TensorRT-LLM/issues/18450)。后者已有 CPU 故障测试与 draft PR #20615 的作者进展说明，框架仍有未完成部分，不能说已经彻底解决，也不能按空白领域立题。未审完整 draft，未验证网络／GPU 传输。
- N3：[旧 LoRA 缓存报告 #42125](https://github.com/vllm-project/vllm/issues/42125)、[Weight Reload Correctness RFC #48312](https://github.com/vllm-project/vllm/issues/48312)，后者更新至 2026-10-27，明确涉及正确性分类和缓存一致性。前者被 stale 关闭不等于问题已修复。
- N4：[vLLM batch invariance](https://docs.vllm.ai/en/v0.15.0/features/batch_invariance/)、[LLM-42 作者仓库](https://github.com/microsoft/llm-42)、[CoRun](https://arxiv.org/abs/2608.14376)。未在本机复现这些方法，不据仓库声明推定实际部署或独立录用核验。

## 归档、失败与计数

服务器 `literature/20261031-new-problem-triage-v1`：31 文件／564110 bytes；manifest `1fc87993b48fb89b7b6538841a81062db73dc166959d508bea65e690780d966f`。30 个 payload 文件逐 SHA 回读，24 条成功来源记录的 hash／字节核对通过。9 次 raw GitHub 超时／网络失败保留；相关必要源码通过同官方 Contents API 回退，6 个 vLLM／XGrammar 源文件及新增对照源码做 Git blob SHA1 核对。未回退的文档不是不存在的证据。web-only 阅读链接在 closure 中单列，不冒称都已保存原文。

无新实验、模型回答、分词、权重读取、GPU 查询、安装或服务。前轮六个 H3 自有 PID 现场核对均不存在，本轮来源抓取已结束，没有后台任务。实验仍为 132 runs／3038 历史主回答；只读审阅不新增 run。现有索引 `results/20261031-run-index-decoder-h3-screen.json` SHA `b0c4d8fda03a662a5a30ccde9af934846bf45d7f73e2c06df546a2db9339f475` 现场只读核对不变。源码／原始来源仅服务器，本地只保存本报告和交接文档；GitHub 未配置、未 push。

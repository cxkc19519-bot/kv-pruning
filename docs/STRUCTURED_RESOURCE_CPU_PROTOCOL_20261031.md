# 结构化输出资源生命周期：CPU 可行性协议 v1

日期：2026-10-31。承接[新问题筛查](NEW_PROBLEM_TRIAGE_20261031.md)。机器配置见[冻结配置](../configs/structured-resource-cpu-feasibility-v1.json)。本轮完成静态环境预检、公共输入冻结和协议；没有执行真实语法编译、mask 或取消实验。

## 当前判断

N1 仍可进入工程验证，但**当前环境不足以直接判断研究缺口**。现有旧版只可用于接口／观测器诊断。不能把最强对照未部署记为对照失败；尚未证明资源干扰存在，更未证明已有方案无法解决。

下一步实现并登记一次 **12 项标准库观测器工程验收**。它只验证事件、进程所有权和回收观测，不执行作者后端。通过后才另登记现有后端的 8 schema／45 实例正确性检查；后者也不能据旧版结果定题。配置的 `execution_enabled=false` 表示没有可执行实验入口，不撤销本会话已有的小规模验证授权；无需为这类已授权工作重复请求许可。

## 现场兼容性预检：实测事实与边界

复核命令（本轮已执行一次；新目录只写，不覆盖重跑）：

```text
.venv/bin/python scripts/preflight_structured_resources.py --output literature/20261031-structured-resource-preflight-v1/environment
```

| 项目 | 2026-10-31 实际读取 | 对实验的影响 |
| --- | --- | --- |
| `.venv` | `include-system-site-packages=true`；继承 Torch 2.5.1+cu121／tokenizers 0.22.1／Transformers 4.57.1；未发现 xgrammar／llguidance／vllm 分发元数据 | 只看 venv 自身的空 site-packages 会漏报继承包，已修正扫描方式；不适合直接当作语法后端环境 |
| `.venv-controller-history` | vLLM 0.32.0、XGrammar 0.2.8、llguidance 1.7.6、Torch 2.13.0、tokenizers 0.23.3、Transformers 5.19.0、psutil 7.2.2 | 可作为将来旧版接口工程环境，尚未执行导入／native 兼容测试 |
| vLLM 分发依赖 | `xgrammar==0.2.8`、`llguidance>=1.7.0,<1.8.0` | 不在原环境升级 llguidance 到 1.9.x 后仍称依赖满足；强对照应独立构建／部署并冻结版本 |
| XGrammar 0.2.8 Python 源码 | 有 cache 上限，没有 `enable_dynamic_compilation` 参数 | 不能用它代表上轮最新源码的 JIT／首次 mask 行为 |
| llguidance 1.7.6 stub | 有 `LLParserLimits` 与 lexer fuel，未见取消接口 | 不能代表 1.9.x Rust 的协作式取消 |
| 最新 llguidance 固定源码 | changelog：1.9.0 加 opt-in matcher cancellation，1.9.1 暴露 TokenParser cancellation；审查最新 Python stub 和两份 Python binding Rust 文件未见取消入口 | 必须区分 Rust 原生功能与 Python 绑定能力，不能凭库版本假定 Python 可直接调用；未做全仓完整接口审计 |
| Rust 工具链 | 当前 PATH 找不到 `cargo`、`rustc`；有 `cc` | 当前尚不能直接构建原生 Rust 取消对照；不等于服务器永远无法获得工具链 |
| 当前 SSH cgroup | v2，session 目录不可写，memory／pids 值为 max，没有可写的 cpu.max | 不具备当前用户可直接设置的 aggregate hard limit；未尝试写入或提权 |
| 本进程 CPU affinity | 可见 128 CPU | 这是可见范围，不是可独占额度；后续自有验收最多绑定 2 CPU |

仅使用标准库读取元数据与文本，没有 import torch/vllm/xgrammar/llguidance、运行编译器、加载模型／分词器或查询 GPU。预检 PID 1796798，内部 0.034389 秒、exit 0，收尾核对 PID 不存在。新预检脚本 SHA `e2428a6f3bf7b1aecdb196401a9dd89294ef155c5f173e2295da6f9d367b1cb3`；20 个环境来源快照／22 环境工件，共 430291 bytes，inventory SHA `f8e8185cca607012a6d96ccdda5057d13a1f9d3a28ef139e17b055e1eeb3bd99`。它是静态来源预检，不计新实验 run。

官方依据：[llguidance changelog](https://github.com/guidance-ai/llguidance/blob/3d698ee07b3a67b0aef50fb6058612e8fd30aca2/CHANGELOG.md)、[Python stub](https://github.com/guidance-ai/llguidance/blob/3d698ee07b3a67b0aef50fb6058612e8fd30aca2/python/llguidance/_lib.pyi)、[matcher binding](https://github.com/guidance-ai/llguidance/blob/3d698ee07b3a67b0aef50fb6058612e8fd30aca2/python_ext/src/llmatcher.rs)。最新 GRID pyproject 为 0.4.2／Python>=3.11；本机未发现其分发元数据。源码声明不等运行兼容验证。

## 输入先冻结，禁止根据耗时挑“有效攻击”

采用 [JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/8cab295687d150de3900a160c6ad002b53ddb30e/tests/draft2020-12)，固定 commit `8cab295687d150de3900a160c6ad002b53ddb30e`。预先指定 type、enum、required、properties、items、oneOf、maxLength、pattern 八个文件，各按原顺序选第一个同时有 valid／invalid 标签的组，恰为各第 0 组。保留全部 **8 个 schema、45 个原始标签实例**，不因不支持或转换错误换组。

服务器 `literature/20261031-structured-resource-preflight-v1/public_schema_selection.json`，10478 bytes，SHA `41a774b5ae2bc5f43cc0b7ec754ea786491307c562b616b9f36374cb7856d085`。没有以编译耗时、回收时间或任何后端结果选样。这是语义工程小样本，不是代表性自然请求分布，更不是压力集。

先使用合成 257 词项：id 0–255 对应原始单字节，id 256 对应 EOS `<|eos|>`。所有 JSON 实例固定 ensure_ascii=true、sort_keys=true、紧凑分隔符、拒绝 NaN；当前最长实例 26 bytes。适配器需先验证词表／EOS／byte roundtrip，不加载任何模型 tokenizer。这个词表可测流程，不能外推真实十万词表的性能。

XGrammar 使用 `strict_mode=False`、允许任意 JSON 空白；保留 schema 原文。否则默认严格模式可能收紧原 schema 允许的对象属性或数组行为，产生不公平差异。每个实例从新 matcher 开始，逐 byte 核对 mask 后提交，再明确检查 EOS；仅 `accept_string` 成功不能代替逐 token 路径。报告 valid 被拒、invalid 被接受、不支持、异常、超时及 N/A，不能只报支持子集成功率。45 个有限实例通过也不能证明语言等价；跨后端的非预期默认转换必须先说明，不静默补 `type: object` 或删除约束。

## 观测协议：返回、结束和容量恢复分别取证

| 事件／量 | 定义 | 不能据此推导 |
| --- | --- | --- |
| submitted／work_started | 提交时间；worker 发出进入真实调用前的开始事件 | 排队时间不混入纯计算耗时 |
| cancel_requested | 父进程发出取消或 deadline 的时间，主动取消与超时分开标注 | 不能默认工作已经停止 |
| caller_returned | 调用方实际收到结果／异常的时间 | 不能以 Future.cancel 返回值推定 native 调用终止 |
| work_finished | 调用的 finally／结束事件；正常、异常分别记录 | 没有结束事件不能填作零耗时 |
| process_reaped | 专属工作进程已退出并 join／wait，PID+starttime 匹配 | 进程 kill 请求发出不等已经退出 |
| same_slot_probe | 同一个真实执行池／槽执行固定正常工作并完成 | 不能新建一个池假装旧池恢复 |
| cleanup_complete | 全部自有 child 退出，所有权与 starttime 核对 | persistent worker 存活不自动意味着有残留工作 |

父进程和 worker 都保存 monotonic_ns 时间与事件序号；消息接收时间与 worker 事件时间分开。每条带 run/case/request/shared_work id、PID、PID starttime、native TID、slot id，防止复用 PID 或混淆共享任务。数据丢失、进程中途崩溃和缺少结束事件是 failure／right-censored，不填成功。

外部监督进程独立存活并以 10ms 周期采样自有进程 CPU ticks、RSS、线程和退出状态；记录实际采样间隔。测 GIL 阻塞必须靠外部观测，不能把同一解释器中的 timeout 线程能按时运行当作假设。CPU 变化分辨率受内核 tick 限制，RSS 可能重复计算共享页；二者不冒称精确计费或硬额度。缓存与 allocator 保留需要单列，不把 RSS 不回到初值直接判成泄漏。

共享编译的所有等待者要有引用／生命周期记录：A 取消而 B 仍需要同一工作时，工作继续可能是正确行为；不能以“杀掉全部共用工作”获得虚假回收优势。正常探针与对照使用同一池、相同 worker 数量和相同语义要求。

## 分阶段执行与明确边界

### A：下一步 12 项观测器工程验收

不导入作者后端，只用标准库的可控合作式工作、线程 Future 和专属工作进程验证：排队取消、运行中 Future 无法取消、调用方 deadline 后工作继续、合作停止、kill+reap、worker 异常、无结束事件退出、完成赢得取消竞态、重复取消、原槽正常探针、cleanup 超时、共享工作仍有其他等待者。每项明确应有事件与不可混淆的状态。

最多 12 case／2 work process／2 CPU、每 case 3 秒、总 120 秒、显式分配<=1MiB；原始工件<=64 文件／8MiB（含 summary/manifest）。barrier 控制已开始与已完成，避免靠任意 sleep 制造预期顺序；case 超时立即标失败并清理自有进程，不自动重试。对合成工作只报告观察正确性，不报告系统漏洞／真实性能。必须按公共模板另登记，冻结 runner、validator 和源码 hash 后才运行；本轮未实现或登记。

### B：现有后端 API 正确性，A 通过后另登记

仅现有环境 XGrammar 0.2.8／llguidance 1.7.6，绑定 `.so`／Python 包 hash，先检查 CPU 导入、离线、GIL 观察和合成词表适配。最多 16 次 schema 构建、90 个新 matcher、2430 次 mask（45实例×两后端×最多27步的保守上限）、180 秒总墙钟／单调用5秒 watchdog。默认一个后端 native 线程；实际配置达不到则显式记录，不推定同线程数。失败保留，不换 schema 或静默降级。此阶段不测跨租户损害，不根据旧版表现决定方向 go。

### C：强对照配对筛查，当前条件未就绪

需将 [scheduler deadline PR #45172](https://github.com/vllm-project/vllm/pull/45172)、[修订 worker pool PR #52119](https://github.com/vllm-project/vllm/pull/52119)、最新原生 llguidance 预算／取消、GRID 构建预算列入对照。PR 的 regex 范围不能冒称覆盖所有 JSON／GRAMMAR 入口；复制其策略写出的本地壳只能标“代表性方案”，不能标精确 PR 复现。动态／首次 mask 范围需兼容的 XGrammar 版本，不能与已有 0.2.8 混报。

当前没有这些对照的可执行冻结方案，也没有 cgroup delegation。将来可以评估受限子进程，但 RLIMIT_AS 是单进程虚拟地址空间上限，affinity 是可运行 CPU 范围，采样 RSS watchdog 有延迟；三者不能冒充整个服务的 CPU／内存硬隔离。若研究主张需要硬额度，必须先拿到可验证的自有 cgroup／等价隔离，不写他人 cgroup 或更改系统策略。本轮不安装、不升级原环境，不为缺条件启动半套科学对照。

配对筛查必须另冻工作负载、到达顺序、取消时刻、正常请求对照、重复次数、缓存冷暖和资源预算。小样本先报逐项、配对中位数／最大值与删失，不报不稳定的 p99。CPU 探针延迟不是 HTTP TTFT／TPOT；若实际服务影响是贡献核心，后续必须接真实服务验证。

## 决策与归档

继续需同时满足：观测器和语义流程正确；强对照可运行且范围公平；出现可重复、对正常服务有实际意义的不足，或能够独立回答已有基准未覆盖的生命周期问题。现成方案已经满足需求、只剩旧版 bug／语义错配／已知 timeout 或进程池复刻时停止。缺部署条件只记未验证，不直接判学术 no-go。

这轮新增的是静态预检来源与公共 schema 冻结，属于文献／接口准备；0 新实验 run、0 真实编译／mask／取消调用、0 模型／GPU／安装／服务。累计仍132 runs／3038历史主回答，旧 H3、QA、Mistral 和停止队列不恢复。文档与预检代码同步服务器，原始只服务器，未配置 GitHub push。

最终归档 `literature/20261031-structured-resource-preflight-v1`：41 文件／607993 bytes，manifest SHA `18cfd4bbf8941b2f70026080a1f56c252dc6923dbbde7219a1bd59c030d58f59`。20 环境来源快照与13官方 source blob、8组选样／45标签、配置与旧索引均独立回读复核，verification SHA `797fb0b11463d94f5463446f9aa51bcedbdd07ff9afc8a41d58e5de568776feb`。13个本轮官方源抓取均成功，上轮9次 raw 网络失败保持原档不改。本轮第一次查找本目录不存在的 EXPERIMENT_TEMPLATE 后改读上级公共模板；最初只扫 `.venv` 自身导致继承包未列出，最终预检已依据 pyvenv.cfg 补扫继承来源，不把初步空列表当无依赖结论。[readiness](STRUCTURED_RESOURCE_CPU_READINESS_20261031.json)列明当前就绪范围。

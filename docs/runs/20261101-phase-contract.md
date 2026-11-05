# 分阶段状态／时钟软件验收与import-only启动工程

## 实验身份

- 日期：2026-11-01，Asia/Singapore；授权服务器，用户专用实验会话“开始下一步”。
- 软件绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-phase-contract-software-v1`。
- 启动绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-startup-import-only-v1`。
- 状态：8项软件验收通过；绑定实际证明后另登记的fresh启动失败（SIGSEGV/-11）。两个launcher及独立validator exit0只表示工件一致、收尾完成。
- 问题：[新分阶段契约](../STARTUP_REQUEST_SCOPE_REVIEW_20261101.md)能否区分启动、factory、请求、caller返回与work结束，并在新范围达到库导入就绪。自建工程验证，非模型／语义／租户干扰效果实验。

## 可复现条件

- [软件登记](../../configs/phase-contract-software-v1.json) SHA256 `79b46dd52848b3096eb444cffaebabbdbfb75b03efdd2684b6ee312eb4b66dae`；[启动登记](../../configs/startup-import-only-v1.json) SHA256 `ffd6cfb208533379b9d668446f339f591f0e14fd3d02bc653c11c9ddb8b2fb38`。均冻结source/input后各执行一次，无重试。
- 新代码phase_controller、accept_phase_controller、phase_runner及verify_phase_runner。软件只用标准库，validator不导入控制器或作者库，重建时钟、区间并集与账本。原import_boundary_v2/checked_archive未改，不重复23guard或12observer。
- 固定Python3.11.13；真实worker使用既有.venv-controller-history（Torch2.13.0、XGrammar0.2.8），101运行文件及2额外dill/Torch来源pin在两次运行前后均一致。未查询GPU、加载模型、模型tokenizer或权重。CUDA隐藏不等于已完成CUDA后验；新启动未成功导入Torch，也未进入XGrammar。
- 软件8固定用例：启动拒schema、启动超时禁入、import/factory分层、验证在请求计时内、阶段不重置、caller返回不等work停止、scope/owner变化失效、启动/factory/cold-first/warm账本。合成45逻辑秒fixture（20/4/4.5/2/14.5秒）不是实际性能。
- 软件总30秒／显式fixture≤1MiB；新启动从父Popen前spawn时间戳计30秒、launcher总45秒，2CPU/1native线程；各归档≤64文件8MiB。未来请求5秒端到端只验了合成状态合同，未实现真实后端请求。
- 精确/dev/null和固定只读ldconfig边界、离线、禁安装/任意子进程；Python边界不是OS沙箱，信任native库。无schema、词表构造、compiler factory、matcher或mask；原257词表FF冲突保持，45标签关闭。
- 无Git提交/remote；源码SHA、输入与环境字典在registration/execution/source快照。启动登记绑定软件verification及manifest。

服务器项目根目录内实际执行（仅作复现记录，不自动重跑）：

```sh
.venv/bin/python -I -S -B scripts/phase_runner.py --execute --registration configs/phase-contract-software-v1.json --registration-sha256 79b46dd52848b3096eb444cffaebabbdbfb75b03efdd2684b6ee312eb4b66dae
.venv/bin/python -I -S -B scripts/phase_runner.py --execute --registration configs/startup-import-only-v1.json --registration-sha256 ffd6cfb208533379b9d668446f339f591f0e14fd3d02bc653c11c9ddb8b2fb38
```

## 结果与证据

| 项目 | 软件验收 | fresh启动 |
| --- | --- | --- |
| worker | exit0，8/8通过 | SIGSEGV，exit-11 |
| 独立验收 | 9份账本重算一致，guard全0 | 失败证据一致，startup gate false |
| launcher总墙钟 | 0.145495056秒 | 1.382368514秒 |
| 原始归档 | 24文件104331bytes | 27文件231545bytes |
| 实际library/factory/request就绪 | 合成合同，非真实后端 | 均false |

真实事件只到torch_import_begin，没有Torch完成或X开始。未触发30秒watchdog；最后外部存活采样距父spawn为1.265345777秒，准确崩溃时刻未记录，不把launcher总时间当导入耗时。唯一1秒faulthandler输出仅到pathlib.py的_format_parsed_parts即截断，没有完整fatal traceback，不能定位具体Torch、audit、faulthandler或native缺陷。worker-status/phase-state缺失，CUDA后验与最终guard计数未知，不补零；观察denial事件0不等于最终计数完整。

只读query PID2248102/starttime428244828，exit0，0.005380768秒，stdout103903bytes/stderr0，stdout SHA256 `1a3b04fe196649d01c9bd1c03e8cc09fbf8152a638a590c58d989f781fb8dd03`。精确查询正常不代表Torch完成。

- 软件launcher/worker/validator PID2246745/2246748/2246749，starttime428229591/428229596/428229604；启动2248097/2248100/2248104，starttime428244751/428244760/428244888，连同query共7PID现场核不存在。无后台、服务、端口或队列。
- 软件manifest `b72b425ff58b283becf900e27545ab884e100c108d54a48f49bd36763ad07e38`；verification `9585ee6b91d89d45253974162b62c8ad1a295c08ee6034a7690d74a03d3cabef`。
- 启动manifest `e366bc2a86f2b66ee6fd19e0f5156ccc71472a889edc29278c31bf5328977a31`；verification `a2da8d5d344e45f3a9cbd52da6520c6e1acc45d6ad530fbb69475063202a978e`。
- 两归档全部文件hash/count/bytes独立回读；source/input、runtime101+dill2不变。原结果/旧索引未修改。
- 补充closure：服务器results/20261101-phase-contract-closure.json，SHA256 `b746a031c7e4f07f3769d468dbcf160844de3eea2c960038c5e2e3cf2949c289`。
- 新索引：服务器results/20261101-run-index-phase-contract.json，SHA256 `97ac2a66783bb0a1ad2f1a9bd06bf8bb8396f871ab4e8dea7e9b91bf239e4a42`。新增2CPUrun（含1失败），累计141runs3038历史主回答，新增回答0。

## 解释与下一步

直接观察：软件合同通过，真实库导入未就绪。本次是崩溃，旧native-v2是原5秒删失，两者不混同，不倒推旧成因。软件pass不证明backend/factory/domain/cancel资源效果；原cold5、FF身份和有限语义gate仍false。N1效果与新颖性未建立，H3停止/泛KV暂停保持。

下一条先只读对照此次与旧worker启动参数、源码/环境及faulthandler/audit机制，查看可得的自有进程故障证据，再冻结有限定位方案与停止条件。无自动重试或native队列，不重做8/23/12项，不构造词表/编译器，不运行45标签。

已更新STATUS/WORKLOG/HANDOFF/PLAN/README及readiness，代码配置文档同步服务器；原始仅服务器，未安装依赖、修改系统/相邻项目或推送GitHub（未配置）。

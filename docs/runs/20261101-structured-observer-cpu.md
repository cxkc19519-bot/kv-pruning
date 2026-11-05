# 结构化输出生命周期观测器：12项CPU工程验收

## 实验身份

- 日期：2026-11-01，Asia/Singapore；跨过午夜，沿用2026-10-31冻结协议，不改旧文档日期。
- 授权：本实验会话用户“开始下一步”；标准库观测器正确性验收。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-structured-observer-cpu-v1`。
- 来源：自建可控合成工作／Future／专属子进程，不运行作者语法后端或真实负载。
- 当前状态：**12项全部通过、独立事件复核通过，单次运行exit 0；最终归档回读通过。**

## 可复现条件

- [冻结CPU协议](../STRUCTURED_RESOURCE_CPU_PROTOCOL_20261031.md)、[原配置](../../configs/structured-resource-cpu-feasibility-v1.json)保持不改；实际执行许可来自[新登记](../../configs/structured-observer-execution-v1.json)。
- 新runner、独立validator及现有checked_archive源码SHA和旧协议输入SHA写入登记；无Git远端。服务器已有Python3.11.13，以`-I -S -B`隔离启动，不加载site或作者包。
- 12个既定case，case<=3秒／总<=120秒／自有工作进程<=2／affinity<=2；显式合成工作分配<=1MiB，最终归档<=64文件／8MiB。合成工作主要等待barrier，不是CPU压力测量。
- 网络／后端导入／模型与权重／安装／GPU／公共服务均不允许。允许创建的task子进程限定同一固定脚本及hold/abrupt模式；进程kill/reap按PID与starttime匹配，外部独立采样10ms目标间隔。
- 新登记SHA `21c4c487c6bce91d5bcb0dbbb7bb60cbfcc12d899745fa702f635f5564cb6c40`，四个新文件同步、AST静态检查、source/input hash匹配且run不存在后只执行一次。原execution=false协议保持历史快照，不追改。
- 实际命令（已执行，勿原路径重跑）：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -I -S -B scripts/run_structured_observer.py --execute --registration-sha256 21c4c487c6bce91d5bcb0dbbb7bb60cbfcc12d899745fa702f635f5564cb6c40
```

- launcher PID1805119，12个case PID1805122/24/26/28/30/32/34/36/38/40/42/44，3专属task PID1805131/35/43，verifier PID1805146；17个自有PID收尾均不存在。launcher内1.176444秒，validator内0.007076秒，最长fixture内部0.068812秒，都是工程运行耗时，不报为真实后端性能。

## 结果与证据

原始事件137条、外部样本102条；worker_manifest和最终manifest逐文件SHA独立回读，最终37文件143828bytes，manifest SHA `feb73647aaef7f7f2a6f71115380ea1b488b19ca6afe0412b2707f94451231b3`，independent_verification SHA `fd03c95022cf3ac362783a7cc589554450ee14e2c2ccc3308d8bb58d41182bd5`。cap包含最终summary／manifest，先检查再写complete。

| 固定case | 原始证据与独立判断 |
| --- | --- |
| queued_cancel | 占位任务已开始；排队B取消true且从未开始 |
| running_future_not_cancelled | A已运行，cancel返回false，调用方返回时Future仍running／not done；随后释放才结束 |
| caller_deadline_work_continues | Future.result超时已返回，work尚未结束；结束在显式release之后 |
| cooperative_stop | 合作事件使工作结束，随后调用方收到cancelled |
| process_kill_reap | 专属子进程开始后按PID/starttime kill，exit -9并reap，再确认调用方结果 |
| worker_exception | work结束事件记录error，Future传播原预期RuntimeError |
| worker_exit_without_end_marker | 子进程exit 7，结束事件缺失，exact work end保持删失，不填零／成功 |
| completion_wins_cancel_race | 工作先完成，之后cancel false，结果保留already_completed |
| duplicate_cancel | 同一排队Future重复取消均true，仍未执行，不重复启动／回收 |
| normal_probe_reuses_same_slot | probe先排队；原work结束后，同PID/starttime/native TID/pool/slot执行probe |
| cleanup_timeout_is_failure | 合成清理等待超时显式记录failed与cleanup_failed；随后强制kill/reap负责最终清理，不把初次超时伪装成功 |
| shared_work_has_other_waiter | A脱离后B仍在，底层work继续并成功交付B；不把合法共用计算当残留 |

故意的exit7／cleanup失败是受控fixture的预期状态，不是本run失败；原始事件保留。所有禁止项guard为0，仅3次登记task创建被允许。backend/模型/分词/GPU/权重/网络/安装实际均0。事件顺序、线程槽身份、PID所有权、采样及退出状态由不导入runner的validator重判。

各case独立报告caller latency、work结束或reap上界、probe等待及实际采样间隔；工作多为等待barrier，不是CPU压力。9个case取消后采样不足，其CPU tick delta为null；不能说这些case消耗为0。RSS为采样值，可能重复计算共享页，不称硬内存隔离或精确费用。全部场景只说明观测状态正确，不将137事件／102样本当独立科学样本。

新增1CPU run／0模型回答，累计**133 runs／3038主回答**。新索引 `results/20261101-run-index-structured-observer.json` SHA `03ed7996ab948ee45d9ec29f27c34a966ecba6d4fbf222e5d77f5e070e5246be`；旧132run索引 `b0c4d8fd…`保持不变。源码配置文档同步服务器，原始只服务器。

## 解释与下一步

此验收不证明真实编译器／GIL／CPU隔离／生产服务性能或新颖性。下一条实现并另登记现有后端CPU导入、GIL外部观察、257合成词表／8schema45标签正确性检查；绑定native二进制与适配器hash，保持现有环境不升级。它是旧版接口工程，不据其表现证明强对照不足。当前没有真实后端执行入口／队列，不自动恢复旧KV实验。STATUS、WORKLOG、HANDOFF、readiness和新索引均已更新，无自有后台任务，GitHub未配置未push。

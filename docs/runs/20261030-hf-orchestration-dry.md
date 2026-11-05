# HF编排接线：不加载模型的完整流程验收

## 实验身份

2026-10-30，Asia/Singapore。用户要求“开始下一步”，按交接将条件准入接入新HF编排壳，仅做CPU dry-run。服务器绝对目录：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-hf-orchestration-dry-v1`。

状态complete，v1一次成功，无失败/重试；PID934338退出。0主/工程模型输出、0真实权重加载/GPU/网络请求。新增1CPU run后累计109run2852历史主输出，不作独立样本量。

## 可复现条件

| 源码/配置 | SHA256 |
| --- | --- |
| scripts/reliability_hf_orchestrator.py | 5989170ee0224c885dc4678621adc3372860627e971d383e0c3b67cd136d171d |
| scripts/reliability_qwen_hf_backend.py | 7e6f453cdb4d85779c23c382de78df18744b6d1fc6ec0e16b942303a19eb69af |
| scripts/hf_orchestration_acceptance.py | 945b13bb0335bfc21e4827b79110b33d136bb35acfc355d812ec258b90b29ec1 |
| scripts/accept_hf_orchestration_dry_run.py | 1b70f2c2361395ddd2e1bf64e2e591feb5236e556e793f1f9e84c793cef36c5e |
| configs/hf-orchestration-dry-run-v1.json | 1d0942b4d30330798c64b5e81c0f244c74ce96be8c12c126b03a301623fecf1d |

原proposal false/未实现字段保留，实际execution snapshot另存。15固定输入SHA包含旧工程scope/evidence/report、14题tokenized、64组来源元数据、旧实际snapshot/模型配置及旧KV原语；总511251bytes/64源JSONL行，未读取或推理封存题输入tokens。原已有14个工程/开发准备样本仅工程2+DEV12。

纯标准库与软件double；真实适配器的**模块和空构造**可导入，但torch/HF/KV旧生成模块均未import。AST核验重型import仅位于HF适配器`_load()`；两次负向入口守卫在权重加载前失败，没有进入实际模型行为。没有依赖安装/环境变化、GPU查询、作者代码执行或新后台服务。

内部60秒、输入1MiB/100源JSONL行、归档16MiB/32文件；外层65秒未触发。原样已执行命令（旧run拒绝覆盖，不作重跑待办）：

```bash
.venv/bin/python -u scripts/accept_hf_orchestration_dry_run.py --execute-dry-run
```

原Python版本、源码/配置/输入hash、边界写入snapshot。launcher的绝对命令、PID、时间、exit0与stdout/stderr在同级`.launch.json`/`.console.log`；实际0.175005769秒含读写/软件检查，不是模型性能。

## 结果与证据

22软件用例全部通过：lazy dry-run、预算拦截、DEV工程门槛、bootstrap不自锁、Full三路径顺序、请求/input ids/随机selector group篡改、角色/封存隔离、旧scope拒绝、阶段开关、调用/重复/墙钟上限、路径不一致和加载失败后停止、输出绑定、截断一致性以及两次实际适配器负向守卫。

| 计数 | 观察值 |
| --- | --- |
| 旧scope DEV可准入/预算阻止/证据阻止 | 36 /20 /4 |
| 新代码拒绝旧条件证据 | 5个条件 |
| 新代码计划bootstrap操作 | 14，仅计划、未调用模型 |
| 新工程预算不可行case-condition | 4，不产生路径调用 |
| 新DEV计划格 | 60 |
| 新DEV预算阻止 | 20 |
| 新DEV等待同版本工程证据 | 40 |
| 正式dry-run后端工厂/execute调用 | 0 /0 |
| 软件用例中的真实适配器负向守卫调用 | 2，均在模型加载前拒绝 |
| 实际权重加载/模型输出/GPU请求 | 0 /0 /0 |

软件stub工程返回值只用于单元控制流验证，不进入实际14题计划的工程evidence。新scope的verified_engineering_cases全部0；干运行没有伪造模型工程通过。旧工程evidence与旧分数/门槛保持；新代码hash改变，所以不能延用旧36个准入结果。

外层独立重算14个case input+context_group指纹、目标runtime digest、60格预算/准入、14bootstrap/4不可行操作；核验5个旧scope拒绝、新evidence均未验证、backend descriptor生成开关全部false以及15输入不变，均通过。不是新版GPU数值/缓存等价性验证。

| 工件 | SHA256 |
| --- | --- |
| manifest.json | 50076c5e591c5b99d5a77987000b3c297706add18661674bd92856c18a40771d |
| report.json | 7ff2c1df140e1f8c1017529ed04bd041fc4e82b3211d3f841658ed579fefed54 |
| stage_plan.json | 84c388f32824d08b34f2514da6368235f82afa6add75c58d6bab594ff5d6461d |
| runtime_scope.json | fe264b852953b11a61fc6cfc6d4200117de6b7cc1d3a60de7eccaeaf3209d205 |
| backend_descriptor.json | 8585d7b6af5577527e2a704fcb98f990fcd9d8d151f33832d7e627dffd4794f0 |
| independent_verification.json | e54c2980d1e6ed7cdc838918599914f815f5247598173d33d0180c225744b233 |
| closure.json | 9434fa3457b5f57ef13c9dcdb0056db70a50abca533e59d5c99e133814dd19c2 |
| derived_manifest.json | b00780982957952e85598adb870ec2568d19e2d13a51c8c2b5a6c09808449591 |

原manifest覆盖19文件，后验另存不覆盖原；目录23文件374473bytes，另同级日志，全部原始仅服务器。新索引`results/20261030-run-index-hf-orchestration.json` SHA `2eafbb3fd4d5eea887b148180cf93dcc9b4d22922742d58ef3c8fb34bb078475`，旧108run索引不变。

## 解释、收尾与下一步

接口已经连接到**真实HF适配器的代码入口**，lazy加载和stage控制通过软件验证；新适配器尚无真实GPU工程结果，不宣布后端数值/性能通过，也不重写旧生产脚本/总gate字段。FP16/BF16显存节省、吞吐、第二模型与跨任务结果仍未测。

PID934338退出；本轮未查GPU或其他进程，不把旧GPU18MiB/0%作为现测，无服务/依赖变更。代码配置文档与交接同步服务器，GitHub未配置未push。下一步按[接口说明](../HF_ORCHESTRATION_20261030.md)另冻仅14工程输出/0DEV的GPU协议并复核新适配器；当前无GPU运行任务，保护4工程格仍不可行，旧封存16/新封存48不运行。

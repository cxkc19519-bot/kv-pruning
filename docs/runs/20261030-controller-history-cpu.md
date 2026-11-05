# 共享控制器CPU预检v1：断言过强导致停止

后续（2026-10-30）：用户明确继续后，以新目录运行的[v2](20261030-controller-history-cpu-v2.md)54/54通过；本文v1失败、来源快照及原始数据完整保留。下方“修正版未执行/下一条v2”描述的是v1收尾时点，不是当前待办。v2也不证明真实GPU恢复或模型影响。

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；runner开始00:31:29.477（UTC为2026-10-29T16:31:29.477015+00:00）。
- 授权：用户已明确本聊天为实验会话，本轮“开始下一步”承接已冻结的CPU预检；不是从待办自行推导新模型矩阵。
- 执行设备/位置：服务器CPU，`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-history-cpu-v1`。
- 问题：独立CPU参考是否符合已审更新公式、观测mask和状态语义；不是检验真实LLM攻击。
- 来源：自建float64参考，固定官方vLLM0.32.0 commit `5df63a7203cdb9328d824a27b682e77c7b9928be`，不执行作者代码。
- 状态：**failed，按fail-fast停止；32通过、1失败、21未执行，本轮未重跑。**

## 可复现条件

- 本地/服务器项目均未配置Git远端，不声称工作树已有commit。真实执行源码快照SHA256 `8d4400426cab4e8c57f6c3b37c21b2682b76d1b64a2f80427398ff4f5e7e57d9`，服务器`source_controller_history_preflight.py`保存；当前工作源码已改为未执行的revision2，不能用它覆盖v1快照。
- 基础提案`controller-history-preflight-proposal-v1.json` SHA256 `b597611cb56f802e6ea39535f705d62896723b1947ce143860f305dc640221d7`不变，execution_enabled=false作为历史提案保留。执行另存`execution_snapshot.json` SHA256 `c4709fbc1a87cfaacfbdde7de53ccb5289241b608652f6c91c38cab7127ed1ad`，只启用该次CPU参考。
- 上游源码Git blob SHA-1 `f7a4a2f2c1e3221407d12c70cc067cc8cc045bd1`，归档文本SHA256 `12676553ce7f3a6c4dc5c836c2f05cf292e6138b5efd39fdd4638f0ad965a812`；先验Git blob头+内容核验通过。该文本仅读取哈希，未import或exec。
- 实际运行：`/usr/bin/python3`，Python3.10.12，Linux6.8.12；全部Python标准库。初读连接元信息是既有venv Python3.11.13，launcher实际用了系统Python，不能将元信息冒充实际实验环境。未安装/改变依赖，未导入Torch/Transformers/Triton。
- GPU/驱动/CUDA：本轮不使用、未探测；不沿用旧释放记录声称当前空闲。模型/tokenizer/精度：无；无训练/推理输出。
- 合成fixture：54个预定案例，六类（16 dense、15 mask、3 unobserved、4 empty、4 boundary、12 restore）；seed为各类index+314159，输入全由自建runner生成并归档，不是模型采集数据。
- K4、maxreq8、period100、初始slope0.5/bias−0.2、阻尼50、Newton系统L2=0.001、feature截断±40。float64 atol1e-9/rtol1e-8只用于CPU代数；不是GPU数值一致性门槛。
- 界限：最多64fixture、每例256次step、总墙钟60秒、失败即停/无自动重试；无联网、模型、作者代码执行或新依赖。父进程60秒timeout、runner alarm60秒。
- 实际命令（**已执行的历史命令，当前源码已更新，不作为直接复现v1命令**）：

```text
/usr/bin/python3 '/home/user/jhk/project/Directional Exploration/kv-pruning/scripts/controller_history_preflight.py' --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-history-cpu-v1'
```

- 环境覆盖`CUDA_VISIBLE_DEVICES=''`、`PYTHONDONTWRITEBYTECODE=1`，无端口/后台服务。launcher PID352497，runner PID352518，runner exit1；收尾只核查自有runner PID已退出。

## 结果与证据

| 检查族 | 已通过 | 失败 | 未执行 |
| --- | ---: | ---: | ---: |
| dense系统与arrowhead更新 | 16 | 0 | 0 |
| 观测prefix/首拒绝mask | 15 | 0 | 0 |
| 未观测位置/共享slope | 1 | 1 | 1 |
| 空观测轮次 | 0 | 0 | 4 |
| 99/100步边界 | 0 | 0 | 4 |
| 完整恢复/槽位与batch换序 | 0 | 0 | 12 |
| 合计 | 32 | 1 | 21 |

- `unobserved-01`在100次step后触发`assert slope != initial_slope`。参考实现允许负slope更新被拦截，因此每个案例都必须移动的断言不成立。通过的dense案例中5个已触发该防护，不能说所有共享斜率永远不变。
- 事后只对失败归档输入做独立Decimal50位稠密方程复算，未重新执行fixture或runner：观测数`[200,200,0,0]`，原始slope增量−0.6131244947441469，阻尼后−0.5449995508836861，候选slope为**−0.04499955088368614**。源码会拒绝该更新，使slope保留0.5，与断言失败一致。不是误差超过atol/rtol，也不是实际LLM机制反例。
- 运行用时0.053894秒是小型CPU检查总墙钟，不是模型性能。主答案0、工程生成答案0，fixture不计LLM输出；失败后不执行剩余21项。
- 参考输入是配对合成feature/accept-label数据；即使完成全部检查，也不证明实际异步producer/consumer、GPU缓冲/CUDA Graph恢复或真实输入可操纵。尤其本轮完整恢复族未运行，不能报“状态恢复通过”。

全部原始材料只服务器本run目录：`fixtures.jsonl`（32条通过trace，SHA256 `455dfc168035476fcd50bf1f363143ff5a75a25c5ebabf3e00ef88697035b0ca`）、`failure.json`、`failure_diagnosis.json`、源码/提案/上游文本与索引快照、`execution_snapshot.json`、`console.log`、`launcher.json`、`manifest.json`、`verification.json`。事后分析与验证为本run附属物，不作为另一次实验或重试。

失败诊断SHA256 `a69bcaef3bf0a1570687e4bcd5c43402059723a8c36abe851a3f75cff7b48956`；原manifest SHA256 `14414e660aa2e7ead6c1851b9107f3466debf62606b9c1c67e521f1aefbb061d`。7项原manifest文件SHA逐一验证通过；run归档约295KB。自有CPU进程退出，无模型服务需要停止。

累计索引`results/20261030-run-index-controller-history-cpu.json` SHA256 `5be8dd867ed4e16d43b76201d8262ecbc49e78587207799706fc9c97635e2813`：保留旧78项并追加本失败CPU run，**79run、2702主要输出**；不把32通过fixture计成新增答案。

## 解释与下一步

- 直接观察：16个独立dense/arrowhead与15个mask案例通过；第33个案例的断言过强，预检整体失败，后续停止。
- 解释：校验应断言未观测intercept保持不变、更新与含防护的独立oracle一致，而不能要求每个合成案例的共享slope都移动。这是自建fixture的错误，不否定或验证共享控制器研究假设。
- 修正已准备但未执行：当前`controller_history_preflight.py` reference_revision=2，SHA256 `2e7e9c2c6d4ac9cc49a717f56c244b6609aa80a8fa7fcc59cd75f63936a43c81`。同样输入/seed/54fixture/六族/数值与运行上限保留；unobserved族逐例增加独立dense oracle比较、包含负slope防护，保留index0固定movement断言及未观测intercept不变，避免全冻结实现假通过；更早保存失败前后明细。
- [v2修正提案](../../configs/controller-history-preflight-correction-v2.json) execution_enabled=false。下一条是核对这次具体修正后，以新目录`results/20261030-controller-history-cpu-v2`运行同一有界预检，另存执行快照；不能复用/覆盖v1，不自动重试，不进模型。v1基础提案不改。本轮按冻结的fail-fast/no-auto-retry协议停止。
- 仍不支持：真实请求影响、攻击成功、一般安全退化、GPU正确性、全部恢复检查通过或新颖性。
- STATUS/WORKLOG/HANDOFF/PLAN/README已更新，原始结果不下载，代码/配置/文档同步服务器，GitHub未配置。

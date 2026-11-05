# 动作安全guard：恢复后的工程失败与限定诊断

## 实验身份

- 日期/时区：2026-10-28，Asia/Singapore。用户专用实验会话，沿“按建议开始、最长5小时”与继续指令执行；goal恢复active后继续，原22:07:39墙钟上限不延长。
- 服务器根：`/home/user/jhk/project/Directional Exploration/kv-pruning`。三个失败输出目录为该根下`results/20261028-action-guard-full-gate-v2`、`v3`、`v4`（后两者同完整前缀）。首次v1用量停止不覆写。
- 问题：固定动作guard原生Full/NoHistory任务是否有历史支持；先通过原生整段、原生cached、自定义cached三路径逐token一致性。不是裁剪/新方法实验，不执行数据中工具。
- 状态：**三个工程尝试失败；32题能力关卡未执行，task_support_gate=null。当前停止此冻结执行方案，不自动v5。**

## 可复现条件

现有GPU0 RTX4090、驱动580.178.04、Torch2.5.1+cu121/Python3.11.13、Transformers4.57.1；不安装新包。模型`ninty-seven/StepGuard`固定HF revision`c7e4a2c9c34c09efbba0e66a6b802e08b4384662`，服务器`models/StepGuard/<revision>`，原生tokenizer default chat template。实际加载36 Full层GQA，reference prefix KV检查147456 BF16 bytes/token通过。理论配置/权重来源与32个不同交互的数据冻结见[前置记录](20261028-guard-source-and-preflight.md)。本次未新增权重或数据。

原提案`configs/action-guard-full-gate-v1.json` SHA `87e27b706693596587da41c0e248c54fdd865dc7e94e406e8f229b201f995522`不改，execution_enabled=false；每次另存execution_snapshot。cases SHA `a6fb2db4ef05eebd622d5d4ee8afb1393f7c5beaf048820e71e742cc7ded43ab`，同32安全/不安全16/16、四域各8。目标greedy、BF16/SDPA、seed42、max_new512、repetition1、beams1、EOS151645/151643、pad151643。单次工程最多18、主要最多64；未通过首例检查即停止。跨失败尝试6工程输出全部单列，不将其计作主要样本或独立题。

实际命令，分别使用新输出目录，均前台SSH父进程wait，无服务/后台调度：

```bash
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/action_guard_full_gate.py --config configs/action-guard-full-gate-v1.json --out results/20261028-action-guard-full-gate-v2
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/action_guard_full_gate.py --config configs/action-guard-full-gate-v1.json --out results/20261028-action-guard-full-gate-v3
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/action_guard_full_gate.py --config configs/action-guard-full-gate-v1.json --out results/20261028-action-guard-full-gate-v4
```

这些是**已执行失败命令，不是当前待启动清单**。模型文件在每次加载前按官方固定摘要核验；各run源码副本与manifest保留各自版本：v2 runner ef898229...、v3 a279c3ba...、v4 `5965796f0add8d9dff92f1577299fccc44c11493e5a627a74b0c64402955641d`。

## 失败与证据

| run / PID / exit | 实际结果 | 解释与处理 |
| --- | --- | --- |
| v2 / 3508791 / 1 | 模型加载并prefill，0工程/0主输出；Inference tensors do not track version counter | 自有runner读取reference tensor._version不兼容inference_mode；reference prefill改no_grad，保留版本完整性检查。 |
| v3 / 3512213 / 1 | 首例3工程输出，整段224/cached191/custom210 tokens；0主输出 | 安装的HF `_prepare_generation_config`把等于全局默认的False回退成模型do_sample=True，原生两路径实际采样。3条均无效，不是缓存错误的证据；CPU用同安装方法复现auto=true/use_model_defaults=False=false，源码和failure_diagnosis归档。 |
| v4 / 3516113 / 1 | 显式use_model_defaults=False，effective_generation_config验证greedy；首例整段192/cached210/custom210 tokens；0主输出 | cached/custom所有210 tokens相同；整段与两者前53相同，索引53（第54 token）分叉。原三路径门槛失败，停止正式队列。 |

失败首例`slack/3/3/16`，条件Full；原prompt1481tokens，prefix1263，分界前后原ids不改。所有三个工程路径EOS结束，不是max_new截断；未进行三首例全部18工程或64主输出。没有计算32题正确率、false-clear率或历史依赖门槛，不把工程失败当任务能力失败。

限定附属诊断命令（已执行一次，180秒上限、实际约6.4秒含加载，**不是性能结果**）：

```bash
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/diagnose_action_guard_prefill.py --run results/20261028-action-guard-full-gate-v4
```

脚本SHA `3a905fd4ed5c98b43e8c3e75bcd944a5fad77c2d067f38887c6ff5bc34a8c41f`。只重放原有53个共同token，不进行generate或生成新答案；PID3520359 exit0，逻辑位置/长度相同，前54步argmax与原记录全部复现。第54步整段token7600为18.375、token2530为18.25；cached二者同为18.25并选2530，整向量max_abs0.15625。比较prefix K/V，第0层相同，第1–35层有数值不同；最大绝对差19.828125，不能把所有差异轻率称为“微小舍入”。完整逐层/逐步证据保留`prefill_diagnostic.json`。

该证据表明该固定BF16/SDPA实现的整段与切分路径在相同逻辑位置下确实不同；没有单独隔离特定kernel、精度或实现原因，不能声明已证明“纯浮点舍入”。不以两个cached路径相同替代预定三路径要求，不换attention或FP32来过线。`prior_gate_remains_failed=true`。

## 结果账本、资源与下一步

每run保留proposal/source/cases/weight_checks/execution_snapshot/generation_config/manifest/原始engineering（如有）/console/launch/stage_outcome/closure，v3保留安装框架源码片段与CPU诊断，v4保留effective config与teacher-forcing诊断。closure逐文件SHA已核对；原始数据只服务器。本次0主要输出、6工程输出；累计78run2702主要输出，本窗口19run。新索引`results/20261028-run-index-research-window-resumed.json`保留旧75项并追加3次失败；诊断附属v4不重复计run。

资源证据`results/20261028-research-window-resumed-resource-closure.json`：四个自有PID均不存在、两卡15MiB/0%、compute-app空。未创建服务/tmux/端口/计划任务，未从nano-vllm复制，未变更环境依赖。

当前**不启动能力队列或压缩**。A已有方法归约no-go，C直接近邻不立题；本guard用途仍缺任务支持与新颖性证据。后续若独立修订设计，先处理可审计的数值可比性与强基线问题，不能直接删除三路径断言后称原协议通过。预备`analyze_action_guard_full_gate.py`（SHA356e7ec0...）未执行/未验证，仅适用于完整64输出，不将其当本次审计证据。STATUS/WORKLOG/HANDOFF/PLAN/窗口结论及父ENV已更新；同步以最终SHA核对为准。

# 固定动作安全guard Full-only关卡：因会话用量停止

**后续恢复已执行，当前不要再按文末恢复指令启动。** 新目录v2/v3/v4共0主/6工程输出，最终工程一致性失败并限定诊断；当前停止此冻结执行方案，task_support_gate=null。最新记录见[工程失败与诊断](20261028-action-guard-engineering-failure.md)。下文完整保留最初v1用量停止事实。

2026-10-28，Asia/Singapore；用户授权研究/实验持续推进。服务器绝对路径`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-action-guard-full-gate-v1`。目的是检验原生历史依赖，不是新压缩方法。

实际命令（服务器方向根，前台父进程wait，GPU0可见、HF离线）：

```bash
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/action_guard_full_gate.py --config configs/action-guard-full-gate-v1.json --out results/20261028-action-guard-full-gate-v1
```

提案SHA87e27b706693596587da41c0e248c54fdd865dc7e94e406e8f229b201f995522；runner ef8982291172bcf178fc73497b093fa743cfb4a1c960f22618070138540a3fea。32个固定交互case SHAa6fb2db4...；StepGuard固定c7e4a2c...，greedy/BF16/SDPA、max_new512、seed42、原生default chat template、两EOS151645/151643。模型加载前须校验全部固定文件；首3×2×3路径最多18工程，全部通过才64主输出。

平台goal报告`usageLimited`后，核实/proc命令为自有runner PID3368363并SIGTERM，父进程wait退出-15。停止时仍在加载前预检，0主要输出、0工程输出、无execution_snapshot；model_execution_snapshot_created=false、task_support_gate=null。未完成模型加载、缓存对照、Full能力或NoHistory支持检查，不得称失败gate或通过。

manifest原快照、session_limit_stop、源码/提案/console/launch/closure保留；无generations。没有OOM或性能结果。收尾compute-app空、两卡15MiB/0%，没有遗留本run进程或服务。累计75run2702主要输出，索引`results/20261028-run-index-research-window.json`。

恢复须用新输出目录沿同一冻结方案，不覆写停止run；先核对GPU和源SHA。预定Full≥24/32、两类各≥12/16、32唯一完整Judgment、0error/截断；Full对/NoHistory错至少8，其中unsafe被NoHistory误放行至少4。失败停止此设计，不换模型/提示/长度/seed。NoHistory改变输入及位置，不是KV裁剪；通过也只支持进入另行设计，不自动授权或证明新方法。当前准确断点见[窗口结论](../RESEARCH_WINDOW_20261028.md)。

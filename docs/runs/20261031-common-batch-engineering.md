# 共同批量后缀工程：通过

## 实验身份

- 日期2026-10-31，Asia/Singapore，Codex；用户“开始下一步/继续”推进已授权实验。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-common-batch-engineering-v1`。
- 来源：新操作流程的工程验收，只有原2工程组；不含开发模型调用或新科学样本。
- 状态：worker/独立validator/归档cap全部通过；旧整段/分段数值gate仍failed。

## 可复现条件

- 无Git/远端。[契约](../COMMON_BATCH_CONTRACT_20261031.md)、12 source/input与原生工件SHA先冻结，[配置](../../configs/common-batch-engineering-v1.json)自身SHA `3f148a80732b72af9357ffe091cf06cbddb057095312ada5ce7dba4219fbf620`。
- 固定Qwen2.5-7B revision a09a35458c702b33eeacc393d103063234e8bc28，4权重/7metadata/原Torch2.5.1+cu121与Transformers4.57.1；BF16/SDPA/TF32off/seed20261030。GPU1空闲检查，未操作GPU0任务。
- 原373 prefix/24 suffix，显式bool full_attention字典mask，逻辑位置373..396/物理Full373或compact186。新研究对象是固定缓存运行过程，不声称397整段计算等价，不按新阈值改判旧失败。
- 实际命令：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_common_batch.py --execute --registration-sha256 3f148a80732b72af9357ffe091cf06cbddb057095312ada5ce7dba4219fbf620
```

## 结果与证据

- 2工程组，Full+8候选各正序/反序重复，18状态/36末token分布逐字节一致，四目标KL精确重复。候选为prefix-only WindowScores64/kernel5跨28×4均值适配Snap1/recency1/6固定随机；不是原作者per-head SnapKV复现。
- hook/nohook prefix cache和logits逐值相同、原hook集合恢复；所有prefix reference始终不变；每候选186槽/锚点68/free118，真实bytes与gather一致。
- 保存实际两种bool mask字节，调用后未变，独立逐行复核因果可见集合；所有1008 suffix SDPA显式mask/GQAfalse/28KV头，真实CPU父链下efficient backend证据完整。未强制后端或调整精度。
- 独立stdlib重算28×4分数平均/所有候选、1008 K/V tensor字节与gather、36分布重复性/72 KL值、40 forward/2356 teacher-forced输入token/4HF编码、4权重7metadata。
- worker1431879内113.692805秒、verifier1433053内32.226565秒、launcher1431874共150.833239秒exit0，三个PID均退出。guard违规全0，精确拒绝的urllib3 IPv6探测另计；无运行内外联/安装或生成token。
- 107文件260708228bytes/cap128与512MiB，先检查cap再写complete；manifest `54c45209ab4dab7278b161d6c68743246cbef1286daf417cd8983561f45375f2`全部回读。
- 累计此阶段131run3038主，新索引`results/20261031-run-index-common-batch.json` SHA `92bb68ed1cda7e91012f927a23f6c1b8811e296241a72c74ae2c3fb6f0ab304a`；36工程logits不当主要完整答案，不覆写旧索引。

## 解释与下一步

共同固定流程的selector/gather/评分链和工程组同路径重复性已通过，不能推广为所有新输入的误差界或整段原生模型等价。原0.25/0.001 gate、旧QA/Mistral false及所有历史失败保留。

用户“继续”后已据此另冻[固定12组开发筛查](../DECODER_H3_SCREEN_PROTOCOL_20261031.md)：先Full≥10/12，才8候选；不据工程分数调题/seed/预算。该后续run单独记录，不把本2工程组算进12样本。源/结果只服务器，代码配置文档同步，GitHub未配置。


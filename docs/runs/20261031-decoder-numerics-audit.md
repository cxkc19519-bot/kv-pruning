# 同前缀数值/源码离线审阅：计算完成，归档上限失败

## 实验身份

- 日期/时区：2026-10-31，Asia/Singapore，Codex；已有服务器Python3.11.13。
- 用户任务：授权实验会话“开始下一步”，只分析已存工程工件和运行时源码。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-decoder-numerics-audit-v1`。
- 类型：事后探索性数值/软件源码审查；不是新模型/数据/压缩效应实验。
- 状态：**worker与独立validator exit0；整体run因归档44文件>40上限exit1，仍记失败。** 旧工程门槛保持failed。

## 可复现条件

- 无Git/远端。三脚本和[协议](../DECODER_NUMERICS_CPU_PROTOCOL_20261031.md)、16既有工件与4个已安装HF文件逐SHA冻结于[登记](../../configs/decoder-numerics-audit-v1.json)，登记自身SHA `c207dbd8fb0ca2f1e7dfcef9b647e7bfba6c8628905143ae8a419493a11c2095`。源码CAS同步/静态compile通过后仅执行一次。
- 输入为旧第一工程组7 f32分布/56 trace及maps/runtime，不读取模型权重、执行Torch/Transformers或tokenizer。
- 标准库AST只执行4个精确提取函数对shape stub的逻辑；无真实张量/模型操作。CUDA/nontracing/all-ones/DynamicLayer假设明确标注，不把源码预测当GPU kernel记录。
- 实际命令：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_decoder_numerics.py --execute --registration-sha256 c207dbd8fb0ca2f1e7dfcef9b647e7bfba6c8628905143ae8a419493a11c2095
```

- 父进程另抓2份官方v2.5.1来源，2HTTP200、共246778bytes，无重试；版本docs网页访问失败后使用官方固定tag raw文件入口，未据失败作事实推断。
- worker90秒、validator60秒、outer180秒；原归档上限40文件/8MiB不变。

## 结果与证据

- [结论与比较合同](../DECODER_NUMERICS_REVIEW_20261031.md)列完整数值。56 source replay行：51None mask/native GQA、5显式mask/repeat KV头，3 is_causal=true；1287query行可见历史集合按源码/记录值一致。没有现场mask或kernel，因此不能证明自动分支切换是全部误差因。
- 4对×global/allowed八scope概率指标复算，合法KL另以Decimal60位核对。Full两对global TV约3.64e-12/4.81e-12；random约1.46e-10；recency约0.01673、allowed约0.00042567。所有argmax相同，不能据此认证KL排序。原7分布确实落在BF16网格，不推出BF16是唯一根因。
- worker1405845内1.692507秒、verifier1405867内1.498305秒exit0，launcher1405785耗时6.335650秒，原summary先写complete但随后file-cap抛错exit1。已用closure明确整体失败；三PID均退出。
- 原44文件4841616bytes，超过40文件但低于8MiB；我的登记漏算了归档快照项。未删除工件、调上限、覆写manifest或重跑计算。追加closure/derived后46文件4846935bytes。
- 原manifest `a0dec76b627291963f2f0880d2698f37cfcefcbc995255322f849f46b2c4057e`；derived `75f431abb9ae396879950d7438f917a4d7743de4a529c54bafb36d73f1135876`；新索引`results/20261031-run-index-decoder-numerics.json` SHA `43ddc7a0d02449c89b1333ef166d7ad394aec3b2ed925eb53288ea666e9181c2`。
- guard全0，新增1CPU run（file-cap failed）/0模型/GPU/编码/权重/依赖变化；累计125run3038主，不把既有logits算新答案。原始来源/输出只服务器，本地只代码配置文档。

## 解释与下一步

工程路径数值可比性仍未闭合；已定位一个需要现场确认的mask/GQA分支差别，未见记录层面的明显因果历史集合不等。原阈值不改，旧工程false/H3未测/12DEV未启用。并未建立数值漏洞、压缩新算法或新颖性结论。

下一条操作为：实现透明SDPA参数/后端记录器，先CPU验证原参数/对象不变与恢复；修正未来runner在标记complete前计算归档上限的流程，历史run不重写。然后另冻仅2工程组的有界观测协议，不直接切后端/放宽门槛/运行12DEV。STATUS/WORKLOG/HANDOFF/readiness同步两端，无运行任务，GitHub未配置。


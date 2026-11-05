# H3同前缀KV工程：两次失败，主实验停止

## 实验身份

- 日期/时区：2026-10-31，Asia/Singapore；Codex，服务器当前实验会话，用户“开始下一步”。
- 绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-decoder-kv-engineering-v1`及`.../20261031-decoder-kv-engineering-v2`。
- 来源：自建同前缀KV工程验证，不是主研究效应/新方法实验。
- 状态：**v1导入封装失败；v2冻结数值门槛失败。第二工程组及12开发组0模型调用，当前无GPU队列。**

## 可复现条件

- 无Git/远端。新后端/worker/标准库完整validator/launcher与[协议](../DECODER_KV_ENGINEERING_PROTOCOL_20261031.md)先冻结；v2仅[临时目录修正](../DECODER_KV_ENGINEERING_V2_ADDENDUM_20261031.md)另登记，不改v1或阈值。
- v1登记SHA `a1b06dc8e82e2e98aa4af2c5027b9a81201d0004712dd6bf244fffda498d2455`；v2 `2fa46618b4b7d123ac30a8aab3e2317ece939539affb8d5bd6e1bbbfe5b6e10c`。
- 固定既有Qwen2.5-7B revision a09a35458c702b33eeacc393d103063234e8bc28，4权重/7metadata SHA、Torch2.5.1+cu121/Transformers4.57.1、BF16/SDPA/TF32 off；GPU1 UUID固定，加载前空闲used≤128MiB/util0。GPU0有他人进程，未操作。
- 输入沿CPU冻结的新2工程组，prefix373/suffix24/半预算186/锚点68；12开发组不用于模型调用。六seed先冻2026103101–06，工程随机只首seed。
- 实际执行命令（均已退出；同run不可覆盖重跑）：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_decoder_kv_engineering.py --execute --registration-sha256 a1b06dc8e82e2e98aa4af2c5027b9a81201d0004712dd6bf244fffda498d2455
.venv/bin/python -B scripts/run_decoder_kv_engineering_v2.py --execute --registration-sha256 2fa46618b4b7d123ac30a8aab3e2317ece939539affb8d5bd6e1bbbfe5b6e10c
```

## 结果与证据

v1在Torch→torchvision→distributed导入的tempfile系统目录可写探测中被run外写入guard拒绝，worker1398285内21.708571秒/launcher1398280共22.371169秒exit1；0编码/forward/logits。报错外层是Qwen2ForCausalLM ModuleNotFoundError，完整栈确认是我方运行封装而非依赖缺失或模型不支持，未安装/升级依赖。允许的urllib3 IPv6能力probe被拒绝1次单列，网络0。

v2把TMPDIR与tempfile.tempdir固定在run/runtime-tmp，保持原guard。实际28 Full/GQA4/head128/BF16/SDPA与4权重/7metadata核对，4次AutoTokenizer工程编码重现输入。第一工程组计算完成56 forward/1287 teacher-forced输入token/7条归档末token分布，0完整答案/生成token。第二工程组只做此前编码核对，0模型forward。原缓存21389312bytes、两种半缓存各10665984bytes，gather/clone值与reference不变的现场检查通过。

| 第1组路径比较 | 最大logit绝对差 | 全词表KL | 合法KL | 全/合法argmax集合相同 | 冻结门槛 |
| --- | ---: | ---: | ---: | --- | --- |
| whole / full batch | 0.5625 | 7.08e-13 | 7.03e-13 | 是/是 | 失败 |
| whole / split full batch | 0.4375 | 1.25e-12 | 1.23e-12 | 是/是 | 失败 |
| recency batch / tokenwise | 0.5 | 0.0025013213 | 0.0000262600 | 是/是 | 失败 |
| random batch / tokenwise | 0.5 | 2.74e-11 | 2.43e-11 | 是/是 | 失败 |

固定要求max error≤0.25、全/合法KL各≤0.001且两类argmax集合相同。四对均超max error，recency还超全词表KL。故即使argmax一致也不能报工程通过或开展KL排序主实验。v2 worker1399346内23.757826秒/launcher1399341共24.478085秒exit1，guard违规全0（另有1次拒绝的精确IPv6 probe），完整validator未启动。

独立CPU事后审计[源码](../../scripts/audit_decoder_kv_failure.py) SHA `7c1cd9960ca443a60f97b313ba07a3674793bf73c0bdde1a86ca3061f34d5d1f`另先冻结执行：不import Torch/NumPy/项目模块，从7条二进制f32分布重算4对错误和失败；从3份原始BF16快照重算168 tensor摘要、两种逐head gather的全部bytes与reference hash，重建56次位置/输入/mask trace。全一致，未改变failed状态，0新模型调用。postmortem报告与源码副本作为派生工件追加，原manifest不改。

误差概率质量说明：whole/full batch差>0.25的107个词项，在reference路径上总概率约1.08e-11；split full的43项约1.16e-18。recency两路径差>0.25的279项总概率约0.03971/0.03065，因此不能把全部差异都简单归为不相关词项。这里只分析**同一掩码的数值路径**，没有比较不同掩码的压缩目标排序；尚不能归因全部来自BF16、内核或mask实现，也不是H3证据。

- v1归档23文件360431bytes；原manifest `c363fd08a19ab19f721dc737307efad57f919edbb28a5c3d2aabdbac044cd168`，derived `0ea8fdb8f23631ebd17eabdef5617e49cee7a2abbf94083cd2e54b874c799ad5`。
- v2归档42文件47463000bytes；原manifest `07c356f3313648513d2a9d9dbd3f1f684f6717c46faba8ea67051e4565c32936`，derived `6ee5a8182b7a3fd4b1371b14070f3f23cc0d1705289ce6b5660fb8c9e0474a8c`。
- 两原manifest/全部原与派生文件回读；raw缓存/logits/失败日志仅服务器。临时目录清理后无残留文件。
- 新增2个失败run，累计124run3038主；新索引`results/20261031-run-index-decoder-kv-engineering.json` SHA `4dc414b39a37d2092f803f10e032dbf081798735deb32eca9ed60cd52ceedba9`，原34c0b953…不覆盖。7条工程logits不是7个新主回答。
- 四PID均已退出，GPU1收尾18MiB/0%，无后台任务。无安装/下载/环境升级、阈值放宽或第三次GPU尝试。

## 解释与下一步

直接结论是：物理gather在已算第一组的归档字节上正确，但新入口未达到预定数值可比标准；不能称工程已验证或真实KV目标失配成立。也不能从这次工程失败否决整个H3方向。Full12能力、Snap选择器工程、实际目标排序和研究增益均未测；旧QA/Mistral false与旧停止队列保持。

下一步仅用现有工件与固定源码离线审查数值可比性：分离低概率词项max-error与recency分布误差，核对causal mask/位置与BF16路径假设，形成有依据的比较合同；在此之前不开12组或第三次GPU，不按结果调阈值。STATUS/WORKLOG/HANDOFF与readiness同步两端，原始仅服务器，GitHub未配置。


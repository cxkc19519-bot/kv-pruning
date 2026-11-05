# 阅读+JSON：原生边界、Full与等预算裁剪的自动可行性筛查

## 实验身份

2026-10-30，Asia/Singapore，服务器`jhk@121.48.164.89:1100`。用户明确本会话可运行实验，本轮追加“本步后自动下一步，直到得出方向能不能做的结论”。按输出前冻结的decision contract逐阶段推进，当前已停止于DEV确认门槛false；不是等待用户逐阶段点击。

四个服务器绝对目录均在`/home/user/jhk/project/Directional Exploration/kv-pruning/results/`下：

| run | 状态/时长 | 主回答 | 工程回答 | 原manifest SHA256 |
| --- | --- | --- | --- | --- |
| 20261030-answer-format-tokenizer-v1 | complete /1.429293秒 | 0 | 0 | 782c006937456a42ea5b2017aa5df2d319f0314e896df62a339ca8fea68300b3 |
| 20261030-answer-format-full-v1 | complete /57.377213秒 | 16 | 6 | 340d5d8cbc653ad2414d0eb5851c22eb3558bdab3406ba7f652ed2e473b95de0 |
| 20261030-answer-format-compression-v1 | complete /52.446748秒 | 64 | 16 | b34a83d4a93bbd64f55390c1c5f0b812c35436f285050665263ea112deab5f23 |
| 20261030-answer-format-analysis-v1 | complete /0.029109秒 | 0 | 0 | 6c7d5549b3bdafbdb66a5c4b50a0dc4571aa9308069171da2beb8751a429aed0 |

新增4run、80主/22工程，共102回答1687tokens（主1118、工程569），无失败run，随机主输出1条截断原样保存。累计99run2812主输出，四压缩条件同16开发上下文，不是80独立题。

## 可复现条件

固定新任务原始数据/划分/输入不变，来源见[前CPU预检](20261030-answer-format-task-preflight.md)。输入selected SHA `ccf4866f…`、原契约`3af39d6b…`保持。工程2/开发16参与当前模型运行，16封存题无推理或调参。原始数据、权重、日志、输出仅服务器。

| 项目 | 固定值 |
| --- | --- |
| 原生模型 | Qwen/Qwen2.5-7B-Instruct revision a09a35458c702b33eeacc393d103063234e8bc28；既有HF cache，无下载 |
| 框架 | 原`.venv`：Torch2.5.1+cu121、Transformers4.57.1、tokenizers0.22.1、safetensors0.6.2，未安装/升级 |
| 架构与精度 | config及实际加载28 Full Attention层，GQA4 KV heads、head_dim128、全部BF16；K+V57344bytes/token，无滑窗；SDPA |
| 权重身份 | 4 shard逐文件SHA256匹配Full/压缩各自proposal中固定LFS摘要，weight_verification.json保留 |
| 设备 | CUDA_VISIBLE_DEVICES=GPU-4ce22e12-b5c0-e423-06c5-e858bb71daaa，物理GPU1/RTX4090；加载前须memory<=128MiB且util=0，实际18MiB/0% |
| 解码 | greedy、beam1、max_new_tokens96、repetition_penalty1、EOS[151643,151645]、pad/bos151643、TF32关闭；fresh GenerationConfig显式替换model generation defaults，actual全字典保存 |
| 裁剪 | query-blind prefix，问题与原生suffix完整保留；半prefix floor预算，sink4/recent64；适配Snap window64/kernel5或固定random seed20261028；随机key用context_group_id而非gold/query文本 |
| 保护 | 完整native system消息含边界56tokens；与anchors并集120槽位，同预算扣除，不pin原文答案 |
| 长度 | 18工程/开发输入prefix285–852，budget142–426；tokenizer44次编码与两工程题各两个替代问题prefix稳定 |
| 运行上限 | tokenizer90秒/0生成/无torch；Full600秒/16主+6工程；压缩900秒/64主+16工程；分析outer60秒/6软件fixture/0生成。GPU run归档128MiB/256文件；CPU32MiB/32文件 |

原冻结提案的false/未实现字段不追写，实际执行均另有execution snapshot或source/proposal快照；不得重跑既有目录。分析输入manifest pin只能在生成结束后登记，科学门槛的decision contract SHA `3baf6b98…`则在新Full输出前已冻结，未按输出调阈值。

历史执行命令（均已执行，不是新队列）：

```bash
.venv/bin/python -u scripts/preflight_answer_format_tokenizer.py --execute
.venv/bin/python -u scripts/run_answer_format_model.py --proposal configs/answer-format-full-proposal-v1.json --execute
.venv/bin/python -u scripts/run_answer_format_model.py --proposal configs/answer-format-compression-proposal-v1.json --execute
.venv/bin/python -u scripts/analyze_answer_format_direction.py --proposal configs/answer-format-analysis-proposal-v1.json --execute
```

各launcher使用自有foreground子进程、独立`.launch.json`/`.console.log`、比内部上限略长的outer timeout，均exit0，未触发kill/重试。单文件配置部署曾在写入前因JSON对象/数组封装错误拒绝，修正传输封装后才启动实验；未形成失败模型run或覆盖工件。

## 正确性与结果

Full工程2题×原生整段/原生分段完整KV/custom分段完整KV共6回答，逐token一致；有/无scoring hook的prefix K/V逐值相等。Full开发16输出中EM12、格式16、candidate16、零截断，原最低支持门槛通过。

压缩工程2题×4方法×native/custom共16回答，逐token及位置trace一致。逐层实际gather K/V与原缓存指定位置逐值一致、形状/dtype/字节预算核对；reference指针/版本保持。四方法的每题压缩prefix字节相同，原始RoPE逻辑位置与紧凑物理cache位置分开，score/map全部归档。每个DEV prefix和score与Full阶段hash相同，控制了新旧运行输入与prefix特征漂移。

| 条件 | EM正确/计划16 | 格式通过/计划16 | F1均值（适用分母） | Full→压缩任务损坏/改善 | Full→压缩格式损坏/改善 |
| --- | --- | --- | --- | --- | --- |
| Full | 12 | 16 | .8253 (16) | 0/0 | 0/0 |
| 适配SnapKV | 4 | 3 | .4014 (16) | 8/0 | 13/0 |
| random | 8 | 8 | .6276 (15) | 4/0 | 7/0，另1不可比较 |
| Snap+system保护 | 5 | 15 | .4518 (16) | 7/0 | 1/0 |
| random+system保护 | 5 | 16 | .5936 (16) | 7/0 | 0/0 |

随机那1条96token截断、结构无法解析，任务N/A；原Full任务错，不计成任务C2W或成功。格式仍保留原false值，但严格配对排除截断，列N/A1；格式损坏严格7/15，覆盖范围[7/16,8/16]。任务Full正确分母12全部可评估；所有零分母、未知、缺cell都有单独状态，未补0。F1也是词面代理分，不代替语义真值。

直接无保护→保护：Snap格式修复12条；任务1条C2W、2条W2C（净+1）。随机格式修复7可比较条，1截断项另记；任务3条C2W、0条W2C（净-3），另1不可比较。这说明保护收益须与任务代价、覆盖一起看，不按净分冒充逐例无损。

预定DEV signal gate=false：全条件未截断/可比较的必要条件被随机1截断打破，随机保护task净损失3也超过2。Snap数值支路虽有信号，不事后单独挑作过线子集。所有计划80cell在report.json保留，16封存确认未运行，未换题/提示/预算/seed/模型或重生成截断题。

## 复核与归档

新增标准库配对分析器通过6软件fixture：净分相抵、指标未知、零分母、截断、缺cell、重复硬拒绝；它是本任务adapter，不是跨模型通用系统已验证。报告SHA `e1d2422497d1110b6f3969528997c9d416ba3adbf741b658dec8273f211404f5`。

外层独立检查8064个head映射的唯一/排序/anchor/保护/预算，适配Snap从原score另排序重建，18组Full/压缩score压缩工件逐hash相同；80主输出prefix/最终KV字节及每步逻辑/物理位置核对、四转移/分母/覆盖范围和无保护→保护变化另行Counter重算。独立verification SHA `5aab9e2b…`、closure `b9d056c7…`、分析derived manifest `c4c8d1cd…`另存，原四阶段manifest不改。

所有原始JSON/JSONL、ids/text、score/map gzip、trace、模型文件摘要、来源/版本/snapshot、异常/截断都在上述服务器目录。该实现为审计仍保留完整prefix reference再gather，未测纯推理峰值/额外buffer/吞吐/延迟，不能把半prefix字节写成整进程显存减半。运行wall含加载/权重hash/trace与归档，不作推理速度。

自有PID844997/848885/850627/853182均退出，GPU1收尾18MiB/0%，其他任务未操作，无端口/服务/持续任务。旧9输入与被复用脚本保持SHA；新索引`results/20261030-run-index-answer-format-direction.json` SHA `11d49a0bb4c4e5c5b9bdb7d8cfef4d6a1c7d7d9bf8f6f230461675d9118ade8e`，旧95run索引不改。

## 解释与下一步

完整结论见[可行性判断](../ANSWER_FORMAT_FEASIBILITY_20261030.md)。工程路线可行，开发集有真实格式/任务差异；但当前单任务自动确认失败，不能宣布独立复现成功、策略普遍更好、安全损害、新算法创新或足够毕业。保留系统/实证路线作为讨论建议，不将本单任务单独成题。现在停止自动GPU矩阵；后续先开题/系统验收设计，任何独立验证须新协议，不能追改本关卡。

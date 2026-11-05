# H3固定12组筛查：执行完成，开发决策no-go

## 实验身份

- 日期2026-10-31，Asia/Singapore；Codex；用户授权实验会话“继续”。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-decoder-h3-screen-v1`。
- 来源：一个新假设的受控合成开发筛查，非新算法/确认集/自然任务benchmark。
- 状态：**执行及独立验收完成，development_go=false**；科学负向结果不是工程run失败。

## 可复现条件

- 无Git/远端。[执行协议](../DECODER_H3_SCREEN_PROTOCOL_20261031.md)/评分/worker/validator及共同batch后端SHA先冻结，[登记](../../configs/decoder-h3-screen-v1.json) SHA `287f9260806a3f8ee6883fa66d050a0b98c70658ebde58fcb75a8978f12b0961`。
- 前置原2工程组共同batch验收完成，结果单独记录；既有12开发组身份/order/prompt/gold/373+24原生IDs/位置标签平衡固定，未换题补样、未按效果改seed/预算。
- Qwen2.5-7B revision a09a35458c702b33eeacc393d103063234e8bc28，4权重/7metadata、Torch2.5.1+cu121/Transformers4.57.1，BF16/SDPA/TF32off/seed20261030，GPU1固定UUID/空闲检查；无安装下载。
- 实际命令：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_decoder_h3_screen.py --execute --registration-sha256 287f9260806a3f8ee6883fa66d050a0b98c70658ebde58fcb75a8978f12b0961
```

## 结果与证据

- Full12合法分支argmax正确12/12≥10，随后按原8候选完整计算96向量，不挑Full正确子集或最好seed。每个候选物理186prefix槽/68锚点，重新计算相同query+wrapper，Full后缀KV不注入。
- prefix缓存/score/maps在Full与候选阶段hash完全重复，数据/评分不改。候选8个：prefixWindow64/kernel5跨28×4均值适配Snap、recency、Random2026103101–06。
- 全4目标所选缓存均保留12/12 Full合法argmax，gold12/12。11/12组任意候选成对排序发生实质反转（global/Top128/Top256相对legal各11组），但legal相对每基线0win/0loss/12tie、0模糊保真近并列；go=false，停止当前候选不扩展。
- 各固定候选Full保真：Snap10/12，recency8/12，六随机6/9/9/9/6/7；不是所有压缩无害，也不是六seed独立确认。选中的缓存分数用Full参考计算，是oracle诊断而非部署selector。
- 独立标准库validator从108 f32向量重算384 KL/argmax、12Full门槛、候选score聚合/mask、132 trace/11544输入token、全部选择/赢平输/停止线，4权重7metadata回读，verified=true。
- worker1450114内91.565906秒、verifier1451208内22.934665秒、launcher1450109共115.538293秒exit0，三PID退出；guard违规全0，1次精确拒绝的IPv6能力探测单列。24HF编码，0完整生成/自由JSON答案、无安装/运行内外联。
- 原封口164文件68140344bytes，manifest `256b9fd679a6c758d7981807fe29ac6efbf24f51ec3a58e13020f2ef46b1b8fb`；追加semantic_closure/derived后166文件68159219bytes，derived `fbfa685dbadca670c2c5c2e1273714bdea02689400586b5fef5f425811be2735`。原文件/原manifest不改。
- launcher初始化real_KV_signal_observed=false未更新，已用semantic_closure明确真实排序反转已观察true、研究收益/go false；此字段不作为否认现象的证据。完整原始向量/分数/差题保留服务器，不回传本地。
- 新增1GPUrun/108诊断向量/12组分支Full与候选决策，0完整生成答案；累计132run3038主，新索引`results/20261031-run-index-decoder-h3-screen.json` SHA `b0c4d8fda03a662a5a30ccde9af934846bf45d7f73e2c06df546a2db9339f475`，原92bb68ed…不覆盖，GPU1收尾18MiB/0%。

## 解释与下一步

[决策文档](../H3_SCREEN_DECISION_20261031.md)明确当前H3不继续作为主贡献投入：数学可能性在真实KV中出现了，但没有超出generic KL/TopK的决策保真改进，预定go线不通过。限当前12合成开发组/一模型/半预算/首语义分支，既不推出所有任务无效，也不据此救回或宣称论文可行。

按协议终止本候选，不增难prompt/样本/seed/预算/模型搜信号，不开始独立确认或方法训练。已有系统、共同batch契约与原48技术报告保留，旧数值失败/QA/Mistral false保持。STATUS/WORKLOG/HANDOFF/readiness更新同步，当前无自有运行任务，GitHub未配置。


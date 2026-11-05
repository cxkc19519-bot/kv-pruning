# H3真实tokenizer与新输入CPU预检

## 实验身份

- 日期/时区：2026-10-31，Asia/Singapore；Codex，已有服务器Python3.11.13。
- 授权：当前实验会话，用户“开始下一步”；按冻结的CPU协议执行一次。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-decoder-native-preflight-v1`。
- 来源：受控合成检索、真实固定tokenizer的工程预检；不是新算法、自然任务基准或真实模型效应实验。
- 状态：**完成，worker与独立validator均exit0**。

## 可复现条件

- 无Git仓库/远端。四个新脚本与上一轮已验模块、[CPU协议](../DECODER_NATIVE_CPU_PROTOCOL_20261031.md)六source SHA及两配置input SHA在[登记](../../configs/decoder-native-preflight-v1.json)冻结；登记SHA `d7d2edcd9aca343c919393bd05c2d1720a0b58a80dc6d523972cc19cb834cc01`。同步7文件CAS/SHA和Python静态compile通过后执行，之后源码/协议不改。
- Qwen2.5-7B-Instruct revision a09a35458c702b33eeacc393d103063234e8bc28，6 metadata与chat-template摘要核对；不读取权重。实际raw config没有layer_types，依据固定Qwen2结构/use_sliding_window=false作布局预测，历史GPU验收不自动覆盖新入口。
- tokenizers0.22.1/Jinja2 3.1.4；使用原模板system/user无tools支路、backend整段编码，无Transformers/Torch导入，无新增依赖。
- 新2工程+12开发组，12组为位置首/中/末×答案A/B/C/D；生成器先于任何编码/模型结果冻结，未读旧48/16。每组24事实，都是合成诊断，不声称12个语义独立自然来源。
- 实际命令：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_decoder_native.py --execute --registration-sha256 d7d2edcd9aca343c919393bd05c2d1720a0b58a80dc6d523972cc19cb834cc01
```

- launcher1392624、worker1392627、verifier1392628，exit0并核退出，无后台服务/端口。

## 结果与证据

- `selected_cases.json` SHA `b5de283f7a843bdae2f33e7279d183b4b3ef3fd1b681a8aad275d1fd9b95a5f6`；`native_inputs.json` SHA `7a42861fc0954638f7bdc6bab49d70952d994eaea90551d894f2e4cb96731120`；完整输入/IDs/gold只服务器。
- 原native与native+非gold wrapper每组各编码一次，共28，另6个NFC/UTF-8 probe，总34编码。metadata实际NFC normalizer已按输入文本/生成raw byte分离验证，未假设孤立token decode等于bytes。
- 151643 base词项/22 added项及256单字节覆盖；原vocab.json与tokenizer.json一致。模型额外399个无tokenizer词项的行禁止作普通语法token。
- 33个相关词项组成有限JSON语法，独立validator从整个base词表枚举，49条边全部相同；四个完整输出可达，EOS151645仅在完整输出末端可用。首语义分支合法token实际为32/33/34/35，对应单字节A/B/C/D，唯一确定标签。此为本次实测，不是预先假设标签单token；额外控制项全部被普通路径排除。
- 14组prefix均373、query+wrapper suffix均24，0查询跨界token，14组原native IDs prefix均稳定。整段branch IDs再切prefix/suffix，后续每候选必须在裁剪prefix之后重算相同suffix，不能注入Full suffix KV。
- 半预算floor(373/2)=186槽；sink4+recent64=68锚点，free118，14/14可行。57344 bytes/槽，Full prefix21389312 bytes、半预算prefix10665984 bytes为布局预测；实际KV gather/bytes/VRAM未测，不能称显存减半。
- 独立标准库validator未导入tokenizers/Jinja/项目模块，逐ID还原native bytes与所有边界/预算，重建事实/gold/平衡与digest、6个probe及全词表语法图；0额外编码。未独立重实现Rust BPE或证明HF生成入口兼容。
- worker内0.915733648秒，verifier3.262950008秒，launcher4.396327750秒；guard全0，0模型答案/权重/GPU/运行内网络/依赖变化。Python audit不覆盖全部Rust原生IO，不称OS级沙箱。
- 归档28文件342048bytes，manifest SHA `798a680978ff5dd2689aabadc4563476b312668bcc3c9875323a0e7328dbaef4`；worker/final manifest全部回读一致。新增1CPUrun/0主要回答，累计122run3038主；新索引`results/20261031-run-index-decoder-native.json` SHA `34c0b9532254bd20530ff66a7427a399670301dc4fbf5e4cdc5165be7988f484`，上一轮3c7cdede…索引不覆盖。

## 解释与下一步

- 直接观察：新14组原生编码、有限JSON语法/合法语义分支和半预算数学可行性已验。
- 尚不支持：Full任务≥10/12、真实KV目标排序失配、部署selector/任务收益/成本优势、新颖性或论文可行性；没有模型logits，安全/正常任务/性能/显存指标均未测。
- 下一条具体操作：只在独立新协议下实现这2工程组的真实同前缀KV检查，冻结实际Full/gather/位置/数值标准、权重/runtime SHA、六随机seed和forward/token/时间上限；通过才测试固定12组Full支持及最多108主logit向量。Full支持不足或无失配信号即停，不换题/seed/预算救回。
- 本次不实现/启动GPU runner，不把旧草案改true，不重跑上一轮18软件用例。代码配置文档同步服务器，原始结果仅服务器，STATUS/WORKLOG/HANDOFF更新，GitHub未配置。


# TREC有／无示例Full KV能力关卡

## 实验身份

- 日期2026-10-28，Asia/Singapore；用户“开始下一步”，按冻结32题提案实现runner、通过前置工程检查后实际完成64个Full KV输出。不是裁剪实验、完整官方TREC复现或安全特异性结果。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-trec-context-full-v1`。本地仅代码/配置/文档，全部原始输入/输出在服务器，不复制nano-vllm。
- 状态complete，工程门槛通过，描述性context支持门槛通过；0运行失败、0补样本、0截断、0缺失。额外18条正确性输出单列，不计64主输出或新独立题目。

## 可复现条件

- 数据与前端沿[上轮CPU预检](20261028-trec-data-preflight.md)：官方HF fixed5e628be...，32个_id和两输入条件固定，cases SHA `e709d4bd298cd61a272f42835a180c7ac032b450b0aa1c40892814c7f6c8caf7`。两边相同50标签表和exact-label指令，query/gold不变；仅有无原context示例，长度/位置随之变化。原数据和提案未编辑。
- 原能力提案SHA `6e9c61d13d8a926ed0ce3d338d33642f95ff4aa48e2a014a8804896f65e2f91c`保持execution_enabled=false作为历史提案；runner复核64个原生输入ids和五个tokenizer/config摘要、8个判分fixture后加载模型。六个请求工程检查全部通过后、主生成之前，另存execution_snapshot.json启用此次执行，SHA `ad2d3cfd4036c190b6bea1dfcc4f3f2aa2822ac31472af97042f28661ed14cdf`。不靠修改历史提案启用其他实验。
- 现有Qwen/Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`，不下载权重。实际Qwen2ForCausalLM、28Full Attention层/无滑窗，7,615,616,512参数元素全部BF16。仅GPU0 RTX4090 24564MiB，驱动580.178.04；GPU1未使用。框架沿Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1，无依赖变化。
- 显式独立GenerationConfig：BF16/SDPA、greedy、num_beams1、repetition_penalty1、max_new_tokens64，EOS `[151643,151645]`，pad151643。不沿用模型默认1.05惩罚。输出text仅移去末尾EOS传输token再decode，其他特殊token/正文不隐藏，clean_up_tokenization_spaces=false；原ids及含末尾token文本一起保存。
- 独立runner `scripts/trec_context_gate.py` SHA `12cffbddf37d00e686d51ccd9fce4be59616a4218e34ed136db71329b18dc616`；CPU复核分析 `scripts/analyze_trec_gate.py` SHA `eef958ea0f1b426b1a93b3129f1e62e2df803aae5b549fdcd3011daa886322e0`。均保存同版本源码，不改旧runner/旧失败run。

实际执行命令（服务器方向根，前台SSH等待子进程；无tmux/nohup/服务）：

```bash
CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/trec_context_gate.py --proposal configs/trec-context-gate-proposal-v1.json --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261028-trec-context-full-v1
.venv/bin/python scripts/analyze_trec_gate.py --run results/20261028-trec-context-full-v1
```

本次启动前py_compile通过，两卡15MiB/0%、compute-app为空；自有模型PID2743087，前台父进程wait结束，exit0。命令/环境覆盖/console另存launch.json等。当前代码默认拒绝覆盖结果/分析manifest；复核须新建目录，不能重写本run。

## 结果与证据

| 条件 | exact正确 | 标签格式合规 | 官方兼容均分 | 截断/错误/缺失 |
| --- | --- | --- | --- | --- |
| 有示例 Full KV | 19/32（59.375%） | 32/32 | 0.59375 | 0/0/0 |
| 无示例 Full KV | 11/32（34.375%） | 32/32 | 0.34375 | 0/0/0 |

32对有示例→无示例：C→C=10，C→W=9，W→C=1，W→W=12，N/A=0。净正确数差8，所有13个有示例错题保留，未挑9个受益题替换总体。64输出均合法标签、EOS结束，含EOS长度2–8tokens，没有隐藏的其他特殊token。这轮错误是分类标签错误，未观测到标签格式违规。

工程检查：

- 首3题×两输入条件，共6请求的native整段/native cached/custom cached输出逐token一致，18条校验输出在correctness_checks，主输出另行生成。每次分支clone K/V逐tensor相等且存储不共享；原reference的指针、version及形状不变，缓存物理长度与原逻辑位置一致。
- 实测57,344 prefix KV bytes/token；首3个with_demos前缀2657/2528/3878tokens，对应152,363,008 / 144,965,632 / 222,380,032bytes；without均205tokens/11,755,520bytes。不计后续suffix/decode为prefix预算，也不称两条件等预算。
- CPU分析重新解码全部64的原始ids、重算whole-response exact/格式、逐题配对及门槛，并复核source/input/artifact SHA，与原summary一致。官方兼容指标只作副指标；本轮均合法单标签，故与exact计数相同，不把这个巧合当一般等价。
- 冻结的with exact≥16、truncated≤3、C→W≥8全部满足（19、0、9）；这是小规模描述性可行性门槛，不是统计功效或显著性证明，更不是旧权限任务95%门槛通过。

证据：manifest、cases、proposal、execution_snapshot、generations、correctness_checks、summary、paired_analysis、analysis_manifest、closure_audit和两份源码/console在本run。generations SHA `72a429e7333a90b87baf135bc7aef291e79eb9d69f40b00bb6fe438fec68dd0c`；correctness_checks SHA `4b4bb473f7b6378a5b04874a79f316773b7f26c584bb9698c705d2f7c9b0d6c6`。原始逐题文本仅服务器。

## 解释与下一步

直接观察：在此冻结32题和新前端中，有示例与更高的分类exact分数相伴，9题受益、1题受损；format两条件均32/32。示例移除同时改变长度/位置，不能据此唯一定位内部机制或把C→W称裁剪损坏。样本为较短前缀子集、18类gold不均且大量复用训练示例；不保证原gold全部语义正确，不外推整个LongBench或安全策略可靠性。

下一阶段独立提案：[trec-pruning-calibration-proposal-v1](../../configs/trec-pruning-calibration-proposal-v1.json)，SHA `289bb122e62788cff3406df9ba42a792172b2f10959144be187271e52634093f`，execution_enabled=false。本轮只写提案，未做裁剪、选择器CPU检查或新评分hook复测。

- 首先CPU固定同32个with_demos前缀的任务头token边界、50%预算与全部保留索引；每层/KV-head恰好floor(N/2)，共享sink4/recent64。完整任务头含标签表与输出指令，须用原生字符offset对应全部重叠token，跨边界token也保留并计成本，不能把整个system当任务头或私自保护示例。
- 四个条件各32：适配SnapKV、随机，以及各自保护完整任务头的对照，最多128新主要输出；保护成本全部包含在相同实际K/V字节预算。随机使用固定seed/key/layer/head生成，并对有/无保护共用同一随机分数流，无query/gold或模型结果访问。不是新方法或作者公平SnapKV复现。
- CPU合成KV需验证100%恒等、索引唯一/排序/边界、锚点/完整任务头、等字节与随机重放，失败就停。随后首3题实际hook不改K/V/Full输出、100%gather与原逻辑位置检查，通过后才保存执行快照；额外正确性输出最多24。不能因本轮context门槛通过就自动运行128裁剪。
- baseline复用本轮同版本32个with_demos输出，首3个新检查须逐token重现；使用全部32，包括13个Full错题，报告Full→压缩四转移、原32分母与Full正确19分母。NoDemo的9/1转移单列，不混作压缩结果。没有退化、出现改善和所有截断/error/N/A均保留，不调参直到出现想要的效应。
- 分类与exact-label格式只是校准指标，不代表一般约束/隐私保持。Pitfalls等已有这类近邻，完整任务头保护/随机是诊断基线，不作创新主张。旧IFEval停止配置和AccessDenied失败不变。

## 收尾

- 本轮1模型run64主要输出，另6请求18校验输出；累计54manifest run2524主要输出，索引`results/20261028-run-index-trec-full.json`，历史重复控制不当独立样本。
- 总耗时26.97秒，包含加载、CPU检查、额外校验和写盘，不是性能测试；未持续测量峰值显存或吞吐。不新增依赖/权重/后台/服务/端口，无其他会话进程改动。
- 自有模型进程已退出，两卡收尾15MiB/0%、compute-app空。STATUS、HANDOFF、WORKLOG、README、PLAN与本run按旧SHA核对同步；全部原始数据/输出留服务器。

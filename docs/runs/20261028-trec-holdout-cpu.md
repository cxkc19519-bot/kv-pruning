# 十题留出复查：来源核验、重叠审查与CPU冻结

## 实验身份

- 2026-10-28，Asia/Singapore；用户“开始下一步”，按交接只做CPU审查与复查设计，不加载模型或运行新答案。
- 服务器绝对根：`/home/user/jhk/project/Directional Exploration/kv-pruning`。结果`results/20261028-trec-holdout-cpu-v1`（自有解析断言失败，保留）、`results/20261028-trec-holdout-cpu-v2`（准备、逐题审查与独立验证完成）。无nano-vllm文件复制，本地仅代码/配置/文档。
- 目的为检查同一来源与长度规则下的未用问题能否支持一次有限复查；不是独立数据集、论文创新或安全结果。全部10题保留，无模型结果导向的挑选。

## 固定条件与来源

- 沿官方LongBench HF revision `5e628be450b7e67fb7ae6e201bd6d8f7056f7672`、TREC SHA `20a88e14f7442f58a39082cdd7396f1093ea8162da0a4ea7ead7d6757514c8f4`，复用已归档原始数据，不重复下载114MB归档。原42个合格_id减开发32，剩余10，仍为原SHA256(`20261028:trec:`＋_id)顺序；不换seed/扩长度/padding/修题。
- 为核对gold来源，新归档原作者的[分类定义](https://cogcomp.seas.upenn.edu/Data/QA/QC/definition.html)与[原TREC测试标签](https://cogcomp.seas.upenn.edu/Data/QA/QC/TREC_10.label)，两份均官方直接获取、无代码执行。taxonomy7552bytes/SHA `91f9ae5a4d289a011b9bca622a1b7ea2af3a5accab0a67e873ba41c058de3261`；测试标签23354bytes/500行/SHA `033f22c028c2bbba9ca682f68ffe204dc1aa6e1cf35dd6207f2d4ca67f0d0e8e`。这是获取时字节快照，不虚构Git revision；v2复用v1的已验来源文件，不再抓main。
- 只用现有Qwen2.5 fixed a09a354... tokenizer和config，五文件摘要匹配，未加载权重。Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1沿用，无新依赖。CPU线程4、CUDA_VISIBLE_DEVICES为空，CUDA未初始化。
- 准备脚本v1 SHA `ddb907c1314dfdf19ddc02349579ac6b239180fde3277211c16f8a4be082e5e6`；v2 `prepare_trec_holdout.py` SHA `9e6fdde643ee375ec2b81b3eea160ca0c457f06237908f7bb7553b04204a37e3`。v1把示例重组为带末行换行，与原文不符而失败；修正为原regex匹配片段逐字覆盖，不改任何数据/排除规则/前端，v1源码/manifest/console保留，v2另目录执行。
- 完成审查`freeze_trec_holdout.py` SHA `8c8dc9c7be98b80fd69ee0f99279460a0fefdce6ef36292006a87cd2b4c32b84`；独立验证`verify_trec_holdout.py` SHA `f2ed427c4d92332f42c5cd4ee468ae3ce348e4e83d2729d7b126ffd0fc20dc4a`。本项目工具selector SHA92594811...不变，全部同版本快照在服务器。

实际命令（服务器方向根）：

```bash
CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/prepare_trec_holdout.py --out results/20261028-trec-holdout-cpu-v1 --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/prepare_trec_holdout.py --out results/20261028-trec-holdout-cpu-v2 --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --provenance-snapshot results/20261028-trec-holdout-cpu-v1
CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/freeze_trec_holdout.py --run results/20261028-trec-holdout-cpu-v2 --review configs/trec-holdout-label-review-v1.json
CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/verify_trec_holdout.py --run results/20261028-trec-holdout-cpu-v2
```

v1实际运行的是未增加snapshot参数的原源码；目录与manifest均拒绝覆盖。CPU自有PID2941904已退出，v1 exit1、v2/审查/验证exit0，无后台任务或服务。源码修复不构成换数据/重跑模型，所有失败保留。

## CPU结果与审查边界

| 项目 | 结果 |
| --- | --- |
| 原规则下全部未用题 | 10，未删除或替换 |
| 与开发集_id/规范化问题文本重复 | 0 / 0 |
| 与已保存实验输出_id重复 | 0；独立逐行扫描32份generations共2652行，并保存各文件SHA |
| 原TREC测试标签逐题来源匹配 | 10/10，code到LongBench类别映射保存 |
| 原gold类别 | 7类；Definition3、Other location2，其余各1 |
| 相同共享header的新native prefix | 2203–4163tokens；suffix18–26 |
| 完整header/与锚点并集 | 200 / 267位置，半预算1101–2081全部容纳 |
| CPU随机流pin/unpin选择检查 | 2240个层/head，通过；不是实际SnapKV模型评分 |

- 10题question/gold/context原字节保留；不做任何“改成更合理gold”的处理。source_id、源行/逐行SHA、完整messages/ids、header_metadata与tokenizer SHA冻结。
- 逐题审查记录见[trec-holdout-label-review-v1](../../configs/trec-holdout-label-review-v1.json)，SHA `6c285a88eb4f40e268874a3cbaa702d029bf100a545e826648796d9a59f59e74`。审查为Codex的来源与分类定义核对，不冒称独立人工标注。定义型问法保留DESC:def原约定，不按题目讨论的是化学/医学对象就自动改为实体类别。
- 两题预先标记：53314c...原问题地名拼写可疑但原TREC相同，保留不修；f9666d...泛where问法的地点粒度可能与City/Country混淆，仍保留Other location。两个标记均不用于排除或改分，主分析包括全部10，最多补充逐题说明；原标签匹配不证明语义上唯一正确。
- 10个新问题都未在开发集示例中出现，但示例材料并不独立：每题独特(question,label)对有51.89%–66.43%已在开发32题出现，全部留出示例独特对共1313，其中808与开发示例共享。这个比例按去重示例对计，不是按raw token或模型记忆计。不能把共享示例下的十个新问题称全新训练材料或独立数据源。

冻结cases SHA `e2b6c2ed0d9d771c46e933364de0d21ca98d86995b357be6f6130c26ea0c6a6a`。独立验证重新编码10题，核对原question/context/gold、原始行SHA、预算/保护集合，全部source/input/artifact/tokenizer摘要通过。原始文件、示例重叠、逐题来源/审查、扫描证明、审核前manifest快照、finalization/verification和closure均服务器；本地无raw cases/标签源/结果。

## 已冻结的复查方案（未执行）

[trec-holdout-recheck-proposal-v1](../../configs/trec-holdout-recheck-proposal-v1.json) SHA `147aea59f40dfe6bc6a33635a3f2d8fbb482eb9e5232e00f15765b522584b915`，与服务端proposal逐字一致；execution_enabled=false，待适配有明确规模和阶段门槛的10题runner。

1. 同模型/原前端/评分/seed/四方法/50%每层head字节预算，不根据开发赢家去掉方法；不新增NoDemo，不扩长度、换seed或扫预算。
2. 首3题先做Full native/nohook/hook/100%gather，最多12个额外校验输出。通过后生成全部10个主要Full输出，冻结其原始ids/分数。
3. Full必须exact至少5/10、标签格式10/10、0截断/运行错误，才进入任何压缩参考或主输出。5/10沿开发gate的50%最低描述性支持比例，格式要求完整基线；这些不是功效计算或旧AccessDenied门槛例外。失败保存10个Full并将其余40格标not_run_full_support_gate，不能修提示/换题/模型直到通过。
4. Full通过后，首3题再做两种代表压缩分支的HF参考/custom对照，最多12个额外输出；工程校验总数严格24。通过后原全10题各跑四种压缩，40主要输出，包括Full错题；不挑Full正确/受损子集替代总体。
5. 总主要输出上限50，额外校验上限24。运行错误停止并保存部分结果和未执行格，不自动fallback/增加模型重试。单轮结束即收敛，不根据有无退化继续加seed/方法/预算。

主要指标是完整回答是否为允许列表中的精确标签，以及Full格式合规→压缩不合规的个数；原gold exact、Full→压缩四转移、pin干预和官方兼容分分别报告。条件损失分母使用本次实际Full正确数，不能沿开发的19；主表全部10含两个预标记案例，分类/格式/安全保持分开。报告0违规、改善或负结果，不作n10方法赢家/稳定家族/显著性或安全主张，也不把32+10混称独立确认的42题。

## 下一步与收尾

下一步编写独立、阶段受控的10题runner：现有开发runner硬编码32题/19个Full正确，不能仅跳过断言继续。保留已审过的真实位置分离、HF输入准备适配、评分hook和gather工具；验证冻结SHA/输入/新样本边界，确认GPU资源，再按12工程→10 Full→支持门槛→12压缩工程→40压缩顺序执行。任何阶段失败按新配置停，不能因旧32题通过就跳新Full关卡。

本轮2主manifest run（v1解析失败、v2完成；审查/独立验证manifest单列）、0新模型答案，累计58run2652主要输出，索引`results/20261028-run-index-trec-holdout-cpu.json`。无新依赖/模型/后台服务/端口或其他会话改动；审计进程均退出，两卡最后15MiB/0%、compute-app空。STATUS/HANDOFF/WORKLOG/README/PLAN与本记录、源码/配置按旧SHA核对同步。旧IFEval停止、AccessDenied失败和开发结果不改；本轮无质量/性能/安全模型结果。

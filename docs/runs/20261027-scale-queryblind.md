# 多事实 query-blind 筛查（2026-10-27）

执行前计划：本会话用户已明确授权小规模实验。全部环境/权重/原始结果留服务器；不使用 nano-vllm。

## 实验身份与复现条件（公共模板）

- 日期/时区/执行人：2026-10-27，Asia/Singapore，Codex代用户执行；任务“开始下一步”，沿用本会话明确实验授权。
- 实验绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning`；原始结果为其 `results/<id>/`。本地仅代码与文档。
- 问题：事实数量增加且不能全部固定保留时，Full KV是否足够稳定，再决定是否开展query-blind等预算裁剪。来源为自建任务/独立HF harness与固定公开EA评分的工程适配，无新方法主张。
- 状态：6个run结束，3次模型运行及原生审计共208输出；含重复控制。Full质量失败已保留，裁剪效果矩阵未运行；门槛拒绝测试按预期失败退出。
- 设备/版本：GPU0 RTX4090，GPU1未用；驱动580.178.04，Torch2.5.1+cu121，Python3.11.13，Transformers4.57.1，safetensors0.6.2，其他精确依赖见各manifest。复用本方向`.venv`与已缓存权重，没有改环境包/下载模型或数据。
- 模型/tokenizer：Qwen/Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`，模型原生chat template；初始化核查28层Full Attention/GQA且无sliding_window。自建synthetic JSON目录，固定生成器种子20261027及base/count偏移；世界300–302开发、400–402新世界检查，交换/任务/四问并不独立。
- 代码：`scale_pilot.py`/`scale_native_audit.py`/`analyze_scale.py`及既有helpers；所有run存执行时source快照、SHA与manifest。v1/v2/v3/v4的代码修订不覆盖旧结果。EA源文件经再次下载固定commit比对，仅两处已记录imports有差异。
- 本地方向未建立Git仓库，`git status`返回not a git repository；没有可报告的Git提交，以实际执行的源码快照/SHA固定版本。
- 进程/端口：前台SSH执行、日志重定向；无服务/tmux/nohup/新端口。模型任务均已退出；归属与GPU核查见收尾记录。

## 冻结设计与门槛

- Qwen2.5-7B-Instruct 固定 revision/既有环境，BF16 SDPA，raw greedy、repetition_penalty=1、max_new_tokens=64；禁用 TF32 和 BF16 reduced-precision reduction。
- 新基础世界 300–302；32/64 条可查询 record、两条 member，无长背景填充。每世界四问（两允许/两拒绝）；配对世界交换这四个 record 的组，保持全局组数、行序、ID、payload。两任务沿用已审计 JSON 输出合同。
- 压缩仅见首个 system prefix；运行时身份/可信组和未来问题均未提供给选择器。身份对应两条 member 行仍在目录中，runtime 组来自未压缩后缀。
- 每个 record 数组内，所有任务/世界实际 prefix token 数相同，因此各层/头形状与前缀 KV 字节相同。轻量中性 padding 配平；不是逐字符同 prompt。
- oracle 重新从 JSON 目录校验；扫描全文中的所有不匹配组 payload，不只抽中的问题。仍只检测完整明文标记。
- 必须断言规则+全部事实+sink4/recent64 位置数超过 50% 预算；这是不能完整保留全部原始事实位置，非信息论容量证明。
- 先运行 Full KV：每种规模/任务，至少90%的世界四问全对、95% schema、权限任务零观察到的完整禁用 payload。未通过的整个规模保留失败记录，不进入裁剪。不能筛掉失败问题。
- 后续独立世界400–402按相同生成器和门槛，保留其所有 Full 行；属于开发筛查，非独立预注册确认。

## 对照与实现边界

50% 同预算：窗口评分（SnapKV adapted）、Expected Attention、EA+规则固定、EA 按完整 JSON 行贪心装入、随机行装入。所有压缩方法共用 sink4/recent64；行方法额外固定规则并补全与 anchor 相交的行，剩余 token 用 EA 填满。随机行顺序不使用未来 query；EA 行密度为归一化跨层/头分数的行内均值。统一每层/头物理 gather，记录全部 indices/scores。

[Expected Attention](https://arxiv.org/abs/2510.00636) 的 NVIDIA/kvpress 评分主体固定为 commit `2d66e747719a7bf1b9276f2cae6d135b96b92fd7`，仅适配 imports/Qwen2 query helper；见 scripts/vendor/NOTICE.md 与 Apache-2.0 LICENSE。保留原公式及 BF16 运算，不称完整作者系统/性能复现。测试评分 hook 不改变完整 cache；首世界四问原生 cached generate 逐 token 对齐。

[KVzip](https://arxiv.org/abs/2505.23416) 也是相关 query-agnostic 强对照，已查看官方及 kvpress 实现；其重构评分、可变预算及 mask 压缩流程还未复现，本轮不声称已覆盖全部强对照。完整行装入属于结构控制，不能直接包装为新方法。

## 执行与结果

- `20261027-scale-prepare-v1`：24 个 case 生成成功，无模型推理。32 行规模 prefix=1222、预算611；64 行 prefix=2214、预算1107。规则/事实/anchor 联合覆盖分别1222/2214位置，均不能在50%预算完整固定。
- `20261027-scale-baseline-v1`：新世界300–302，96输出。32行权限24/24、路由24/24；64行权限23/24、路由20/24，世界全对5/6与2/6，整个64行规模停止。路由有1次非匹配值输出，属于公共任务错误，不称隐私泄漏；权限零观察完整禁用值输出。
- 发现 v1 prefix 精确配平但 runtime/question suffix 为42/43 tokens。修订 v2 在较短的 runtime system 内容尾加一个 neutral token，保证 prefix 与 suffix 均逐组等长；不改写旧结果/快照。下一运行只用32行世界400–402，先单独 Full 检查48问；通过才做同输入6条件矩阵。v2源码 SHA `4d9ec783871e556a165bde17eca2a645fbbf66b602e2edf92759b4d34f0483c6`。
- v1基线首世界四问 native/custom cached greedy 逐token相同；v2继续执行相同检查。旧64行失败不被调提示或删除样本掩盖。

命令均在服务器方向根目录，`MODEL=/home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`；通过前台SSH执行，stdout/stderr保存对应 `results/<id>.console.log`：

```bash
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-scale-prepare-v1 --stage prepare
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-scale-baseline-v1 --stage baseline
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-scale-fresh-baseline-v2 --stage baseline --counts 32 --base-start 400
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-scale-score-check-v3 --stage check --counts 32 --base-start 400 --bases 1
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-scale-gate-rejection-v4 --stage screen --counts 32 --base-start 400 --gate-run results/20261027-scale-fresh-baseline-v2
.venv/bin/python scripts/scale_native_audit.py --model "$MODEL" --source-run results/20261027-scale-fresh-baseline-v2 --out results/20261027-scale-native-audit-v1
.venv/bin/python scripts/analyze_scale.py results/20261027-scale-fresh-baseline-v2 > results/20261027-scale-fresh-baseline-v2.analysis.log
.venv/bin/python scripts/analyze_scale.py results/20261027-scale-score-check-v3 > results/20261027-scale-score-check-v3.analysis.log
.venv/bin/python scripts/index_runs.py results --out results/20261027-run-index-scale.json > results/20261027-run-index-scale.log
```

### 新世界门槛与原生审计

| 设置 | 权限严格正确 | 公共路由严格正确 | 四问全对世界（权限/路由） |
| --- | --- | --- | --- |
| v1，32行，世界300–302 | 24/24 | 24/24 | 6/6，6/6 |
| v1，64行，世界300–302 | 23/24 | 20/24 | 5/6，2/6 |
| v2，32行，世界400–402 | 23/24 | 23/24 | 5/6，5/6 |

v2所有schema正确，权限/路由各一次误拒答，均无观察到的完整不匹配值输出。两个失败均为base400/W0/query0，对象r4443：应读到cedar，但输出record_group=orchid，随后BLOCK；源表第22条JSON行（0-based索引21）。两任务错误完全相同；不能据此把错误归为安全特异。

为排除新数据下分段缓存的干扰，额外对**全部48个冻结请求**做整段原生`model.generate`（没有传cache）。48/48输出token与v2自定义缓存路径相同，原生也各23/24。此审计不作为新的独立样本或门槛通过证据。

### 评分工程检查与未执行内容

`score-check-v3`只在base400的4个任务/交换case上计算EA/窗口评分、生成Full输出，未用压缩cache生成回答：

- 首case评分hook前后Full cache逐元素bit-exact；首case4问原生cached与自定义路径逐token一致。
- 16个Full输出与v2无评分hook完全一致；判分检查接受正确对象，并检测未抽中问题的禁止值出现在回答尾部或字段中。
- 5种保留选择器均实际构造物理压缩cache，字节为Full一半：35,037,184 vs 70,074,368 bytes。只计前缀K/V，未计完整参考备份、后缀、权重、索引与评分工作区，不作为部署节省/延迟结果。
- 原始scores、indices与行跨度保存在4个`cache_maps/*.pt`。分析共2688层/头索引检查，验证数量、唯一、排序、公共anchor及对应规则保护；全部通过。
- v4加入必须指定通过的gate-run、模型/解码一致及cases字节相同的screen门槛。使用失败v2门槛尝试screen，预期exit1，manifest=`refused_quality_gate`、0输出，模型未加载。该运行是门槛拒绝验证，不是已执行压缩矩阵。
- 实际复现的EA评分主体不等于完整EA/AdaEA系统；本轮没有压缩后回答，因此不存在EA/行方法优劣结论，也没有KVzip复现结果。

验证过程一条内联辅助命令误用系统`python3`导入torch，报`ModuleNotFoundError`；改用本方向`.venv/bin/python`后判分/16输出复核通过，无实验输出丢失。无模型OOM、无服务启动、无旧项目复制。`torch_dtype`弃用和greedy模式忽略temperature/top_p/top_k警告已留日志。

### 证据、解释与下一步

- 全部cases/generations/manifest/source快照/检查/console日志位于上述服务器run目录；本地不保存原始数据。分析输出为fresh-baseline-v2及score-check-v3下`paired_error_analysis.json`，附`analysis_manifest.json`与源码快照。总索引含21个run、1748生成记录；本轮208条含多项重复控制，独立基础世界只有6个。
- 直接观察：加入多条事实后新世界Full门槛不稳；v2权限与路由的同一组别读取错误同时出现，原生完整输入复现。推断：应优先解决共同的查组可靠性；当前没有新证据支持裁剪导致安全特异关系损坏。
- 下一步：冻结更可靠的模型/模板后，预先选定新世界重新跑Full；门槛通过才开展适合query-blind的强对照。不得降低门槛、挑通过世界或继续增加规则复杂度掩盖问题。KVzip/作者公平实现及第二模型族仍待补齐。
- STATUS、WORKLOG、HANDOFF、README、PLAN及协议已更新。末次GPU/进程与两端摘要核验另在收尾追加。

收尾：索引验证21个run、1748生成记录，索引内文件513,646,999 bytes（不含目录外console日志等），6个本轮run的全部source摘要通过，两个分析目录的源码/输入摘要通过。精确归属本方向的实验PID为空；GPU0/1均15MiB、0%利用率。无运行任务/服务/新端口，没有停止其他会话进程。两端文档按旧SHA先整体比较再同步，避免覆盖并发修改。

# CPU 配对报告模块实现与回归验证

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；服务器Unix/UTC另存启动记录。
- 授权：本专用实验会话，用户“继续”，按[冻结CPU提案](../../configs/reliability-report-replay-proposal-v1.json)实现并验证只读报告。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-reliability-report-replay-v1`及同级`20261030-reliability-report-replay-v2`。
- 问题：从已存结果规范化、配对、聚合时能否复现历史结果，并显式处理分母、缺失、失败、预算不一致及未知成本。
- 来源：软件实现与回归验证，非新模型/安全实验。v1归档结果与12个原fixture通过，后审查发现一个历史口径的错误路径语义遗漏，保留并标superseded；修正v2通过。
- 本轮新增2 CPU run、0主/工程生成回答。累计94run2732主要输出，历史运行数含CPU/失败/重复，不能当独立样本量。

## 可复现条件

- 服务器旧`.venv/bin/python`3.11.13、标准库，未导入torch/transformers/vLLM或旧runner/scorer，没有模型/tokenizer/tensor加载、GPU查询、网络下载或依赖变更。`PYTHONDONTWRITEBYTECODE=1`避免新pycache。
- 无Git仓库/远端。本次新增[纯报告模块](../../scripts/reliability_report.py)、[边界fixtures](../../scripts/reliability_report_fixtures.py)、[有界runner](../../scripts/replay_reliability_report.py)；旧10个生成/判分/审计脚本保持不变。
- 输入为3个旧TREC run的9个已固定JSON文件，共294450bytes、242个JSONL行。开发控制文件64行只取with_demos的32行为Full，另32行without_demos不进入压缩配对；开发压缩128行，留出10 Full+40压缩。baseline副本按case/input hash/gold/token ids/metrics核对，模型路径、版本、tokenizer摘要和实际生成配置一致。
- 模型与数据仅为历史来源背景：Qwen2.5-7B-Instruct固定snapshot、旧LongBench TREC开发32/留出10，不在本次运行。两组均已使用且示例共享，仅作软件回归材料。
- 原提案SHA `0e98ebcd56a5f69a7af60161f73a296f043325d59864d83f05da36af4999bc33`保留false/未实现历史字段；启用快照另存。每run60秒/32MiB输入/300 JSONL行/32输入文件/12fixture，外层subprocess70秒，只管理自有CPU子进程。
- v1 PID786388，0.050494秒、exit0；v2 PID787643，0.051172秒、exit0。两PID收尾均不存在，无端口/服务/后台任务，无GPU/他人进程探测。

已执行命令，cwd为服务器项目根（不要在原目录重跑）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/replay_reliability_report.py --run-dir results/20261030-reliability-report-replay-v1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/replay_reliability_report.py --correction configs/reliability-report-replay-correction-v2.json --run-dir results/20261030-reliability-report-replay-v2
```

两个run同级各保留`.launch.json`和`.console.log`。原始规范化逐例记录、fixture证据和机器报告只在服务器，本地只保存源码、配置和本文档。

## 修正及版本证据

v1将两种口径的条件损失分母都写成“可比较且Full正确的配对数”。对本次无错误/截断的旧数据，这与历史分数一致；但方法出错时，旧报告的历史分母仍应保留所有可用Full正确数。原fixture2仅检查strict路径，未捕获这个区别。

后审查写入`v1/post_review.json`，未改v1 manifest或报告。修正v2只区分分母、显式记录eligible pair数，并在同一个fixture2同时检查两种口径。冻结9输入、两组期望与12fixture身份及运行上限不变，没有为过线改模型结果。

| 版本 | report模块SHA | fixture模块SHA | runner SHA |
| --- | --- | --- | --- |
| v1归档 | 974f637b2f3e4f8cb36831c26baac434221058f2c7ce7f6daf02480866933776 | 72ad8fe2e3c9af44a628a13c2288da5b8270a391b5ef79b9513794dfa7c22c75 | a9db988a481ad2b9fca53073e237d1c260c29b27c954383d3c71607e4b04a634 |
| v2当前 | b4a1afe3170b92098dbc03593c25f3be144dc5f20b10b845608dc7f4bd46dffb | ee08aab635cad37f5e831dafa3bb5b3de5044b6086a6344773b4f0e682dcb450 | e748a497804f0eb2a63f4ea2092429e6657c34a2c8ecc4db803f3dd21131d3c9 |

修正提案SHA `d46a3c9bc4240a00a6a7eeed6ff3cdf3b2bd625ae1ad94726ee53b7d26292818`，固定原manifest与post_review摘要；未覆盖原提案。

## 结果与证据

两个cohort各有两份口径报告，共210个唯一规范化记录。逐行聚合与冻结期望、历史summary全部一致，外层独立Counter重读任务/约束四转移、分母和unknown字段通过。仅复算已存布尔分数的聚合，没有重新解码或验证原判分器。

| cohort | Full任务正确/约束合法 | 适配Snap | 随机 | Snap保护 | 随机保护 |
| --- | --- | --- | --- | --- | --- |
| 开发32 | 19/32 | 17/31 | 17/30 | 16/32 | 19/32 |
| 已用留出10 | 7/10 | 7/10 | 6/9 | 7/10 | 7/10 |

每格是“任务正确个数/约束合法个数”，共同题数分母由行标题给出。不是精度分数相除。留出随机保护与Full净分同7，但报告明确显示C2W=1、W2C=1；不称逐例无损。历史数据无错误/截断，两种口径此处计数一致。

12个软件fixture全部通过，覆盖零分母、方法失败、截断、缺cell、重复身份、输入hash/gold不一致、损坏改善相抵、保护与未保护字节不一致、未测成本、保护超预算、约束注释缺失及跨cohort同ID。fixture5对hash/gold两个轴分别检查，但仍是一个冻结fixture；v1/v2两次运行不算24个独立案例。

方法失败且Full正确的fixture在v2明确表现为：历史口径条件损失0/1、eligible pair0且unassessed1；严格口径分母0、率null、unassessed1。历史0不是安全成功，报告同时保留覆盖不足证据。截断分数保持原值；strict不将其纳入完整配对。未测peak GPU bytes、latency、extra-buffer peak保持null与原因。保护不足预算标infeasible，不增加预算。

### 工件

- 每run原manifest分别覆盖12/13文件，逐SHA核验；后审查/closure等另用derived_manifest，不改原始归档。原9个输入及旧run索引核验未变。
- v1 manifest `5aaf3753c020d4b3012698532a2f3b27fa4e9f097fe77e09e38a535adf8d2d84`；post_review `aa852d4a3308053fb41ab6a3a96562ce0d5a68df2df7d3522f93bbeaed557bbe`；closure `5bfe8e3ebeb31dc134ddf0e53837a40bc6237836e84d1a861d91cb790cfa00a6`。
- v2 manifest `e395fb3f2e0b4aaf270e404690e5668f3786c70b9ddc9bf2dd35d60ff2a2e12f`；summary `e61bfa30a855ce1328748626a759fdf3da81e45be5d24b8acaa5496a8142da4b`；report `380c5af39b5e263a0fae680a0861594ddffec63936a6bde83e60da2c7aab318a`。
- 两run normalized_records相同，SHA `e3b8d013d7f6b0e24230c301dd046b6f8ae147f508ca44c61b92733d1650805a`；v2 fixtures `1a9f94fb6f88b727e07b96febcfbfb25b712b813a21e9ceb651bae6ab2a41738`；v2 closure `ff74895df49128f546692ad526d4e3d7a00c5c0cd821958ffd15dfd5f5ef945c`；derived manifest `c714d163a3dac3ea1d65710caf2d3f2769561fea516ff3c2e56586fee50bf521`。
- 新索引`results/20261030-run-index-reliability-report.json` SHA `54b237c27d47bd73bbc52def700c42e9136da414453e42f43f93682c2ffd97a4`，累计94run2732主要输出。v1标complete_superseded_profile_semantics_gap，原run自身complete字段不追改。
- 工件约v1 526538bytes、v2 530767bytes（不含同级日志/最终文档同步记录）。没有新模型答案、安全指标或性能测量。

## 解释与下一步

已实现可用的、范围明确的历史TREC结果adapter、配对报告与边界验证；重复身份和不一致输入会拒绝，错误/未运行/截断/不适用、不可评估的Full正确数及未知成本不会被默默删除。这是评测系统的报告层，不是跨任务/跨模型平台或论文新机制。

旧真实map审计只传递manifest中的引用及范围，本轮不读取`.pt`或重新审计KV，也不证明评分器、生成后端或一般约束语义正确。新增软件回归不能充当独立实证数据。现有系统/实证题目还需要新任务数据契约及独立确认。

下一条先离线设计一个新任务的数据与判分契约：确定具体约束、任务正确性、来源/上下文族、独立划分、Full支持条件及失败处理，写清与旧TREC材料的关系；不立即写通用生成器或启动模型。样本/预算/第二模型需另冻有界协议，不恢复旧A、guard、controller或取消攻击队列。

收尾更新STATUS、WORKLOG、HANDOFF、PLAN、README、需求/盘点/选题稿与准备清单，同步源码和配置并逐SHA核对。GitHub项目远端未配置，无外发消息或提交。环境未改变，根环境文件无需新安装记录。

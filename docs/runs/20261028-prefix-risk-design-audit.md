# 前缀风险预算候选启动前的CPU方法审查

## 实验身份

- 2026-10-28，Asia/Singapore；用户“按照你的建议开始吧，5小时额度用完再停”。本轮工作窗口从17:07:39起最长五小时，余额不可见，不声称已经用完。执行人为当前Codex会话；仅CPU数学/研究审查，未加载模型。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-prefix-risk-design-audit-v1`。
- 问题：候选A的按组风险/效用与KV预算方法是否超出现有LTT/Pareto/输入自适应压缩框架。数学检查为自建有限概率审计，不是论文模型结果复现。状态complete，0运行失败。

## 可复现条件

- 非Git目录，以源码SHA冻结：`scripts/audit_prefix_risk_design.py` SHA `06796f8fa3e3657e363bed7d422f33d5917b8178457166b0049f65588b724a32`；配置`configs/prefix-risk-design-audit-v1.json` SHA `928b49c19be3265fcc0e41ca755b02acaf31ae24f9465b26517a3c7b171a56e7`。
- 使用服务器已有venv Python3.11.13及标准库，Fraction精确概率；无Torch/Transformers/model/tokenizer导入、CUDA初始化、模型/数据或依赖下载。GPU规格沿已有记录，两卡read-only检查15MiB/0%、compute-app空，本轮未使用。
- 确定性枚举：n4/8/12，四原子联合概率以1/4为网格，风险边界0.1/0.25/0.5，检验水平0.05/0.1/0.25。二元风险在每个采样单位内允许任意联合分布，单位间iid。不是LLM数据、随机模型或有限样本安全认证。
- CPU脚本运行上限120秒，配置拒绝启用任何模型输出。失败写manifest与traceback，输出目录拒绝覆盖。

实际命令（服务器方向根，前台父进程wait，无后台/服务/端口）：

```bash
.venv/bin/python scripts/audit_prefix_risk_design.py --config configs/prefix-risk-design-audit-v1.json --out results/20261028-prefix-risk-design-audit-v1
```

## 结果与证据

- `manifest.json`、`proposal.json`、源码副本、`exact_probability_checks.jsonl`、`summary.json`、console/launch及closure/index均服务器，主要模型输出0。882个联合检验原假设检查、22925个多项结果枚举通过，exit0。
- 8独立prefix×8完全相关query的零失败例子：错误iid p0.03752，正确prefix p0.66342。16独立候选后验任取通过者的构造例子：单候选错误通过0.04607，任一错误通过0.52982。这些数值仅为精确数学例子，不是模型或部署概率。
- LTT已允许用max component p构造联合风险检验，固定策略全部风险同时通过不必按风险个数分摊delta；上轮四组Bonferroni86是保守方案，非最小需求。单策略各分量iid零失败的理想例子每分量59即可，但候选选择/分组缺失/相关采样仍需独立处理，不能把16prefix小试当认证。
- Full相对退化0不意味着绝对安全；绝对安全不达标时Full不能冒充安全fallback。非单调p值序列0.01/0.2/0.001仍在第二个停止。两个前缀不同保留需求的toy分配是普通有限搜索，不是新方法。
- 新颖性gate=false是基于文献归约的研究判断，**不是CPU程序检测了新颖性或证明全部未来工作无价值**。独立评估含“执行正确”和“研究可继续”两个不同结论，前者通过、后者当前否决。

## 解释与下一步

详见[启动审查与数学依据](../PREFIX_RISK_DESIGN_GATE_20261028.md)。候选A的当前方法主张归约到已有方法，故不启动原建议256主要输出，也不修改TREC/旧AccessDenied停止状态。继续同窗口离线核查“高保留率下缺关键关系证据时的有条件拒答”线索，先审Compression-Aware Abstention/KVDiagnosis/上下文充分性近邻，再决定是否值得另立任务；现阶段无新模型执行快照。

STATUS、WORKLOG、HANDOFF及相关文献/计划更新并按远端旧SHA同步；所有概率原始结果留服务器，本地只代码/配置/文档。环境无变化，无本轮运行进程或后台服务。

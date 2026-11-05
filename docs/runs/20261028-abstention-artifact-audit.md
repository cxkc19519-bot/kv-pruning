# 压缩感知拒答公开评测文件的CPU核查

## 实验身份

2026-10-28，Asia/Singapore，当前用户授权五小时研究窗口。目的为查重和核对公开证据，不是新模型复现。服务器绝对路径为`/home/user/jhk/project/Directional Exploration/kv-pruning/results/`下`20261028-abstention-artifact-audit-v1`、`20261028-abstention-artifact-analysis-v1`及`20261028-abstention-artifact-analysis-v2`。一个下载run完成、分析v1失败/v2完成；全部0新模型输出。

## 可复现条件

非Git工作区，源码冻结：fetch脚本SHA2740df32d855506081fac61ba12d69eefa20a77f7c60acfc99cdcb375b7467a8；分析v1 SHA222bec9689af6a979115340a76d47cc265d44dc3b64e717e83e49820b71e9f9a、v2 SHA f12578fefe6747d15972f04144bd587352287887d5d87363395230283c4d3695。Python3.11.13标准库，未导入Torch/模型，GPU未使用，无依赖/权重安装或服务。

作者仓库固定1426730aaf29edf48e91930d14d3b47b73f8e584；4文件通过公开GitHub blob API读取，每个文件大小与预期Git blob SHA1核对，再记SHA256。单响应16MB上限、socket超时30秒（不是总传输时间上限）；原始约11.5MB只服务器。模型/adapter、1GB训练数据均未下载。无需模型/tokenizer/chat template/种子或解码参数，因为只重算已发布文本；作者的推理条件不能冒称本会话已复现。

服务器方向根命令：

```bash
.venv/bin/python scripts/fetch_abstention_artifacts.py --out results/20261028-abstention-artifact-audit-v1
.venv/bin/python scripts/analyze_abstention_artifacts.py --artifacts results/20261028-abstention-artifact-audit-v1 --sources results/20261028-abstention-source-audit-v2 --out results/20261028-abstention-artifact-analysis-v1
.venv/bin/python scripts/analyze_abstention_artifacts.py --artifacts results/20261028-abstention-artifact-audit-v1 --sources results/20261028-abstention-source-audit-v2 --out results/20261028-abstention-artifact-analysis-v2
```

v1分析误假设metadata比例未舍入，严格1e-6断言失败；原400条中56条采用三位小数，v2按相同公开精度核对后通过，所有mask及数据不改。退出码依次0/1/0，未以修代码修改原始结果。

## 结果与证据

两份实际压缩KV输出463+463行，100源问题、多比例相关；400样例和400judge日志。输入14源码的marker列表仅AST literal提取，不执行作者函数。全部926行拒答标记与保存的model_abstained一致；输出未保存aliases，因此不冒称独立完整复判gold正确类别。

两模型correct86/380，代理Confident标签97条中正确4/24、拒答36/48、错答57/25；always-abstain按代理标签366/463。19条宽泛标记独占记录即使全重判也只影响至多4.10个百分点，不足解释294行correct差。作者judge严格352条κ0.60894与披露一致。无iid显著性/新安全失败或性能结论。

summary/flagged_outputs/diagnostic_baselines、所有输入/源码manifest、console/launch/closure均服务器；索引`results/20261028-run-index-abstention-artifact-audit.json`累计65run2702主要输出。新原始公开文本不下载本地；分析按分母与来源区分，详见[候选边界](../ABSTENTION_SOURCE_FINDINGS_20261028.md)。

## 解释与下一步

候选C宽泛表述已被近邻覆盖，不启动训练或新的GPU矩阵。继续固定历史KV预算下的动作安全guard来源审查，先查真实历史压力、可用逐步标签和训练隔离。用户实验授权有效，停止旧矩阵的原因是研究/任务关卡，非缺少许可。模型主输出累计不变，无本轮模型/后台服务，STATUS/WORKLOG/HANDOFF同步维护。

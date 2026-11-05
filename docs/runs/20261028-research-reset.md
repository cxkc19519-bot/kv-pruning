# CPU证据重算、查重补充与研究收敛

## 身份与范围

- 2026-10-28，Asia/Singapore；用户“开始下一步”，按上轮交接暂停GPU推理，先离线重算已保存证据、补读近邻并写下一关方案。服务器根`/home/user/jhk/project/Directional Exploration/kv-pruning`；本地仅代码/配置/文档，不复制nano-vllm。无模型/数据集新下载、无第三方代码执行或新依赖。
- 研究结论与方案见[RESEARCH_RESET_20261028](../RESEARCH_RESET_20261028.md)。本轮0新模型答案；源文件只读/AST和旧输出汇总不是新模型实验或新独立样本。

## 固定来源与执行

- GitHub连接器读取并固定Google IFEval `e6890f85757dd84e27ca6df2dd30651dafad28e0`的README、LICENSE、requirements、instructions/registry/util/evaluation_lib；KVDiagnosis `153699e227856b891b71beac8bd2a6922f181f79` README/LICENSE；Pitfalls旧固定`73079e1...` README。10文件124,962字符，全部Git blob SHA核验，4Python AST通过；没有import/执行上游模块。
- 新读KVDiagnosis arXiv v1（2608.09412，2026-08-10）的设置/记录/诊断/限制相关节，核查作者仓库；Pitfalls官方ACL2026入口/作者README再次确认多指令测量重叠。网页只读，不下载论文正文到本地；不将预印本未来会议页眉当已录用证明，未复现作者结果。
- 归档最初尝试单命令传输连接器内容，因Windows命令长度限制未启动；改服务器直接固定URL读取又遇read timeout，没有形成完整源payload。此时提前启动CPU审计v1，触发FileNotFoundError，failed manifest/日志/源码保留。随后用分块SSH传输连接器已读内容，137,016bytes JSON载荷在服务器逐个验证官方Git blob；v2同一审计源码完成。没有忽略v1、改研究参数或启动模型。

实际审计命令（v1失败、v2完成）：

```bash
.venv/bin/python scripts/audit_research_reset.py --results results --sources results/20261028-research-reset-sources.json --proposal configs/measurement-calibration-proposal-v1.json --out results/20261028-research-reset-v1
.venv/bin/python scripts/audit_research_reset.py --results results --sources results/20261028-research-reset-sources.json --proposal configs/measurement-calibration-proposal-v1.json --out results/20261028-research-reset-v2
```

## 汇总与决策

- CPU重新读取3个AccessDenied原版模型run的manifest/generations，严格分重现8/0/0、8/7/3、8/0/2；小目录诊断Full47/48、完整规则7/48、全部事实48/48、等量随机10/48；结构化新基线96/96，32行新世界权限/路由各23/24。与旧记录相符，未重打分或重写原结果。
- 上述证据不建立安全特异绑定损坏。暂停AccessDenied模板路线、保留旧门槛失败；补充KVDiagnosis近邻进一步降低“通用失败诊断”作为新贡献的可行性。
- 制定一个标准测量校准提案，最大32题/160主要输出，原生user/完整任务已知、query-aware，官方strict检查器和全样本四转移统计。不是新算法、完整Pitfalls复现或新立题承诺；真实数据SHA/key、检查器CPU正负例与依赖/kwargs、新前端/选择器实现尚未预检，配置execution_enabled=false。本轮不运行该矩阵，不使用新规则救回旧失败gate。

## 证据与收尾

- 脚本`scripts/audit_research_reset.py` SHA `ab98f7f41b6a7972b8d16ff36977827aa3536adcb74820ee842d7eb9406b4440`；提案配置SHA `ecca3b4e26f686496ffceb9918438d5115fb7b879936f12392ff0aa0fea3eb50`。v1/v2保存相同源码快照，v2保存proposal、upstream原文件/许可/检查、evidence_summary、来源/输入摘要与manifest。
- 原始载荷`results/20261028-research-reset-sources.json`、`.part`分块副本与两run/console均服务器。公共源对应的是已核验文本，不把archive复制当作者结果复现。无完整IFEval数据集或新模型权重下载，旧2460模型输出未增加。
- 收尾所有来源/输入/源码摘要通过；CPU汇总v2约0.044秒（不含归档/阅读，不作为性能指标）。新增2个manifest run（v1归档未就绪失败、v2完成），0模型答案；累计47run2460主输出，索引`results/20261028-run-index-research-reset.json`。两卡最后15MiB/0%、自有PID为空，无推理/服务/后台/新端口，环境未变；closure_audit保存转运/超时/过早启动失败与最终核验。
- STATUS/HANDOFF/WORKLOG/README/PLAN/协议/文献/查重和新增研究决策文档按远端旧摘要核对后同步。本轮未把提案当已执行注册；下一步仅CPU数据/判分器/预算预检，达标并固定新执行配置后再考虑模型。

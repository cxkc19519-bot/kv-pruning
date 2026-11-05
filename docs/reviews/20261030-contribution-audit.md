# 2026-10-30至31 近邻贡献差异审阅记录

用户“开始下一步”，执行上一断点的原文与公开实现核对。本轮是只读文献/来源审阅，非模型或数据实验；实验索引保持120run3038主，新模型答案、分词、权重、GPU查询、依赖变动均0。没有执行作者代码/测试或下载其模型/数据集。

主要交付：[差异审查](../CONTRIBUTION_AUDIT_20261030.md)、[范围决策](../CONTRIBUTION_SCOPE_DECISION_20261030.md)、[机器可读状态](../CONTRIBUTION_AUDIT_READINESS_20261030.json)。源材料只在服务器`/home/user/jhk/project/Directional Exploration/kv-pruning/literature/20261030-closest-work-audit-v1`。

## 固定范围

六项主近邻：Pitfalls ACL正式版、KVDiagnosis v1、Risk-Controlled v1、NVIDIA kvpress、质量与系统性能联合基准v1、LYR–001作者先导研究。另读TensorRT-LLM版本化官方开发指南作为工程规范参照，不将其混合/卸载实现当本项目基线。KVDiagnosis未来会议页眉不作录用证据，LYR明确未同行评审。

| 仓库 | 固定commit |
| --- | --- |
| alexluchen/pitfalls-of-kv-cache-compression | 73079e1b3bf27cd182f680d7da5edd97b660bd82 |
| ChosenQC/KVDiagnosis | 153699e227856b891b71beac8bd2a6922f181f79 |
| NVIDIA/kvpress | 2d66e747719a7bf1b9276f2cae6d135b96b92fd7 |
| agrawal-nikita/Benchmarking-KV-Cache-Optimizations-across-Task-Quality-and-System-Performance | 925fadf54a351b389e26d15535c1129aaefe61e2 |
| YesterdaysLemon/llm-research，作者页面直链 | da616c39ba57eeb4d076b36ef320d603b3e9a258 |

前4仓库重新解析HEAD与tree，仍为原项目已知版本；第五个是作者页面固定commit，不称其为最新HEAD。共33仓库文件/6网页或论文来源/24作者Python AST，逐blob与SHA核验，无源码导入或执行。Risk-Controlled未定位可冻结作者仓库，代码层保持未知。

网页工具的部分GitHub HTML/raw请求返回timeout/cache miss，改读同一官方API的固定Git blob；API源文件获取39次、metadata9次均成功，失败网页不是“无代码”证据。曾有一次候选路径列表显示过长导致客户端JSON解析失败，服务器tree_inventory已成功写入，随后只读压缩展示恢复；未重跑实验或改动任何模型结果。

## 源材料完整性

归档51文件2924027bytes，39来源正文共2240119bytes。全部原材料仅服务器。source_manifest将commit/path/blob/size/SHA256与URL逐项登记，AST_inventory只记录语法结构；archive_manifest覆盖正文及元数据。独立逐文件回读匹配，原GPU194工件及上一CPU分型原始工件保持，旧自有PID退出，无GPU队列。

| 工件 | SHA256 |
| --- | --- |
| source_manifest.json | 56f0e78f32c84cf64cf9c4e5b810811414bd154309b8a8b3cc75e6724d1dc69c |
| AST_inventory.json | 2e16c8ba0c24d843f891379cfbbc960335cb4b1348fc08e4243003108f34a012 |
| closure.json | b420d14e85225e933515366bc1f8ca86a2a27dc51ab1bd172e9258500346195a |
| archive_manifest.json | 74239ef0f39ff4273c93ddfc5fef265bf54a29c9dc3431c333b2fec35b1981f9 |

## 判断与后续

通用退化发现、Full配对/N/A账本、实现来源审计、格式与事实混淆、cache与显存区分都有直接先例。当前原型/48组结果保留为工程和受限案例证据，尚未建立独立新方法/新基准贡献；不以更多同类退化实验补新颖性。

下一步先重定具体研究问题与可证伪差异，不自动恢复保护/3/4/BoolQ/Mistral/旧16或新模型矩阵。STATUS/WORKLOG/HANDOFF、文献台账、选题与章节映射/readiness更新并同步服务器。GitHub未配置，无push，当前无运行任务。

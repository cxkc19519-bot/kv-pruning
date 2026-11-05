# 压缩感知拒答作者源码只读审查

## 身份与范围

2026-10-28，Asia/Singapore；同一用户授权最长五小时研究窗口。目的为核查候选C与已有工作的差异，并非复现模型结果。固定公开仓库`mali-kh/compression-aware-abstention`，commit `1426730aaf29edf48e91930d14d3b47b73f8e584`，MIT许可。源码、网络失败和原始文本仅服务器同名方向目录`results/`；未执行或导入作者代码、未加载模型、未安装依赖。

## 条件与命令

使用服务器已有Python3.11.13标准库，GitHub tree/API读取，单文件300KB上限、socket超时20秒、4线程；核对Git blob SHA1与本地SHA256，10个Python文件仅AST parse。树固定、无分页截断，14个选定文件含README/LICENSE/CLAIMS、标签/压缩器/评测器。脚本[ audit_abstention_sources.py](../../scripts/audit_abstention_sources.py)当前SHA `b8e07e22c943ffcce4a7bc876e1959ab409463576a2ca75111a0858d173d4beb`。

服务器方向根命令：

```bash
.venv/bin/python scripts/audit_abstention_sources.py --out results/20261028-abstention-source-audit-v1
.venv/bin/python scripts/audit_abstention_sources.py --out results/20261028-abstention-source-audit-v2 --transport api
```

v1冻结源码SHA `0278bee7e29e59e445d51f32703fd206a3d26520d633d5051e775ba30c39418c`为原raw版本，v2新增API选项；不能用当前脚本冒充v1原字节。v1共有9个raw读取失败，核实/proc自有PID3140010后SIGTERM，父进程wait返回-15；manifest与终止前快照完整保留。终止原因文本原写eight、计数实际nine，另留更正快照，不改原失败证据。v2 API读取14/14成功、blob验证14/14、AST10/10，exit0。无新模型输出，两run不能只记成功版本。

## 已确认的静态观察

- 标签源码明确把required-vs-redundant supporting spans列为开放问题；v1默认全部annotated spans必需。`label_example`丢弃context/query参数，用各span位置保留率及0.8/0.3阈值决定Confident/Abstain/Drop，并非语义证据充分性判定器。
- KVzip与kvpress包装器把分层分头保留mask聚合成逐token分数，再按目标比例选1D top-k；这是公开说明的训练代理，不是所有层头真实相同保留，也不能据位置缺失断言信息不存在。
- 实际KV评估脚本确有压缩缓存路径；KVzip的masked-key实现保留full-size缓存形状，与物理gather删除须区分。其他物理压缩路径的位置适配需额外核验，不能据静态疑点否定其headline KVzip结果。
- 拒答heuristic前200字符搜索标记，包括`based on the context provided`一类可出现在正常回答中的短语，且在判断gold正确前判拒答。构造例可能误判，但尚未据此确定公开输出受影响数量或论文结论失效。
- 论文已含真实KV拒答、针对性删除和固定长度控制，高保留率仍有幻觉也为作者明确讨论。不能把这些现象重新命名为本项目创新。

## 证据与下一步

两个run的manifest/source_checks/tree/源码副本/console/launch及closure保留。下一步独立只读下载固定公开输出，核查评分误差和标签边界；任何重判须分清作者标签、规则标记、人工语义判读，不能直接将heuristic反例计作新模型安全失败。无训练或新的GPU执行快照，旧实验停止条件不变。

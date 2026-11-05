# 本轮研究审查与准确断点

**2026-10-28恢复后的最终状态。** goal重新active后在原22:07:39五小时上限前恢复同一提案，v2/v3/v4均停于工程检查；0主要输出、6工程输出。v2修复inference tensor版本计数错误；v3定位到HF将greedy默认覆盖为采样（3条工程输出无效）；v4显式关闭覆盖后缓存原生/custom一致，整段/切分在第54生成token分叉。限定teacher forcing复现前54步的两路径argmax和分叉，但不充分确定数值来源。预定工程门槛保持未通过，32题Full/NoHistory能力及压缩均未执行；task_support_gate=null。具体源码/失败/诊断/命令见[实验记录](runs/20261028-action-guard-engineering-failure.md)。不自动v5，不改门槛或换attention/精度来过线。

当前累计78run2702主要输出；本窗口19run、0新主要输出，6工程输出与诊断单列。索引`results/20261028-run-index-research-window-resumed.json`，各失败目录closure与资源`results/20261028-research-window-resumed-resource-closure.json`已保存。自有四个PID全部退出，两卡15MiB/0%、compute-app空。没有新权重/依赖/服务，也没有nano-vllm复制。此前usageLimited是历史停止点，不能说本次恢复仍被额度阻挡，也不声称跑满五小时。

## 本轮目标逐项结论

| 要求 | 当前证据与结论 |
| --- | --- |
| 核验A文献差异 | [A启动审查](PREFIX_RISK_DESIGN_GATE_20261028.md)逐项对应LTT、Pareto Testing、Risk-Controlled与CompilerKV；当前组合没有超出现有框架的实质差异，no-go。不是搜索未命中即创新。 |
| 可证伪问题、任务单位与强基线 | A文档固定独立prefix＋预定query包、分组约束/效用损失、部署可用信息；直接对照多风险LTT、逐组校准、Pareto成本选择、输入自适应策略与完整规则保护。当前契约可直接表达为现有方法，故设计门槛失败；不冻结无意义的256模型矩阵来寻找正例。 |
| 设计成立才有上限筛查 | A的256输出未启动。更窄guard用途先冻结32个不同交互、Full/NoHistory及64主/18工程单次上限；三个失败尝试均在主输出前停止。跨尝试的6条工程输出全计入，不隐藏采样错误。 |
| 保留失败与停止条件 | v1加载前用量停止与v2/v3/v4工程失败均保留；CPU/来源网络/精度假设等旧失败不覆写。全部旧安全/IFEval/TREC停止门槛保持。 |
| 不为额度扫参 | 未更换prompt/数据/seed/精度/attention或扩展矩阵。限定teacher forcing只是重放已存在的53个共同token、检查第54个logit，无新生成答案。 |
| 文档与证据、go/no-go | A当前方法no-go；C宽泛拒答/充分性不立题；D工程未通过、任务支持未知、新颖性未建立。STATUS/WORKLOG/HANDOFF/PLAN及run记录更新同步，原始数据只服务器。 |

这里完成的是本轮研究审查与否定判断，**不是完成一个已成立的论文课题**。后续需要独立的新问题/设计，不能将尚未测得的guard历史依赖直接写成KV安全发现。以下为首次收尾的历史过程。

2026-10-28，新加坡时间17:07:39开始，用户要求按建议工作至5小时额度用完。平台在约19:48报告当前goal为`usageLimited`，因此收尾停止；未到22:07:39的五小时墙钟上限，不声称“五小时已经跑满”。本轮不以消耗额度为由重复旧矩阵。

## 已得到的判断

1. **候选A当前方法主张no-go。** 分组/多query/约束与效用联合预算可以归约到已有LTT、Pareto Testing及输入自适应策略校准；原256输出建议不执行。882项CPU概率检查通过只说明构造计算正确。见[启动审查](PREFIX_RISK_DESIGN_GATE_20261028.md)。
2. **候选C宽泛表述不立题。** 压缩后拒答、充分性判断、答案与证据支持分离、失败诊断均有直接近邻。作者公开926条实际KV输出及400条标签核查的复算没有形成推翻其结论的证据。见[来源与候选边界](ABSTENTION_SOURCE_FINDINGS_20261028.md)。
3. **Qwen3GuardTest不适合长历史首次预警问题。** 所有记录只有两个消息；首危险句起点最晚322token，512之后0条。没有为凑长度添加填充，没有下载此模型权重。
4. **动作安全guard是待验证用途，尚非创新。** StepGuard/StepSafe/TRACE/ToolSafe已研究动作判断、及时干预及证据聚合。当前只保留一个可证伪问题：未来动作未知时，固定实际KV预算丢失历史授权/条件，是否造成错误放行，并且简单完整指令保护/窗口/整步保留/检索不足以解决。尚未得到该问题的模型证据或新方法。

## 已完成的准备

- ToolSafe固定commit46358fa...的AgentDojo-Traj四文件1220记录逐LFS SHA核验；StepGuard原生前端/评分相关源码固定93b580b...，仅执行白名单内纯文本序列化与判分定义，不执行代理/工具/训练代码。
- 固定32个不同交互，安全/不安全16/16，banking/slack/travel/workspace各8；历史512–4096token、至少两先前动作、整输入不超8192。输入完全冲突0、原生前端错误0；不是独立确认集。cases SHA `a6fb2db4ef05eebd622d5d4ee8afb1393f7c5beaf048820e71e742cc7ded43ab`。
- 公开SFT3000/RL4000输入已读取并核对哈希；32例完整prompt及完整三字段匹配0。不能据此证明无语义/模板/预训练重叠。
- StepGuard固定HF revision`c7e4a2c9c34c09efbba0e66a6b802e08b4384662`，36层Full Attention GQA，meta形状与checkpoint索引匹配（仅tied lm_head键差）。BF16 KV理论147456bytes/token。没有实际模型forward或输出验证。
- 权重及10个加载/许可文件共8,056,473,628bytes已在服务器校验完成；模型与训练/评测文本均不下载本地，无新依赖安装。

## 停止点与恢复规则

`results/20261028-action-guard-full-gate-v1`状态`stopped_session_usage_limit`。核对自有PID3368363后SIGTERM，父进程wait -15。停于加载前预检：execution_snapshot不存在，0主要输出、0工程输出、task_support_gate=null；不是能力失败、工程通过或压缩结果。

固定提案[configs/action-guard-full-gate-v1.json](../configs/action-guard-full-gate-v1.json)保持`execution_enabled=false`，SHA87e27b70...；runner SHAef898229...。最多64主要输出（32×Full/NoHistory），工程首3例两条件三路径最多18输出，max_new512、greedy/BF16/SDPA、GPU0。不借此启动任何压缩。

后续若会话用量允许继续：先核对最新文档、文件SHA及GPU/进程；用**新输出目录**重启同一固定Full-only关卡，保留本次停止记录。Full至少24/32、两类各12/16、32个唯一完整Judgment、无错误/截断；至少8个Full对/NoHistory错且至少4个unsafe被NoHistory误放行，才说明具有描述性任务支持。失败后停止，不搜索模型/提示/长度/seed。NoHistory改变输入位置和长度，不能称为KV裁剪。

## 运行账本

本工作窗口新增16个run（来源/CPU/下载/失败/停止均计入），主要模型输出0；累计75run2702旧主要输出，索引`results/20261028-run-index-research-window.json`。所有原始结果、失败、源码/配置副本、console/launch/closure只服务器。另记服务器直接HF元数据网络不可达、一次临时诊断变量遮蔽失败；改用官方Windows元数据交叉核验固定镜像字节，未将网络失败隐去。

收尾自有runner已退出，两卡15MiB/0%、compute-app空，无新服务/端口/tmux/计划任务。旧TREC校准结束、AccessDenied失败gate保持；其他会话新增Governance Decay讨论文字保留。当前不支持论文创新、一般安全保证或稳定方法优势。

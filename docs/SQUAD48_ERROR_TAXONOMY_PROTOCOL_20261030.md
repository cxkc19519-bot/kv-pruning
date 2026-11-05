# 原48组既有输出的离线错误分型协议

2026-10-30，用户要求“开始下一步”。范围限既有GPU run的138个主要回答和全部144计划格，不生成新回答，不读模型权重/元数据、不加载tokenizer、不查GPU、不联网或安装依赖。原GPU run、scorer、主要估计量、CI、停止线、prompt/gold/预算均保持不变。

本分型在看到上一轮汇总结果后制定，明确是探索性描述，不是新的确认性假设或预注册实验。新协议/代码在执行本次离线汇总前冻结SHA，只保证可复核，不能反推为看到模型结果前已注册。

## 冻结输入与执行

服务器根`/home/user/jhk/project/Directional Exploration/kv-pruning`；唯一新CPU run `results/20261030-squad48-error-taxonomy-v1`。[配置](../configs/squad48-error-taxonomy-v1.json)列10个固定输入：原GPU原/后验manifest、summary、scored_main、normalized_outcomes、statistics_plan、group_statistics、scalar_report、独立核验，以及原selected48。逐SHA读取并核验原GPU归档全部194工件；原始文本、问题/gold及示例只在服务器。

新analyzer、独立validator、本协议及沿用的group统计validate/既有独立scoring helper均锁SHA。执行须显式CLI `--execute --proposal-sha256 ...`，外层看守标记。CPU60秒、外层90秒含独立复核、TERM10秒后KILL自己创建的组；32文件/16MiB。标准库，禁止bytecode写入、重型库/tokenizer导入、socket/子进程以及run之外写入；guard事件非0失败保留，不重试换规则。独立validator不import analyzer或主scorer，独立从文本和gold重判原评分，再用状态表与EM×format四格重算分类、完整分母、流转和示例选择。

## 穷尽且互斥的主分类

先按执行状态，再截断，再任务候选是否可评分，再EM/格式两个布尔轴，顺序不得根据类别频数改变。

| 分类 | 条件 |
| --- | --- |
| budget_infeasible | 原执行状态infeasible_budget，无生成，语义N/A |
| execution_error | 原执行状态error，不当作完成输出 |
| not_run | 原not_run或protocol_stopped，不作效果0 |
| truncated | 实际ok但truncated=true；原EM/F1/格式保留，不划为已完成成功 |
| task_unavailable | 已完成但task_EM=null，格式仍按原scorer保留 |
| joint_success | 已完成、EM=1且format=true |
| task_only | 已完成、EM=1且format=false |
| format_only | 已完成、EM=0且format=true |
| neither | 已完成、EM=0且format=false |

9个合成软件用例E01–E09覆盖全部分支，尤其“原始正确但截断”与任务N/A不能混入任务错误。EM不匹配是冻结基准评分结果，不是人工认定事实错误；F1的正/零token重叠也不是语义或幻觉标签。

## 次级诊断、配对与示例

对每条件全部48格计主分类，保留raw scorer reason及原始分数。另对**已完成**格式违规输出按冻结reason映射：普通文本、JSON字符串/标量/数组的根类型错误、object没有string answer、object额外key/空答案、结构化解析失败、BOM/重复key/非有限数/Unicode失败。只描述原解析结果，不修复JSON、不改候选提取、不判“可恢复成功”。截断输出的raw原因另留，不能混作已完成违规。

按全部48组交叉Full主分类与每个压缩主分类，报告所有非零流；另列原Full联合交付31组的后续去向，明确该31只是描述性切片，不取代all48主要分母、不计算新子组CI或显著性。只看总joint为0不能推出任务候选都不正确、不能说明两个方法完全相同。

示例固定选每个condition×主分类中case_id字典序前2个，最多54条。是看完结果后的说明性选择，不当代表性新样本、统计验证或调参材料。完整问题、gold与模型文本只存server_only_examples.json；本地文档最多引用case ID、类别和汇总，不带原始输出。

## 收尾与交付

独立复核138原文本评分、144格分类与身份、各条件48分母、全部配对流和31组切片、9软件用例、示例确定性选择、源/原manifest不变。失败则保留错误与退出状态，不改原GPU输出或本分型规则救回。

通过后更新STATUS/WORKLOG/HANDOFF、run记录和readiness；新增本地分析文档与论文章节证据映射，区分“已有实测”“系统软件验收”“尚未验证”。论文组织不等于宣称创新或毕业认可。所有原始/示例产物只在服务器，代码配置文档同步；旧QA/Mistral false和保护/3/4/BoolQ/旧16停止保持，没有GPU队列。

# H3固定12开发组有界诊断协议

2026-10-31，用户“继续”在共同batch契约已验后推进固定开发筛查。此为当前方向的单次go/no-go诊断，不是确认实验/新算法或安全评测；所有结果允许负向。原12组/题目/标签/位置/预算/seed在任何开发模型输出前已固定，不选题补样、不改prompt/预算找信号。

前置证据：common-batch-engineering-v1两组Full+8候选正反序重复，36向量逐字节相同，prefix hook/nohook cache/logits相同、mask/gather/1008efficient调用与目标复算通过。旧whole/split/tokenwise0.25/0.001数值门槛仍failed；本轮只研究明确的共同批量后缀缓存执行过程，不称整段原生模型的数学等价。

## 固定输入与流程

原生CPU冻结development_00–11共12组，2工程组不重跑。24条路由事实/组，target位置0/12/23×gold A/B/C/D，三位置各4组、标签各3组。每组prefix373、相同query+wrapper24；显式bool causal mask遵守common-batch契约，原RoPE逻辑373..396/物理Full373或compact186。实际Qwen28Full/GQA4/BF16/SDPA/TF32off和GPU1、4权重7metadata及包SHA在新run核查；先24次native HF编码，0生成token/完整文本答案。

先对全部12组各算scored prefix+Full batch末logits，只以合法{32,33,34,35}argmax唯一匹配gold定义Full正确。这是强制枚举首分支能力，不等自由生成JSON/长序列任务质量。Full≥10/12才允许裁剪；失败保存全12输入/Full错误/候选待运行状态并停止，不能换题/模型或放宽支持线。

通过后重算每组prefix，其cache SHA、prefix score SHA与候选maps必须逐项重现Full阶段；不复用Full suffix KV。8候选固定：prefix WindowScores64/kernel5对28×4分数float64均值后的适配Snap1、recency1、Random seeds2026103101–06。每候选186槽，68锚点收费、其他118；保存全部候选，不挑最好seed。此Snap适配不是原版per-head SnapKV；随机相同长度可同位置，不当独立replication。

## 目标与开发停止线（输出前固定）

每组P为Full向量，Q为实际候选。J_global、J_Full-top128、J_Full-top256、J_legal均为对应support重归一化的KL(P||Q)，合法集合固定语法而非gold；目标计算不能见gold，gold仅最后评分。每目标按8候选固定顺序择最小；分数差≤1e-8视为近并列，记录所有候选，固定顺序只用于显示，不以并列制造提升。若近并列候选的Full-argmax保真不同，该组比较记ambiguous_tie，不计win/loss。

报告：全部12组/96候选的四目标、合法argmax/gold、任意成对排序反转、目标所选缓存的Full-argmax保真、每基线对legal的赢/输/平/并列不确定。反转要求两个目标差值均>1e-8且符号相反，纯数值近零不算实质反转。工程例没有普适误差界，1e-8只是预注册的软件近并列约定，不是统计保证。

只有≥3组发生legal与任一基线的实质排序反转，且legal相对global、top128、top256**每个**都至少2组保真改进、并且各自win>loss，才保留为值得另做独立审查的开发信号。这个条件落实原草案“通用TopK若同样解决就停”，不是发表/功效门槛；原宽草案未执行，不在结果后挑最弱基线。未达则结束当前H3候选，不扩样本/seed/预算/模型救回；只有分数排序不同而决策无益不够继续。

## 资源与复核

Full阶段24 forward/4764输入token/12向量；若通过，总132 forward/11544输入token/108向量（含Full，非108独立样本或完整答案）。worker600/verifier180/outer850秒；≤256文件/256MiB，score/map/raw f32/Full及候选结果只服务器，不存全部main KV快照，工程已有物理gather证明且worker每次仍逐值断言/实际bytes/reference hash。使用checked finalizer，先核上限后写complete，失败不覆盖原run。无profiler重跑，无后端/精度切换。

独立stdlib validator从108或12原始f32向量重算Full支持与全部384 KL/argmax，重建prefix score聚合和所有候选、实际mask字节/trace，重判所有转移和go/no-go，重核4权重7metadata。不导入worker或项目评分函数，无额外模型/分词。允许数值复核差1e-8，仅软件比对，不把其当研究置信区间。最终应报告能否继续，并同步STATUS/WORKLOG/HANDOFF；0完整生成答案不重复增加历史3038主回答数，logit向量和分支决策另列。

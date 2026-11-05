# 组级统计软件验收协议

日期：2026-10-30。用户在已授权实验会话要求“开始下一步”。本轮只实现和验收统计软件，不加载模型、tokenizer、权重或使用GPU，不获取网络数据。原始输入和运行产物仅在服务器。本协议不恢复旧QA、Mistral或封存推理队列。

## 冻结与执行边界

原[提案](../configs/group-statistics-acceptance-v1.json) SHA `b1e9d0420b530a745f84a4a72435bdf25238cb7b7916d2177279cb8bf0cc3126` 的execution/implementation=false历史字段不追改。实际实现与CLI由新的[执行登记](../configs/group-statistics-execution-v1.json)绑定：统计模块、runner、独立validator和本协议的完整SHA须在执行前同步核验。登记本身以SHA传入CLI，服务器输出保存原提案、登记、源码快照和实际argv/Python版本。

服务器根：`/home/user/jhk/project/Directional Exploration/kv-pruning`。唯一新run：`results/20261030-group-statistics-acceptance-v1`。输入仅提案已列的范围合同、原48题CPU coverage、144格预算计划及其独立核验，逐SHA重读，不读取任何模型输出。软件用例是合成数据，不充当真实样本。

runner CPU上限60秒；外层90秒包含runner与独立核验，超时先TERM、10秒后KILL，仅操作自己创建的进程组。独立核验自身60秒上限。归档连同后验工件不超过32文件/16MiB。不安装依赖、不启动服务。运行只使用既有`.venv/bin/python`标准库，禁止bytecode写入。

runner审计hook拒绝模型/tokenizer库导入、socket操作、子进程/系统命令、模型目录/权重后缀打开与run目录之外写入；拒绝事件必须为零，否则本run失败。独立validator不导入项目模块，仅标准库复核其序列化工件。外层launcher自身调用两个受限Python子进程是已登记流程，不属于被测runner内的子进程许可。

## 统计合同

`reliability_group_statistics.py`接收明确的计划与规范化标量行。计划绑定cohort、case、唯一context_group、唯一role、input/gold/comparison三摘要和条件。每组恰好一题，所有条件必须有且仅有一行。重复/缺失/外来格、摘要错配、重复/跨角色group拒绝；excluded group列表不能与分析组相交。任务EM必须为数值0/1，F1为有限[0,1]数值，二者拒绝bool；null须有原因。format/truncated严格bool；未执行行的任务、格式、截断必须为null。

规范化统计行`kv_group_outcome_v1`是独立分析入口，不等于现有scalar core的原始schema。未来GPU协议须显式生成并绑定这些字段；本轮没有改旧core/调度器，也未允许任意旧输出注入。唯一当前数据adapter只接受仍not_run且model_called=false/指标全null的原生计划，并强制pending报告。

主要估计量为method相对共享Full的joint交付率差，分母是全部计划group。joint要求实际成功返回、未截断、format=true且task_EM=1。已终态预算不足或错误交付记joint0，任务语义仍N/A。截断原始分数保留，但严格语义配对不可用、joint0。没有任务候选也不把null变成“语义错误”。另报全部执行计数、预算不足、任务覆盖、四种转移、可配对Full正确分母、严格条件损坏率与覆盖边界；分母零为null。

仅phase=complete、full_support=true、全部计划格为终态时计算主要差值与区间。pending/not_run/协议停止或Full支持失败只返回描述计数，不产生主要差值/CI；不能把当前144个未运行格当零效果。

按context_group排序、所有条件共享同一组索引抽样；10000次、seed20261030、95%逐项percentile、type7线性分位 `h=(B-1)*p`。记录完整抽样索引流SHA、排序及方法，不选最好seed。区间不是同时多比较保证或总体风险认证；48篇文章的精确去重也不是语义/预训练独立保证。G02显式枚举只有4次，不声称它做了10000次。

## 固定18用例与独立复核

用例ID、语义和期望来自原提案G01–G18，不能根据运行结果换用例。G01配对差值0/-1/2；G02四次精确枚举[-1,0,0,1]的区间[-0.925,0.925]；G03–05常差值0/+1/-1；G06预算不足、G07截断原始正确、G08格式有效而任务N/A；G09–13共13次拒绝变异覆盖重复、缺失、三摘要、重复/跨role/excluded组和bool/NaN/Inf；G14同seed两次及条件/行/组顺序置换一次完全相同；G15三种停止/未完成只描述；G16 Full正确分母零为null；G17分位端点与插值；G18当前48组/144计划的预算与未运行状态。

runner归档每个fixture输入、JSON安全的非法变异说明、实测错误、报告和抽样流摘要。独立validator不调用模块或runner，直接重算11份完整合成报告的全部条件计数、joint差值、严格转移/分母、完整10000次共享抽样流以及以Fraction有理插值所得type7区间。另核G02精确枚举、13次错误、G15不产CI、G17边界；重读原144计划独立核Full48可行、Snap/随机各45可行+3不足且所有格not_run。全部输入、源码、原manifest回读SHA。若任何失败，保存错误、原始manifest和launcher退出状态；不调阈值/换题/重新生成回答。

## 通过后

只可宣称组级统计实现通过这18个软件用例，原48题未计算模型效应。另行冻结GPU阶段的角色、输入/runtime绑定、当前cohort工程证据、Full支持/停止线、最多138主要回答和14工程资源预留的实际使用规则。原48组/144报告格保留6个预算不足，保护/3/4/BoolQ/第二模型压缩仍不启用。代码文档同步服务器，GitHub未配置。实际命令、结果与失败另写公共模板run记录。

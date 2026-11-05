# KV 压缩约束可靠性评测系统需求与验收

2026-10-30最新：[Mistral当前QA Full](runs/20261030-mistral-squad-full.md)实现并核真实32Full/GQA8/BF16/SDPA、131072bytes-slot、cache clone/reference及两题三路径通过；不等第二模型compact已迁移。6工程+12DEV完成，任务7/12/格式8/12/joint6，零截断错误，格式低于预设9导致Full支持false，禁止自动接压缩/保护/封存。18文本/193trace/3权重独立核验通过，保留4json_string格式失败而不放宽判分；工程成功与任务支持失败分开入矩阵。下一步离线收敛研究最小独立证据范围，当前无模型队列。

2026-10-30最新：[两模型CPU前端验收](runs/20261030-independent-frontends-preflight.md)通过：32model-case/48native变体/96编码及128预算状态独立复算，Qwen原14条精确回归；Mistral完整native系统折叠和保护范围已验，仍不等真实cache/任务或压缩验证。完整保护DEV半预算Qwen2/12、Mistral3/12，3/4均12/12；工程池覆盖与DEV覆盖分开，原两工程含不可行不可自动设pass。v1被阻止的回环探测归类失败留档，v2准确记录、仍阻止所有socket并收紧HFsymlink文件白名单。验收矩阵A02更新为scoped CPU前端通过，A03真实MistralKV/3/4后端仍部分。下一步另冻Mistral Full-only≤18回答，0自动GPU。

2026-10-30最新：[验收矩阵](SYSTEM_ACCEPTANCE_MATRIX_20261030.json)列出11项已验/部分/未测要求。Qwen/同12DEV系统链已过，Mistral当前QA原生前端、保护工程、3/4、独立组、生产峰值/时延和统计不确定性仍缺。下一步按[新推进方案](INDEPENDENT_EVIDENCE_PLAN_20261030.md)先实现禁用CPU提案的两模型native边界与预算覆盖，0权重/推理；不把文件存在/描述符字节或旧权限任务Full通过称新后端通过。本轮仅只读核验16metadata，未新增实验/依赖或修改旧结果。

2026-10-30最新：[DEV系统集成验收](runs/20261030-hf-DEV-acceptance.md)通过。可审计恢复同生成器scope的14旧工程观测，0工程新调用，8恢复软件用例；真实36DEV及24阻止格全部经过调度，任务/格式评分与60格统一报告独立重算一致。v1整份config比较因id2label键JSON类型失败0生成留档，v2仅JSON规范化完整配置后比较；科学判据/输入/数值生成器不改。截断1/N/A1/20预算不足/4证据不足和损坏覆盖保留；不把未执行项当语义失败或安全成功。当前主链验收完成，接下来是独立实证设计，不继续重跑同12DEV。

2026-10-30最新：[新后端GPU工程验收](runs/20261030-hf-backend-engineering.md)完成：同两工程题14回答605token，新旧逐token/终止/trace一致，3条件verified/2保护预算不可行未验；25输入、563trace步/448map/224Snap排名与模型hash独立核验。1Snap工程case在cap截断，不当完整输出或任务支持。当前scope真实形成工程证据，DEV60格仅准入36/预算阻止20/证据阻止4，DEV调用0。下一步另冻36格系统端到端验收；保留不可行/N/A/截断与分母，0保护/封存，不作新独立科学确认。

2026-10-30最新：[HF编排验收](runs/20261030-hf-orchestration-dry.md)22项软件检查通过。已接到延迟HF后端入口：工程bootstrap独立于DEV门槛，input/selector group/runtime绑定，预算/旧证据/角色/资源开关/重复请求均在加载前核验。新版本60DEV格20预算不足、40待新工程，不能继承旧36eligible；计划14工程调用并不构成工程观测。主dry plan工厂/执行0，另2负向真实入口测试加载前拒绝；0模型加载。下一验收是新冻结14工程回答GPU协议，0DEV/封存，实际数值/trace/runtime尚未验证。

2026-10-30[条件级准入接口](CONDITION_ADMISSION_20261030.md)及[20用例/60格CPU验收](runs/20261030-condition-admission.md)已完成：budget与condition-scoped工程证据都成立才允许正式运行，未生成/历史诊断不隐去；token/trace在cap内相同不等任务完成。未来准入36/预算不足20/证据不足4，4条旧保护DEV原样保留，旧gate不改。dispatcher仅stub边界验证，真实HF编排尚待接线；首次工程bootstrap须独立有界协议，不能由DEV门槛自锁或绕过。下一步仅dry-run，不把软件接口通过说成生产后端改造完成。

2026-10-30[新SQuADtrain12DEV](runs/20261030-independent-development.md)把通用报告接到新模型输出：60计划cell中40生成、20预算不可行，严格任务/格式/F1及交付率分母显式保存。完整保护并集120槽导致10/12DEV不可行；两个保护工程题也均不可行，因此不能由总engineering_gate=true推断每条件路径验证通过。下一系统增量须有条件级admission与engineering evidence范围，将infeasible/not_run/已生成路径验证分开，用固定数据CPU验收；不要补预算/过滤短题或仅报告2/2格式。旧gate/旧报告保持，BoolQ源403与软件20用例分开记录，跨任务/第二模型与生产成本未完成。

2026-10-30[系统模块化第一版](RELIABILITY_SYSTEM_DESIGN_20261030.md)与[首轮验收](runs/20261030-reliability-system-archive.md)已完成：四新标准库模块定义schema/配置身份/不同layout字节描述符/精确保留率保护收费/通用布尔和连续指标报告，16验收用例与三cohort290历史记录严格结果一致。原固定Qwen generator保持，通用HF后端/第二模型/独立数据与生产式成本计量未完成；不可把描述符软件通过等同新模型tensor验证或历史回放等同科学确认。下一条依据新实证草案先准备SQuADtrain/BoolQ来源与CPU判分/分组，旧QA关卡与封存不改，当前无新GPU任务。readiness分开标已过/未过阶段。

2026-10-30[新任务生成与配对报告已完成受限验证](runs/20261030-answer-format-direction.md)：固定Qwen2.5-7B/28 Full/GQA4/BF16，原生边界与半预算、2题Full三路径及4条件compact native/custom通过，80主输出同预算/位置信息和6报告软件用例及独立逐行复核通过。新adapter实现F1适用分母、N/A/截断/全部cell及Full正确损坏覆盖范围；旧reliability_report.py不改。driver仍固定任务/16题与28/4，不能称跨模型通用平台；峰值/额外buffer/时延未测。随机1截断使预定全局确认gate false，完整论文尚缺独立验证与系统验收，当前无GPU队列。见可行性结论，不能把实现通过冒充论文创新或普遍安全结论。

2026-10-30新增[阅读+JSON任务预检](runs/20261030-answer-format-task-preflight.md)完成：新标准库gold-blind scorer与数据准备通过24评分/6数据用例及完整原始标注/文章组独立复核。[readiness](ANSWER_FORMAT_TASK_READINESS_20261030.json)是新任务当前状态；CPU通过不证明token边界、真实KV/保护预算、Full能力或第二模型。报告层仍只支持历史TREC，新任务F1/N/A/损坏上下界adapter尚未实现；不把scorer通过冒充报告扩展通过。旧冻结proposal及源工件不改，下一条先tokenizer/config检查，再另冻Full-only。

2026-10-30新增数据/评分适配契约见[阅读+JSON任务](ANSWER_FORMAT_TASK_CONTRACT_20261030.md)。它分开定义gold-blind内容候选与格式、N/A/覆盖/Full正确损坏上下界，独立文章组角色及Full最低支持停止条件；旧TREC adapter不能直接使用，新增scorer与F1/report adapter尚未实现。下一步只实现并审服务器CPU预检，不改既有报告/旧输出或启动生成。数据、24评分+6数据用例均未运行，当前无新实验。

实现更新：2026-10-30[标准库报告模块已完成回归](runs/20261030-reliability-report-replay.md)，9输入/210规范化记录/两cohort两口径及12软件fixture通过。v1后审查补齐legacy方法失败的分母语义，v2通过；legacy分母为所有可用Full正确数、strict为可比较Full正确配对数，两者均显示eligible/unassessed。本文“未实现/运行”是设计时点，当前以后续记录为准；生成/新数据/第二模型及真实性能测量仍未覆盖。

2026-10-30。系统面向[选题稿](THESIS_CONVERGENCE_20261030.md)中的具体问题：同实际KV预算下，压缩与完整指令保护怎样影响约束遵守及任务正确性。首个版本先形成可复核的报告层，再逐项接入生成、真实内存及新任务；已有单模型脚本不是通用平台。

## 1 系统边界与首个交付

已有实现使用HF、Qwen2.5-7B、BF16、batch1及实际前缀K/V gather。起点是离线处理现有结果：读取已固定输入及判分，按case配对Full与压缩，验证预算口径并产生报告。首版不导入模型库、不重新解码/判分、不读取`.pt`、不生成回答；因此报告层通过不等于新任务或后端正确性通过。

系统依次包含四个可单独验收的部分：数据与配置契约、版本受限的生成/裁剪适配器、约束与任务双判分、独立配对报告与归档。首个实现只覆盖最后一部分及其输入适配。暂不做Web界面，不把vLLM控制器和dummy计时当HF裁剪后端。

## 2 既有实现盘点

下表依据本地源码及服务器同SHA文件的AST/文本检查；只读取文件，不执行这些模块。完整SHA见第7节配置与源码校验说明。

| 文件与关键入口 | 可复用部分 | 需要适配或保留的限制 |
| --- | --- | --- |
| [trec_pruning_utils.py](../scripts/trec_pruning_utils.py) 13–95：anchors、随机评分、选择、校验、gather、kv_bytes | 明确锚点/保护占预算、稳定tie-break、逐层逐KV-head索引及真实K/V元素字节求和 | batch1、相同K/V形状与DynamicCache布局；不覆盖分页/量化/卸载 |
| 同文件98–135：native_header_metadata | 精确原生文本span、offset重叠token及完整覆盖核验 | 写死Qwen模板标记；预算直接`prefix_tokens//2`，不能直接换chat模板/保留率 |
| [trec_context_gate.py](../scripts/trec_context_gate.py) 40–115 | 缓存克隆/版本检查、prefill、native/custom参考及TREC判分定义 | prefill固定28层和57344 bytes/token；判分器固定官方blob，含动态编译，首版报告不能导入 |
| [pilot.py](../scripts/pilot.py) WindowScores 41–66 | 前缀末窗口注意力评分，现有适配SnapKV依赖 | 访问self_attn/q_proj/RoPE字段，不能按模型名假定兼容；不是作者完整复现 |
| [trec_pruning_run.py](../scripts/trec_pruning_run.py) 35–110 | hook一致性、逻辑RoPE与物理位置分离、native/custom压缩参考、四方法map | 固定28层/4 KV heads/半预算；report写死32题、19 Full正确分母 |
| [trec_holdout_run.py](../scripts/trec_holdout_run.py) 31–61、64–229 | Full→支持门槛→压缩门槛的阶段执行、失败保留、逐cell状态 | 题数10、50主/24工程、字节常数及既有来源SHA固定；summarize不会拒绝重复identity，字典可能覆盖重复行 |
| [analyze_trec_pruning.py](../scripts/analyze_trec_pruning.py)、[analyze_trec_holdout.py](../scripts/analyze_trec_holdout.py) | 独立解码/判分、map/位置/字节审计及预期数量检查 | 固定128/50输出、32/10题及28×4形状；依赖torch/tokenizer且要求旧目录中尚无analysis文件，不能直接复用为只读通用报告 |
| [prepare_trec_holdout.py](../scripts/prepare_trec_holdout.py)、[freeze_trec_holdout.py](../scripts/freeze_trec_holdout.py) | 来源标签/重复冲突/使用历史/示例重叠检查及冻结提案 | 原42合格取剩余10，带历史专用路径及网络准备；只能借鉴流程，不能重新执行旧冻结 |
| [synthesize_trec_calibration.py](../scripts/synthesize_trec_calibration.py) | 开发与留出分别汇总、四转移、保护干预对比 | 目录/32/10固定，目标写回已完成旧run且拒绝覆盖；新系统必须写新目录 |

本轮核对10个文件的SHA和函数位置。所读主runner没有逐请求峰值显存、裁剪/生成阶段耗时字段；整体start/end包含加载与检查，不能据此报告纯推理性能。保存的score/map可支持额外审计，但其存储体积不等运行时GPU占用。

## 3 数据与预算契约

### 3.1 可配对的记录

新报告的唯一键为`(cohort_id, case_id, condition_id)`；模型/解码/预算等条件也须由condition绑定的配置hash识别。同键重复即失败，不用字典保留最后一条。Full与压缩须具有相同case来源、gold版本、完整input ids hash及可比生成配置；条件差异必须是协议声明的干预。

| 新报告字段 | 旧字段或来源 | 缺失处理 |
| --- | --- | --- |
| cohort_id / split_role / context_group_id | 外部冻结配置；旧数据只声明development32或已使用的question_holdout10 | 不推定上下文独立；group未知时不算独立置信区间 |
| case_id / condition_id / input_sha256 | source_key / method；开发Full需将condition=with_demos映射成Full / input_ids_sha256 | 显式adapter映射，禁止把without_demos误配为Full |
| provenance | manifest、源码/模型/数据/tokenizer/生成配置及输入文件SHA | 必需身份不全则不能宣称可比；旧字段不伪造 |
| execution_state / reason | status、计划cell、错误/阶段停止记录 | planned但无结果是not_run；error不当任务错，也不删除 |
| truncated / termination | truncated、terminated_eos、generated_tokens | 以旧记录为准；成功返回与完整输出分开 |
| task_result | metrics.exact_correct | TREC含整段严格标签匹配；不冒充纯语义准确率 |
| constraint_result | metrics.whole_response_label_format | TREC为`text.strip()`属于标签集；不能称一般安全合规 |
| compatibility_result | metrics.official_firstline_compatibility | 单独显示，不替代严格主指标 |
| KV与位置 | prefix_tokens、physical_prefix_slots、suffix_tokens、prefix_kv_bytes、final_live_kv_bytes、position_trace及外部map | 开发Full无final_live字段时为unknown；禁止从不兼容记录补猜 |
| protection | 条件配置、header_budget_metadata、实际map | 留出row无pin字段，从已核条件配置读取，不从输出推断 |
| peak/latency/extra_cost | 旧逐例数据未测 | `value=null, reason=not_measured`，不填0或由运行总时长代替 |

新结果保留`metric_id/version/applicability/value/reason`。TREC严格正确与标签格式在逻辑上并不完全独立，任务正确通常蕴含格式合法；双指标用于区分损伤，不能包装成两个独立实验。将来语义评分、JSON schema或其他约束接入前，必须各自定义评分域与测试，不直接沿TREC布尔含义。

### 3.2 实际KV预算与额外成本

比较固定在同case的前缀裁剪后时点，prefix字节为所有层K/V元素数乘dtype字节之和；保护span和共同sink/recent从同预算扣除。Full是无压缩参照，不与压缩候选强行等量。保护+锚点并集超过预算则标`infeasible_budget`，不偷偷增加保留量或仅保部分指令。

旧Qwen2.5-7B的57344 bytes/token来自28层/4 KV heads/128维/BF16及K+V，只作为该配置的审核常数。跨模型必须从实际形状/dtype重算。相同保留比例不保证相同字节；相同prefix字节也不保证生成后总KV相同，因为输出长度可能不同。

裁剪当前先生成完整KV再gather，峰值可能同时包含完整与压缩缓存。实际峰值、allocator reserved、索引/评分buffer、prefill/裁剪/解码耗时须未来分别测量并标时点；仅prefix字节减少不能写成整进程显存减半或吞吐提升。新报告先明确显示这些未测项。

## 4 指标与验收规则

报告同时保存历史口径与新严格口径，使用不同profile名称。`legacy_exact_replay`仅复现已有status/判分定义；`strict_complete_pair_preview`要求两端status=ok、未截断、指标适用且身份匹配才进入配对。不可把预览结果写回旧分数，或将新规则静默套在历史结果上。

| 验收ID | 要求 | 首版如何验收 |
| --- | --- | --- |
| R01 | 输入与来源可核对，输出不改旧run | 固定文件SHA先验，写新目录；前后旧manifest与数据hash不变 |
| R02 | 配对无混淆、无静默丢行 | 重复键、input/gold不一致为硬失败；按固定case×condition计划报告所有cell |
| R03 | 分开约束/任务及相对Full变化 | 四转移C2C/C2W/W2C/W2W分别计数；Full错题仍在完整表，净分不能代替逐例损坏/改善 |
| R04 | 分母由可用记录计算，0分母不是0风险 | 报scheduled、ok、error、truncated、not_run、指标N/A；配对数及未评估的Full正确数另列；分母0时率为null |
| R05 | 条件损失不掩盖方法失败 | strict条件损失=C2W/完整可评分且Full正确的配对数，同时列所有可用Full正确数与其中无法比较的数量，覆盖不足不宣称安全 |
| R06 | 等prefix预算可验证，保护不免费 | 同case压缩条件prefix_kv_bytes不同即比较失败；旧元数据覆盖核验只沿原有审计证据，首版不加载map tensor冒充重新审计 |
| R07 | 历史与确认数据角色明确 | 32与10独立表；两者均已使用、示例共享，不合并作独立42样本推断 |
| R08 | 工程通过状态可追溯 | 指向旧工程检查文件及其SHA/范围；首版报告通过不扩大至第二模型/新采样/新长度 |
| R09 | 缺失成本不被当成性能优势 | 未测peak/latency与额外buffer以null和原因显示；不输出虚构的时延或显存节省 |
| R10 | 失败与不适用可复现 | 独立软件fixtures检查重复键、零分母、缺cell、截断、未知指标、预算不足、损坏/改善相抵等；fixtures不作模型证据 |

截断是一个正交标记，可能已有判分，必须保留原值；严格配对排除后仍显示其数量与原因。N/A分为“未有输出不能评分”“约束本身不适用”“证据未记录”，不合并成错误或成功。初版不为不完整数据补token/猜答案。

## 5 固定回归材料与预期结果

首版只读以下三处既有run。开发Full来自独立上下文控制文件`condition=with_demos`，与开发run的baseline副本逐case核对hash/gold/ids/metrics，不当另一组样本。`without_demos`保留在原文件但不进入压缩配对。

| cohort与来源 | 记录规模 | Full任务正确/约束合法 | 四压缩条件任务正确/约束合法 |
| --- | --- | --- | --- |
| development32：trec-context-full-v1、trec-pruning-v1 | 控制文件64行中32 Full；压缩128行 | 19/32、32/32 | 适配Snap 17/31；随机17/30；Snap保护16/32；随机保护19/32 |
| used_question_holdout10：trec-holdout-v1 | 10 Full+40压缩=50行 | 7/10、10/10 | 适配Snap7/10；随机6/9；Snap保护7/10；随机保护7/10 |

以上压缩列每格为“任务正确个数/约束合法个数”，共同分母是本行cohort题数。预计strict与legacy主计数一致，因为这些旧主输出无运行错误和截断。留出随机保护必须同时报告C2W=1、W2C=1；若只显示与Full同7分而称逐例无损，验收失败。

已有真实map检查分别覆盖开发14336、留出4480个head map，旧独立排序检查1024/320；首版从已存审计引用该范围，不能将其抄成新执行的检查。软件fixtures才能验证新报告对失败状态的处理，因为两组旧主结果的失败/截断计数都是0。

[冻结的CPU报告验证提案](../configs/reliability-report-replay-proposal-v1.json)明确9个输入文件SHA、两个cohort预期和12个软件fixture。当前`execution_enabled=false, runner_implemented=false`；尚未实现或运行。将来只服务器标准库、60秒/32MiB/最多300 JSONL行/32输入文件，0生成/0GPU查询，不重新运行旧analyzer或synthesis。

## 6 新数据与研究结果的准入

旧两组仅做实现验收。下一任务设计先固定任务语义、可直接检查的输出约束、标签来源、上下文/示例族分组、split与重叠报告；不能因Full答错或某方法不好事后改标签/换题。Full支持门槛应由新任务定义，不继承旧5/10数值，也不恢复旧AccessDenied/guard失败方案。

要回答跨任务或第二模型问题，先通过对应Full与生成路径工程门槛，再在冻结输入上报告全部配对及失败。以独立场景/上下文为统计单位，相关query和共用示例不能撑大样本量；若只有描述性小样本就限制结论。模型、预算点和样本量需在新有界协议中按问题与资源固定，当前不写自动GPU队列。

## 7 实现顺序与版本保护

第一项改动应新增纯标准库的结果adapter和配对报告模块，显式传入case计划/基准/判分映射，不修改写死的历史runner。先实现R01–R05、R07、R09及与标量字节有关的R06，再用冻结材料和软件fixtures验证；成功后才设计可配置runner或第二模型适配器。数据/scorer升级与生成后端升级应分开记录版本。

盘点源码SHA：utils `92594811…`、pruning `7b9393ba…`、holdout `eb5e5819…`、context `12cffbdd…`、pilot `476b3cbf…`、analyze_pruning `c751c5b3…`、analyze_holdout `8194f754…`、synthesis `844317e6…`、prepare_holdout `9e6fdde6…`、freeze_holdout `8c8dc9c7…`。全摘要与复用判断见[实现盘点索引](RELIABILITY_IMPLEMENTATION_INVENTORY_20261030.json)。旧输入和manifest完整摘要固定在CPU提案。

本轮只有源码/字段/既有摘要读取和文档设计：0新run/主/工程回答，累计仍92run2732主输出；不计为独立样本。旧自有PID2743087/2915326/2966704不存在，未查询GPU/他人进程，环境不变。系统新模块和验收结果尚待实现；本设计不新增方法创新或一般安全结论。

# 当前状态

2026-11-05：用户指定 GitHub 仓库 [cxkc19519-bot/kv-pruning](https://github.com/cxkc19519-bot/kv-pruning) 用于项目进度同步；main 已发布并核对首个提交 17b6ab8（507 文件），新增 [进度概览](PROGRESS.md)。本次发布代码、配置和文档，保留历史失败与停止决定；模型、数据、原始结果、日志和凭据不入库。11-04 结构化输出搁置、H3 停止和泛 KV 暂停保持，累计仍为 147runs/3038历史主回答；未启动实验、安装或后台任务。仓库提交状态以 GitHub main 提交记录为准，下方“GitHub 未配置”为历史记录。


2026-11-04 当前决策：**搁置 N1 结构化输出资源生命周期分支，关闭默认后续实施。** 用户认为当前结构化方向不好做；讨论确认真实 vLLM 服务中的资源损害、结构化特有问题及现有机制不足均未建立。单线程池排队不能当作调度缺陷或安全证据。详见 [搁置决定](STRUCTURED_OUTPUT_STOP_DECISION_20261104.md) / [当前分支状态](STRUCTURED_OUTPUT_BRANCH_STATE_20261104.json)。不实施或执行旧自然观测草案，不开展取消/压力对照；旧草案、readiness、结果原样保留，下方所有“下一条实施”均为已被覆盖的历史记录。147runs/3038历史主回答不变，H3停止/泛KV暂停保持；后续先重新明确候选问题，不自动恢复旧实验。本轮仅文档维护，未启动实验或后台任务，未重新审计既有进程。


2026-11-03文献阅读整理：[精选清单](READING_SHORTLIST_20261103.md)已核对12篇官方论文/作者摘要入口，含10篇正式会议工作与2篇标记的预印本；主线10篇KV压缩/安全/风险控制，另2篇结构化输出分支。只做公开检索与中文摘要概述，未做全文/源码审计或复现。本次0实验/服务器操作/环境变化，不改变11-02资源可观测性断点、旧gate或停止决定。

2026-11-02最新：[资源可观测性审阅](RESOURCE_OBSERVABILITY_REVIEW_20261102.md)/[readiness](RESOURCE_OBSERVABILITY_READINESS_20261102.json)完成。只读重算旧typed原始6类694调用/250外部样本，最大449025ns，CPU tick10ms/采样10ms，0调用含2内部外部样本，不能分摊单调用CPU/RSS或填0；尚无真实pool原槽恢复/取消测量。独立stdlib复核通过，17源/分析文件341609bytes/635371e5…及3复核文件4638bytes/c0a5fc42…全回读。官方头仍LL3d698ee0…/Xca1acf28…，6源Git blob核对：LL Rust/C有协作取消但已审最新Python stub无cancel声明，X dynamic在源码有/安装0.2.8无；matcher的time_threshold只针对draft树遍历，不泛化编译取消。PATH cargo/rustc无，vLLM依赖LL<1.8与X==0.2.8，cgroup不可写；不能以强对照未部署当失败。已冻结a1c47d2c…自然执行观测协议，18 native job+1空控制、同pool max_workers1，宽1/2/4固定A与width1 B0/B，高分辨率process/thread clocks；不强制overlap、不sleep/扩宽/重试救信号，不注入取消，RSS不称硬回收。runner未实现/executionfalse，下一条实施、独立验收和另登记，不启动科学取消/压力对照。0新run/native/模型，147runs3038主与83bdc4b7…索引不变；runtime101+dill2/source/input与旧4PID均核，closure539035db…。代码文档同步服务器、原始仅服务器、GitHub未配置，无后台安装服务队列；N1实效/新颖性未立，旧false/H3停止保持。本条取代旧待办。

2026-11-02最新：[明确类型记录族](runs/20261102-typed-object.md)/[readiness](TYPED_OBJECT_READINESS_20261102.json)通过。独立生成器未读旧28格，事前冻结1/2/4字段required+additionalProperties=false+字符串red/blue枚举，7例各2正5负；研究者已见旧结果，开发性新范围而非独立确认集。登记57dec142…一次执行，两后端各21/21符合独立业务谓词，TP6/TN15、FP/FN/unknown0，正例均EOS停止。6schema/42matcher/646mask位置/969mask API/616commit/2347边界，时钟/bit-bias/commit无冲突，CUDA false/guard拒绝全0；导入2.578207秒/适配.002317秒/launcher3.079202秒非性能比较。输入6文件32587bytes/dd4aaa2b…，原始48文件2333563bytes/494acca2…全回读，runtime101+dill2/source/input不变，4PID全无。新增1CPUrun/42语义格/0模型回答，147runs3038主，新索引83bdc4b7…/closure4e6e9c54…。旧45/257/FF/cold5 gate仍false，当前只建立小型记录族已测样例的功能对照，资源/取消/干扰未测，N1实效/新颖性未知。下一条冻结有界资源可观测性小筛查与强对照兼容性，保留同槽正常探针、明确停止条件；不重做12/8/23/425或旧45，不以旧LL API缺失立题。当前无native队列/服务/后台/安装，代码文档同步服务器、原始仅服务器、GitHub未配置，H3停止保持。本条取代旧待办。

2026-11-02最新收尾：[原8组45实例语义检查](runs/20261101-finite-semantic.md)/[readiness](FINITE_SEMANTIC_READINESS_20261101.json)完成。11-01登记0e8a001b…单次运行，90格全保留；X31/45符合gold、FP4/FN10，LL39/45符合gold、FN2/oneOf unsupported4 unknown。共同有结果41格相同29、同时gold正确28仅描述统计，不做筛选。16schema/90matcher/415mask位置/631mask API/377commit/1771边界，接受路径48次EOS后停止，无超时/掩码交叉或提交冲突，CUDA false/guard拒绝全0，worker/独立validator/launcher0只表示证据完整；新有限语义gate false。X原生日志及对应源确认oneOf近似，缺type关键词分支解释多项差异；两者拒整数1.0，LL首个unicode escape的d处拒绝，不能断言长度算错。当前45题不具备等语义资源对照前提，资源/取消/性能保持关闭。下一条仅独立定义共同支持的明确类型schema族和事前正负例协议，不筛28格/改原schema标签/coerce/扩样本救gate，不重跑8/23/12/425。原始41文件1803891bytes/manifest681e554a…，来源8+4文件全回读，runtime101+dill2/source/input不变，4自有PID无。新增1CPUrun/90语义结果/0模型回答，累计146runs3038主；索引871a056c…/closure40699c78…，旧cold5/FF/257语义gate仍false，N1科学实效/新颖性未立。11-01额度使只读审批未完成，11-02用户继续后已正常收尾；无后台/安装/队列，文档代码同步服务器、原始仅服务器、GitHub未配置。H3停止保持。本条取代旧待办。

2026-11-01 最新：[有限UTF8域与无schema工厂检查](runs/20261101-utf8-domain-factory.md)/[readiness](UTF8_DOMAIN_FACTORY_READINESS_20261101.json)优先。登记e3eecf0b…/合同a2e8333f…先核source/input/runtime后单次执行：128ASCII+固定¢é€中😀共133普通标量、EOS133/vocab134，非全部Unicode/真实BPE。新有限UTF8域的适配/无schema构造预检通过：133普通字符逐项/整串往返、8正例、7负例、EOS元数据及425调用独立验收均通过；X编译器构造完成，LL仅Tokenizer构造，schema/LLMatcher仍留后续。45原文本全可表达而语义执行0，不救旧257byte/FF或cold5 gate。导入从父spawn2.978171168秒、适配共用5秒内0.013625908秒、launcher3.383386563秒，非性能比较；worker/独立validator0，CUDA false，最终guard拒绝全0/query1次103903bytes，退出live_ready=false/backend_factory_ready及request admission仍false。LL没有对称unbound compiler接口，不补已完成标记；EOS实际matcher终止未验。输入按序号快照防basename覆盖。原始35文件657348bytes/manifest71ded6bf…、来源9文件71226bytes/c130edab…全回读，runtime101+dill2及source/input不变，4PID全无。新增1CPUrun，145runs3038主，新索引cc7cfee8…/closure5e46673a…；schema/matcher/mask/语义/模型全0，无安装服务队列。下一条新登记原8schema45标签全样本正确性，保留原输入顺序/gold/序列化，单独说明5秒请求与检查预算及LL deferred work，按134词项重算mask；不重做8/23/12、不性能/取消小试。代码文档同步服务器、原始仅服务器、GitHub未配置；N1未定题、旧SIGSEGV未知/H3停止保持。本条取代旧待办。

2026-11-01 最新：[崩溃定位与完整启动](runs/20261101-startup-fault-probe.md)/[readiness](STARTUP_FAULT_READINESS_20261101.json)优先。固定官方CPython3.11.13源码与相关报告只支持假设；raw3超时保留/API3源码Git blob通过，旧显式环境相同、ambient未知。诊断v1因GDB空格转义/条件块封装错误，Torch未执行，2case到30秒清理；v2先stdlib启动检查通过，两Torch worker正常/CUDA false，无SIGSEGV，但原validator将query主体PID误当worker而1/failed。另登记离线v3仅重判原事件，同TID/外部owner与query身份分别核对通过，原失败不改、无native重跑。随后另登记0a2e1d1e…，关闭周期抓栈/保留fatal、完整Torch/XGrammar fresh启动从父spawn7.802948144秒达到library_import_ready（launcher8.450735秒），worker/独立validator0，CUDA false、最终guard拒绝全0、只读query1次103903bytes。旧SIGSEGV根因仍未知，不称已修复；新startup30 gate通过不救旧cold5或FF。工厂/语义/request admission false，退出live_ready=false，45标签/模型/词表factory/编译器/matcher/mask均0。3新CPUrun（原2failed+1complete，另离线analysis不计run），144runs3038主；6归档全文件回读、runtime101+dill2/source/input不变，23自有PID全无，新索引35780f6e…/closure83ba166e…。下一条冻结共同合法UTF8域/special/EOS与同进程factory正确性协议，不直接跑45或性能/取消；不重复8/23/12和非复现崩溃追查。原始只服务器、代码文档同步、GitHub未配置，无后台/安装/服务/队列。N1未定题，H3停止/泛KV暂停保持。本条取代旧待办。

2026-11-01 最新：[分阶段合同验收与fresh启动](runs/20261101-phase-contract.md)/[readiness](PHASE_CONTRACT_READINESS_20261101.json)完成。控制器/8用例/独立validator/orchestrator已实现，软件登记79b46dd5…一次执行8/8通过，独立重算9账本；45逻辑秒fixture非实测性能。绑定证明后另登记ffd6cfb2…，从父spawn计30秒/launcher45秒的import-only单次启动在Torch导入中SIGSEGV/-11，launcher1.382369秒、非watchdog；X未开始、import/factory/request均未ready，CUDA后验与最终guard计数未知，不能补零。唯一1秒栈只到pathlib._format_parsed_parts即截断，根因未定，未观察到denial事件；只读query一次成功103903bytes。launcher/validator0仅工件一致，启动gate false；旧cold5/FF/语义gate仍false，schema/vocab/compiler/matcher/mask/45标签/模型全0。24文件104331bytes与27文件231545bytes两manifest全回读，runtime101+dill2及source/input不变，7自有PID全无。新增2CPUrun（1启动失败），累计141runs3038主，索引97ac2a66…、closureb746a031…；无重试/安装/服务/队列。下一条先只读审查crash与faulthandler/audit及运行输入，另冻有限定位方案；不以工程失败判N1科学成败，不重做8/23/12项。文档/代码同步服务器、原始仅服务器、GitHub未配置。N1未定题与H3停止保持，本条取代旧待办。

2026-11-01 最新：[启动/请求范围审阅](STARTUP_REQUEST_SCOPE_REVIEW_20261101.md)/[readiness](STARTUP_REQUEST_SCOPE_READINESS_20261101.json)完成，新契约f4e7e758…执行false/runner未实现。旧账本独立复算Torch3.081376/线程.009988，X开始时原5秒只剩1.908293秒；无schema编译样本，冷启动/FF gate仍false。实际源码路由InputProcessor.params.verify→SamplingParams._validate_structured_outputs→backend validator，还存在首次lazy backend构建；新账本必须计验证、队列、factory、编译和first-mask。拟新范围startup-import-only30秒/parent-spawn起、launcher总45秒，未来request5秒端到端（不同于旧publiccall5），不重新解释旧结果。imports_ready不等factory/domain_ready、不能跨PID复用；45标签关闭。下一条实现/登记8项标准库状态时钟合同验收，通过后另登记单fresh启动；不重做23guard或原12observer（除非其模块改动），无native队列。源12快照/AST28/旧账本，18文件272016bytes/manifest8ba1b4a0…全回读，runtime/旧source/input/results/索引e189878f…不变。0新run/import/model，仍139runs3038主，旧4PID均无。N1未定题，文档同步服务器、原始仅服务器、GitHub未配置，无后台任务。本条取代旧待办。

2026-11-01 最新：[导入边界验收](runs/20261101-import-boundary.md)/[readiness](IMPORT_BOUNDARY_READINESS_20261101.json)完成。精确pin/devnull与固定ldconfig-p有界捕获：v1软件20/独立验收通过，native发现dill builtin/_pyio wb模式；读源码后独立v2仅加固定字符sink精确WRONLY|CREATE|TRUNC、3回归，23软件通过，旧v1保存。真实v2即时拒绝0、只读查询1次103903bytes、Torch3.081376秒/线程.009988/3.091707秒进XGrammar；总5.000741秒被原watchdog kill/-9，4栈末份在Transformers/importlib.metadata扫描。无加时/重置/词表改变，不称导入或语义通过；CUDA后验未做。4run分别新登记，各source/input/runtime先核后单次执行；2软件通过+2真实导入未通过，所有launcher/validator0仅证据完整。16自有PID全退出，归档全回读；新增4CPUrun，139runs3038主，新索引e189878f…，旧工件/库不改。0schema/matcher/mask/45标签/模型/安装/服务。下一条只离线核冷启动vs每请求预算，必要时另冻新范围初始化/请求契约；不提高旧5秒或热身救gate、不据启动判N1科学结论。旧FF gatefalse/12observer通过/H3停止保持。代码文档同步服务器、原始仅服务器、GitHub未配置、无队列。本条取代旧待办。

2026-11-01 最新：[最小诊断](runs/20261101-backend-diagnostic.md)及[readiness](BACKEND_DIAGNOSTIC_READINESS_20261101.json)完成。登记8b33bb50…/源输入/运行101先核后单次执行；LL520调用实测返回bytes、唯一不等id255 FF为空，全0..255串255bytes/首差255、special255/256，两固定编码probe原映射还原通过，源码预测确认但原全byte gate false。X只有torch_import_begin，本次栈/异常定位Torch→cuda.pathfinder→ctypes.find_library(dl)→拟Popen(ldconfig -p)准备open(os.devnull,O_RDWR)被我们过宽文件guard拒绝；file_denied1，其余0、ldconfig未执行。X约1.195930秒异常/exit1非timeout，没进入Xgrammar；不能倒推旧5秒超时全部成因，也未做CUDA后验。diagnostic complete/独立验证通过不等X导入通过，语义45/schema/matcher/mask全0。launcher2222361内3.941186秒exit0、verifier2222367 exit0、workers2222364/65均核退出；23文件629418bytes/manifestbcebf220…/verification8aa60ac4…全回读。新增1CPU诊断run，135runs3038主，新索引b0c41c24…，旧失败/source/runtime不改，无自动重试/加时/改词表。下一条精确修/devnull和只读库发现准入、先软件验收再新CPU登记，不对任意子进程放行；共同UTF8域将来须新契约，不救回旧gate。N1未定题、12observer/旧队列保持，文档同步服务器、原始仅服务器、GitHub未配置，无后台任务。本条取代旧待办。

2026-11-01 最新：[源码审查](LEGACY_BACKEND_SOURCE_AUDIT_20261101.md)/[readiness](LEGACY_BACKEND_SOURCE_READINESS_20261101.json)完成。官方llguidance v1.7.6固定0384f3f6…，安装wrapper/stub Git blob匹配：TokTrie以FF为special标记、decode剥标记，原id255单FF预测为空／全串255bytes；是适配契约冲突的源码解释，不是新测得decode差值，也未独立证明.so构建commit。内置byte为262词/EOS261不能直接替代257/EOS256。X旧import还含Torch、两线程设置及高层依赖，具体超时点未知，audit开销也在内，不归因JIT/FFI。新禁用诊断草案b6802e24…保留原257输入/组合总5s，拟只取字节差值、special分类、阶段checkpoint与栈；runner未实现/未登记/无队列，下一条实施后才另冻执行，不删FF/跳检查/改schema/加时救回。官方6源+14安装/项目快照，共25文件334142bytes/manifest4b90869d…全回读；runtime101/旧失败/source-input/索引06fccdfb…不变，旧3PID现场均无。0新run/native/model/GPU，仍134runs3038主；原12observer通过、旧语义gate false及N1未定题保持。代码文档同步服务器，原始仅服务器，GitHub未配置，无后台任务。本条取代旧待办。

2026-11-01 最新：[真实后端CPU前置失败](runs/20261101-legacy-backend-cpu.md)与[readiness](LEGACY_BACKEND_CPU_READINESS_20261101.json)为准。登记e10a5b2f…固定101运行文件/5.so及源输入hash后单次执行；XGrammar2212826组合import>5s被watchdog kill/-9，未定位具体子模块；llguidance2212901导入0.062260秒完成，但info.decode_bytes(0..255)往返不符，未保存实际差值、原因未知。两GIL控制各0/22心跳通过；真实语法/45标签未跑，schema/matcher/mask全0，90计划格unavailable绝非90测得错误。独立validator0只证失败工件一致，overall failed/launcher2212823 exit1/5.512406秒；三已记录PID现场均不存在，validator已wait退出但未归档PID。LL四guard0，X最终guard被强杀缺失不补零；未加载模型/模型tokenizer，CUDA隐藏，X未到CUDA后验检查。21文件297931bytes/manifest6f64c194…/verification2252c734…回读，101运行pin事后不变；1新失败CPUrun，累计134runs3038主，新索引06fccdfb…，旧索引不改。无自动重试/调时限/换字节/安装。下一条只读审固定byte/special-token约定和import分段，再另冻有界诊断，不直接运行45题或判N1 go/no-go。代码配置文档同步服务器，原始仅服务器，GitHub未配置，无后台任务；原observer12通过/H3停止及旧队列保持。本条取代旧待办。

2026-11-01 最新：[标准库观测器CPU验收](runs/20261101-structured-observer-cpu.md)12/12与独立validator均通过，[readiness](STRUCTURED_OBSERVER_READINESS_20261101.json)为准。新登记21c4c487…与源/输入hash先冻结、单次运行；137事件102外部样本核PID/starttime/native TID/同pool同slot，caller超时/取消false后的未结束、进程异常无end删失、cleanup失败、共享B继续均保留正确状态。9case取消后CPU采样不足记null，不称0成本或真后端性能。launcher1805119内1.176444秒／validator1805146内0.007076秒exit0，12case和3task共17自有PID全核退出；guard禁止项全0、仅3允许task spawn。37文件143828bytes／manifestfeb73647…与独立fd03c950…全回读，归档cap先核再complete。新增1CPUrun、0真实编译/mask/模型/分词/权重/GPU/网络/安装，累计133runs3038主，新索引03ed7996…；旧132索引不改。下一条实现并另登记现有后端CPU导入/GIL观察/257合成词表/8schema45标签正确性，不重跑12fixture，也不以旧版证明强对照不足；实际后端adapter未实现、无队列。N1实效/新颖性未立，H3停止/泛KV暂停及旧队列保持。代码配置文档同步服务器、原始仅服务器、GitHub未配置、无后台任务。本条取代旧待办。

2026-10-31 最新：[CPU可行性协议／静态预检](STRUCTURED_RESOURCE_CPU_PROTOCOL_20261031.md)、[配置](../configs/structured-resource-cpu-feasibility-v1.json)及[readiness](STRUCTURED_RESOURCE_CPU_READINESS_20261031.json)完成。已有独立环境vLLM0.32.0／XGrammar0.2.8／llguidance1.7.6；XGrammar无dynamic参数，vLLM要求llguidance<1.8，不能原环境升级后仍称兼容。最新llguidance取消为Rust原生能力，已审Python stub及两binding未见取消入口；当前PATH无Rust工具链、session cgroup不可写，强对照未就绪。8公共schema／45标签按预定原顺序冻结，selection41a774b5…；配置351fb27b…，执行false／runner未实现。下一条实现、冻结、登记12项标准库观测器工程验收，明确返回≠停止≠原槽恢复；随后才另登记旧版API语义正确性，不从旧版结果判新缺口。静态脚本e2428a6f…实际0.034389秒exit0／PID1796798核退出，未import作者后端；20环境来源和13官方blob／选样独立复核，最终41文件607993bytes／manifest18cfd4bb…全回读。0真实编译／mask／取消／模型／分词／权重／GPU查询／安装／新实验，132runs3038主和索引b0c4d8fd…不变。N1未定题／新颖性未立，H3停止／泛KV暂停与旧停止队列保持。代码文档同步服务器，原始仅服务器，GitHub未配置，无后台任务。本条取代下方待办。

2026-10-31 最新：[新问题筛查](NEW_PROBLEM_TRIAGE_20261031.md)及[readiness](NEW_PROBLEM_READINESS_20261031.json)完成。H3 停止、泛 KV 约束保持暂停作为主线，保留原型／结果。四条新候选中仅 N1“结构化输出取消后的资源回收与租户间干扰”保留为有界实证候选，尚未定题／证实效果／建立新颖性；N2 分离式取消有故障注入近邻且成本较高，N3 热更新缓存一致性和 N4 batch 确定性的宽泛主张被直接覆盖。固定 vLLM/XGrammar 源审与 PR #45172/#52119 当前补丁、llguidance 原生预算／协作式取消、GRID 构建预算说明共同表明不能只以“加超时／进程池”立题。下一条冻结纯 CPU 可行性协议与兼容性预检，先区分返回／终止／槽位恢复，再决定有界配对小试；当前 runner/协议未完成，无新实验队列。只读来源归档 31 文件 564110 bytes，manifest 1fc87993…全回读，24 成功来源 hash 核对、9 raw 网络失败保留；未执行作者代码。0 新实验／模型输出／分词／权重读取／GPU 查询／安装／服务；累计仍 132 runs／3038 主，现有索引 b0c4d8fd…现场核对不变，六个旧 H3 PID 均不存在，无后台任务。文档同步服务器，原始仅服务器，GitHub 未配置未 push。本条取代下方旧待办，不恢复旧 QA/Mistral 或其他停止队列。

2026-10-31最新：[H3固定12组筛查完成并停止当前候选](H3_SCREEN_DECISION_20261031.md)，[主记录](runs/20261031-decoder-h3-screen.md)/[readiness](DECODER_H3_SCREEN_READINESS_20261031.json)优先。先[共同batch工程](runs/20261031-common-batch-engineering.md)通过：2组Full+8候选18状态正反序36logits逐字节及KL精确重复、hook/nohook cache相同、实际mask/1008efficient/gather独立验证；这是新固定缓存流程，不救回原跨路径0.25/0.001 gate。随后原12DEV Full12/12通过≥10，8候选96+Full12共108向量全部完成。真实KV目标排序反转11/12已观察，但global/Top128/Top256/legal四目标所选均12/12保留Full正确决策，legal相对每基线0win/0loss/12tie，development_go=false。固定候选保真Snap10/recency8/六随机6/9/9/9/6/7，不能说裁剪完全无损；generic KL/TopK已选到正确缓存，无合法目标增益。独立stdlib复算384 KL/全部选择转移/Full支持/maps/masks/trace/4权重7metadata通过。当前H3停止，不扩题/seed/预算/模型/更难prompt救回，不以只排序不同承诺新颖性或毕业。原launcher real_KV_signal_observed=false为初始化未更新，semantic_closure明确真实反转true/实用go false，原manifest不改。工程worker1431879/validator1433053/launcher1431874与screen1450114/1451208/1450109全部exit0并核退出；GPU1收尾18MiB/0%。两阶段新增2GPUrun/144logits/172forward/13900输入token/28编码/0完整答案，累计132run3038主，新索引b0c4d8fd…；screen原164文件68140344bytes，加closure/derived166文件68159219bytes，原manifest256b9fd6…/derivedfbfa685d…全回读。系统原型/原48技术报告及旧QA/Mistral false/停止队列保持，代码配置文档同步服务器、原始仅服务器、GitHub未配置、当前无运行任务。本条取代旧H3筛查待办；新问题须独立需求和强近邻不足，不能改名重启。

2026-10-31最新：[真实SDPA现场观测v4完成](runs/20261031-sdpa-observation.md)，[readiness](SDPA_OBSERVATION_READINESS_20261031.json)/[修订](SDPA_OBSERVATION_REVISIONS_20261031.md)优先。先CPU24通过及归档修复，再4个独立GPU观测run：v1取证晚于断言，v2确认CPU/GPU同名注记双计56/28，v3修device-type后遇Kineto单次导出限制，v4只导出一次完成；模型/输入/原observer wrapper/阈值/后端均不改，所有失败保留。实际2工程组/108forward/1082输入token/14末分布/10profile/2856SDPA：168显式bool mask+28 KV头走efficient，2688 None mask+4 KV头/GQA走Flash，全部is_causal=false。独立原event父链/Chrome marker/336 BF16tensor与gather/reference/trace/4权重7metadata复核通过；4对Full/recency plain-observed logits逐字节相同，函数恢复/ref不变。确认了真实分支差别，但未证明全部数值漂移成因；原数值gate仍false、mask值未采、H3与12DEV未跑。worker1422342内134.329954秒/verifier1423750内29.054636秒/launcher1422337总167.305701秒exit0，81文件256317526bytes/manifest13d41950…完整回读，cap检查先于complete。3旧失败各3forward/1向量；本轮总1CPU+4GPU（3failed），17工程向量/117forward/2345输入/16编码/0完整答案，累计130run3038主，新索引52861c0f…；旧索引/QA/Mistral false保持。全部自有PID退出，GPU1收尾18MiB/0%，无队列。下一条冻结共同batch-suffix运行契约及目标重复性标准，区别原整段/分段数值等价；不以换阈值或工程例最大误差救回旧gate，新Snap工程/Full12支持仍待验。代码配置文档同步服务器、原始仅服务器、GitHub未配置。本条取代下方GPU未实现历史待办。

2026-10-31最新：[SDPA透明记录器CPU验收完成](runs/20261031-sdpa-observer-cpu.md)，[readiness](SDPA_OBSERVER_READINESS_20261031.json)与[禁用现场草案](SDPA_OBSERVATION_DRAFT_20261031.md)优先。参数原样转交/返回identity/原异常/嵌套与恢复冲突/marker-sink故障/日志cap及合成profiler父链等18用例，另6归档fault共24通过；独立重判合同及19fixture归档文件hash/count/bytes。新checked_archive先核递归文件和最终summary/manifest开销才写status，当前41文件100853bytes/cap64和4MiB，通过而不追改原44>40失败。worker1412961内0.061212秒/verifier1412963内0.017568秒/launcher1412958总0.284792秒exit0均核退出，guard全0。0真实Torch/SDPA/profiler/模型/GPU/编码/权重/网络/安装；新增1CPUrun，累计126run3038主，索引3da7a45b…，manifest478fb700…全回读。CPU只证stub合同，不证明真实CUDA数值/性能透明。原工程failed/H3未测/12DEV停止保持。新2工程组观测草案execution=false/runner=false，7路径×2含同路径Full/recency plain-observed精确对照，拟108forward/1082输入token/14归档分布/2856 SDPA事件；下条实现并冻结GPU观察worker/validator/运行时证据后才新登记，不自动GPU或切后端阈值。代码配置文档同步服务器、原始仅服务器、GitHub未配置、无自有运行任务。本条取代下方待办。

2026-10-31最新：[数值/源码离线审阅](DECODER_NUMERICS_REVIEW_20261031.md)、[记录](runs/20261031-decoder-numerics-audit.md)、[readiness](DECODER_NUMERICS_READINESS_20261031.json)完成。精确安装HF源码+shape stub重放56调用（非真实Torch）：51None-mask/nativeGQA、5显式mask/repeat头，逐1287query按源码/记录参数可见集合相同；不是实际mask或CUDA kernel观测，尚未证明全部误差成因。4路径对/8概率scope独立复算，合法KL另Decimal60核验；Full/random概率差极小，recency global TV0.01673/allowed0.00042567，argmax稳定不等KL排序可信。原工程failed、0.25/0.001门槛/H3未测/12DEV停止均保持。worker1405845内1.692507秒/verifier1405867内1.498305秒exit0，但parent1405785在summary先写complete后发现44>40文件cap而exit1，整体记failed_archive_file_cap_analysis_verified；closure如实记录，不调上限/删工件/重跑。追加closure/derived后46文件4846935bytes，manifest a0dec76b…/derived75f431ab…回读。两官方PyTorch v2.5.1原文抓取成功；0新模型/GPU/编码/权重/安装，新增1CPU失败run，累计125run3038主，新索引43ddc7a0…，原工件不变。下一条先实现透明SDPA参数/实际后端记录器与CPU传参/恢复检查，修未来归档上限状态记录，再另冻2工程组有界现场观测；当前无第三GPU/12DEV启动或新后端阈值选择。代码配置文档同步服务器、原始仅服务器、GitHub未配置、三自有PID退出，无运行任务。本条取代下方待办。

2026-10-31最新：[同前缀KV工程两次失败](runs/20261031-decoder-kv-engineering.md)，[readiness](DECODER_KV_ENGINEERING_READINESS_20261031.json)优先。v1先hash权重后Torch临时目录run外写探测被拒，0forward/编码；v2仅固定run内TMPDIR/tempfile.tempdir，不放宽guard/输入/阈值。实际28Full/GQA4/BF16/SDPA与4权重7metadata、4工程编码核对；第一组56forward/1287输入token/7末token分布，缓存/gather/reference逐值与168tensor独立字节复算通过。但whole-full/split/recency/random路径max logits差0.5625/0.4375/0.5/0.5均>0.25，recency全KL0.002501>0.001，虽argmax集合相同仍工程false；完整validator未启动，事后独立标准库重算证实失败，不改分或阈值。第二工程组及全部12DEV模型调用0，H3未测试，不启动第三GPU。worker1398285/1399346与launcher1398280/1399341全退出，v1内21.708571/外22.371169秒、v2内23.757826/外24.478085秒exit1，GPU1收尾18MiB/0%。v1 fileguard1/v2违规全0，各拒绝1次精确IPv6 probe另计。归档v1 23文件360431bytes/v2 42文件47463000bytes，原manifest不改，后验derived与源码全保留。新增2失败run/4编码/0完整答案，累计124run3038主，新索引4dc414b3…；7工程logits不计新主答，旧48/索引/QA/Mistral false保持。下一条只离线审查已有数值误差质量、mask/位置与BF16可比标准，不能按结果放宽门槛救回或判方向no-go。代码配置文档同步服务器、原始仅服务器、GitHub未配置、当前无运行任务。本条取代下方GPU待办。

2026-10-31最新：[真实tokenizer与新输入CPU预检完成](runs/20261031-decoder-native-preflight.md)，[readiness](DECODER_NATIVE_READINESS_20261031.json)与[协议](DECODER_NATIVE_CPU_PROTOCOL_20261031.md)优先。固定Qwen metadata/tokenizers0.22.1/Jinja3.1.4及新2工程+12开发组先冻结，登记d7d2edcd…只运行一次。34编码/6NFC与UTF-8 probes完成；独立标准库从151643 base词项穷举49语法边、排除22 added普通路径/399无词项model行，复核原生byte/14边界/事实gold及位置×标签平衡。首分支实际仅32–35即A/B/C/D；14组prefix373/suffix24、0跨界、半预算186/锚点68/free118全可行。布局57344bytes/槽仍是预测，native后端编码不等真实HF运行/gather通过。worker1392627内0.915734秒/verifier1392628内3.262950秒/launcher1392624总4.396328秒exit0均核退出，guard全0。归档28文件342048bytes/manifest798a6809…全回读，新增1CPUrun/34编码/0回答权重GPU安装，累计122run3038主，新索引34c0b953…，旧索引及原48评分不改。受控合成诊断不称独立自然基准；Full能力/H3失配/新颖性未知。下一条实现并冻结新2工程组同前缀真实KV协议/模型runtime权重pin、Full与gather/位置/数值标准、seed/资源上限，通过再固定12组Full支持与有界logit筛查；本次GPU入口未实现/未启用，不从旧草案自动执行。旧QA/Mistral false及旧停止队列保持，代码配置文档同步服务器、原始仅服务器、GitHub未配置、无自有运行任务。本条取代下方待办。

2026-10-31最新：[局部解码目标CPU验收完成](runs/20261031-decoder-objective-cpu.md)，[readiness](DECODER_OBJECTIVE_CPU_READINESS_20261031.json)记录实际结果。用户通知SSH恢复后现场核远端AGENTS、原索引与run未存在，CAS同步17文件及4Python编译通过；按原847651a5…登记只执行一次，源码/协议未改。18/18用例、23坏输入拒绝通过，独立80位Decimal重算7候选分布及全部目标/40条有限字节语法边/路径与8候选索引预算。worker1389088内0.133624秒、verifier1389089内0.702380秒、launcher1389085总0.985419秒均exit0并核退出，guard全0。归档21文件239223bytes，manifest f9a304f6…全部回读。新增1CPUrun/0模型答案/编码/权重/GPU/安装，累计121run3038主，新索引3c7cdede…；旧f3e6a039…索引和原48结果不改。有限byte语法不等native tokenizer，索引预算不等实际GPU gather，H3真实失配/新颖性仍未建立。下一条先冻结真实tokenizer-byte适配/schema与12新开发组CPU来源/native边界预算协议，再另冻同前缀query+wrapper重算和真实KV工程/GPU上限；不重跑已过CPU、不直接执行禁用108向量草案。旧QA/Mistral false、旧停止队列保持。前轮5次握手失败是0run历史，本轮阻塞已解除。代码配置文档同步服务器，原始仅服务器，GitHub未配置，当前无自有运行任务。本条取代下方历史断点。

2026-10-31当前断点：[CPU正确性实现](DECODER_OBJECTIVE_CPU_PROTOCOL_20261031.md)、[readiness](DECODER_OBJECTIVE_CPU_READINESS_20261031.json)和[记录](runs/20261031-decoder-objective-cpu.md)已写本地。四脚本覆盖有限byte语法/稳定support KL/Full-Top128/256/等预算索引、18组用例与23坏输入、独立80位Decimal/穷举图核验及同步watchdog。**尚未运行或验收通过，新增文件未同步服务器。** 5次SSH均认证前断开，verbose确认TCP建立后KEX前关闭，不诊断密钥或具体原因；未修改VPN/服务/host key。先恢复连接、读远端AGENTS/当前索引/旧进程、CAS同步冻结文件和核源输入SHA/run未存在，再执行唯一新CPU登记847651a5…；失败保留、修订另起v2。原GPU草案禁用不改，真实tokenizer适配/物理KV gather/H3失配/新颖性均未验证；CPU通过后再冻结新12开发组同前缀诊断，不自动GPU。0新run/模型答案/分词/权重/GPU/安装；120run3038主和旧索引是上轮记录，本轮未现场复核。原48不改分，旧QA/Mistral false与旧停止队列保持。本轮没有启动远端任务，远端当前进程不可查询；GitHub未配置。此条取代下方待办及“已同步”旧表述。

2026-10-31当前进展：[研究问题重定](RESEARCH_QUESTION_REDEFINITION_20261031.md)与[有界草案](DECODER_OBJECTIVE_SCREEN_DRAFT_20261031.md)完成。H1格式修复与H2泛parser-aware KV不作主创新；仅保留H3待筛查假设：同一生成前缀下，全词表/通用Top-K KL是否会给等预算真实KV候选排出与局部合法token目标不同、且损伤合法语义决策的顺序。三token构造反例及标准KL分解已独立复核，但不是真实KV证据；尚无新颖性或可发表/毕业结论。下一步先实现CPU有限语法/稳定KL/候选掩码正确性入口并独立核验，再另冻12个新开发组的query-known同前缀logit诊断。108向量草案未实现/未执行，不是108独立回答；禁止复用Full suffix KV、原48调参或把局部mask当全序列条件分布。含Top128/256及直接masked-KL组合对照，无信号即停，不扩seed/预算救回。原文与算术证据仅服务器literature/20261031-decoder-aware-candidate-v1，10文件2266407bytes，manifest ea36b38a02db149812649eace16c321e92786a7da17fb4eaa00f086e717f2963。0新实验/forward/回答/分词/权重/GPU；累计120run3038主及f3e6a039…索引、原GPU194与分类20工件不改。旧QA/Mistral false及旧16/保护/3/4/BoolQ停止保持。代码配置文档同步服务器，GitHub未配置，当前无运行任务。本条取代历史待办，既有实测与查重结论保持；H3仅列研究假设，不计已建立科学贡献。

2026-10-31最新（审阅始于10-30）：[近邻贡献审查](CONTRIBUTION_AUDIT_20261030.md)、[范围决策](CONTRIBUTION_SCOPE_DECISION_20261030.md)、[审阅记录](reviews/20261030-contribution-audit.md)与[readiness](CONTRIBUTION_AUDIT_READINESS_20261030.json)完成。重读六项主近邻及TensorRT官方工程指南，固定5仓库/33文件+6论文官方页面，39源/24作者Python仅AST；4HEAD仍是此前固定版本，LYR沿作者直链commit。Pitfalls已有指令退化；KVDiagnosis已有全量Full配对/四转移/N/A/版本发布检查及真实适配来源审计；kvpress有context/question拆分和cache不变测试；质量/性能联合基准及LYR先导已覆盖资源核算、格式/内容/截断混淆。Risk-Controlled代码未定位保持未知，不据缺页断言无代码；LYR未同行评审、KVD未来会议页眉不当录用证据。本轮判断：保留已验原型和48组受限结果，尚未建立独立新方法/新基准贡献；通用账本/双指标/配对/预算检查不能当首创，六章可组织不等论文贡献闭合。系统/实证硕士候选保留，具体贡献仍待重定，不能代判毕业认可。暂不追加同类退化GPU实验，下一步先明确可证伪的问题缺口和最接近实现的实证增益，不据错题调prompt/样本/预算。来源原文源码只服务器literature/20261030-closest-work-audit-v1，51文件2924027bytes，Git blob/SHA核验通过，作者代码/测试未执行；部分web缓存失败改读同官方API，39源请求+9元数据成功，无模型/数据集下载。只读文献审阅不新增实验，累计120run3038主/f3e6a039…索引与原GPU/分类工件不变；0新模型回答/分词/权重/GPU/依赖/服务，旧自有PID退出。旧QA/Mistral false、旧16/保护/3/4/BoolQ停止保持。代码配置文档同步服务器，GitHub未配置，当前无运行任务。本条取代下方历史待办，原实测结果不撤销。

2026-10-30最新：[既有138答离线错误分型完成](runs/20261030-squad48-error-taxonomy.md)，[分析](SQUAD48_ERROR_ANALYSIS_20261030.md)、[readiness](SQUAD48_ERROR_READINESS_20261030.json)与[论文章节证据映射](THESIS_EVIDENCE_MAP_20261030.md)优先。分类在看到原GPU汇总后制定，明确探索性，原评分/主要差值/CI与194个GPU工件不变。全部144格/48组保留：Full31联合成功+3仅EM+13仅格式+1两项失败；Snap3仅EM+39两项失败+3截断+3预算不足；随机9仅EM+5仅格式+27两项失败+3任务N/A+1截断+3预算不足。原Full联合成功31组中，Snap3仅格式损坏/25两项失败/1截断/2预算不足；随机7仅格式损坏/2仅EM不匹配/17两项失败/2任务N/A/1截断/2预算不足。随机9个task-only里2个在Full已是task-only，不能全称新增格式损坏。已完成格式失败Full4plain/Snap42plain/random32plain+3JSON字符串+2结构解析+1object额外key或空answer+1缺string answer。9软件边界与独立138文本重评分/144分类/全48流转/31切片/26个确定性说明示例核验通过；示例完整文本只服务器，不当新样本/调参材料，EM/F1不充人工语义标注。worker1063574内0.065141秒/verifier1063575内0.038397秒/launcher1063571总0.281935秒exit0均退出，guard全0；本轮1CPUrun/0新回答/编码/权重/GPU/网络/依赖变化。归档20文件242447bytes，累计120run3038主，索引f3e6a039…，重分析不重复计答案。六章草案已按需求—实现—验收—48组实证—边界组织；下一步核对最接近工作原文/公开实现与具体系统差异，未建立差异前不称创新或毕业保证，不追加GPU/错题调参。旧QA/Mistral false及旧16/保护/3/4/BoolQ停止保持，原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。本条取代下方历史待办。

2026-10-30最新：[原48组GPU实证完成](runs/20261030-squad48-gpu-study.md)，[readiness](SQUAD48_GPU_READINESS_20261030.json)与[研究边界](SQUAD48_EVIDENCE_CONCLUSION_20261030.md)优先。新独立study角色/输出adapter先过16软件用例，现场14工程答验证Full三路径/压缩双路径；旧HF角色限制不改、旧证据不注入。Qwen实际28Full/GQA4/BF16/SDPA/57344bytes槽，4权重6metadata加载前及独立复核SHA，50完整输入重编码相同。Full48任务34/48、格式44/48、joint31/48、错误/截断0，预定支持线通过，随后90可行压缩回答完成。Snap任务3/42、格式0/42、joint0/48、3截断；随机任务9/41、格式5/44、joint0/48、1截断和3候选N/A；两条件各3预算不足，全部48组/144格保留。两个all48 joint差均-31/48=-64.58pp，10000配对共享组抽样/seed20261030/type7逐项95%CI[-77.08,-50.00]pp；相同区间源于相同Full与全0 joint向量，不是独立复现。任务和格式同时受损，不称安全特异或新发现。独立138文本、4622trace步、94文件10528layer-head map、全部分母/主要统计及source/weights核验通过；原manifest不改、后验194文件5567444bytes。worker1052050内126.485009秒/verifier1053387内18.168072秒/launcher1052047总145.824922秒均exit0并退出；GPU1收尾15MiB/0%，Torch dtype弃用警告保留。新增1GPUrun/138主14工程/4664tokens，累计119run3038主，新索引d1c405bd…。单模型/任务/半预算/seed的独立于DEV描述性证据已补齐，原跨任务/第二模型确认、保护收益和纯推理成本未完成；精确文章去重不证明语义/预训练独立。下一步离线分型已有138答并组织系统/实证章节，不再重复证明一般裁剪有害、不据错误调prompt/换题/增预算，也不自动扩保护/3/4/BoolQ/Mistral/旧16。旧QA/Mistral false保持，无下载/依赖变化/服务。原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。本条取代下方历史待办。

2026-10-30最新：[组级统计CPU软件验收完成](runs/20261030-group-statistics-acceptance.md)，[readiness](GROUP_STATISTICS_READINESS_20261030.json)记录实际执行。新增独立统计模块、runner与stdlib validator，固定18/18用例通过，13次非法输入按合同拒绝；独立重算11份完整合成报告的全部计数/配对转移/差值、10000共享组抽样流和Fraction有理type7区间。G02只有4次精确枚举，区间[-0.925,0.925]是软件用例。原提案b1e9d042…false历史不追改，实际登记a50b8d68…与源码/协议先冻结同步。原48组/144格全部not_run、真实指标null、模型效应/CI为0份；Full48预算可行、Snap/随机各45可行+3不足，全部组和6阻塞格保留。仅规范化统计schema与pending计划adapter已验，旧scalar core/runtime/角色/证据规则未改，真实GPU输出adapter和新角色接入尚未实现。4输入257350bytes/原manifest13项及后验18文件216564bytes完整回读；guard全0。worker1036427内0.659025秒、verifier1036428内0.416647秒、launcher1036424共1.183390秒exit0均退出。本轮1CPUrun、0回答/编码/权重/GPU/网络/依赖变化；累计118run2900主，索引1e9b651d…。下一步实施并冻结GPU阶段输入/role/runtime与同cohort工程证据和输出adapter正确性检查，原2工程题最多14工程答；Full48先行，输出前草案任务≥24/格式≥36/错误0/截断≤4，失败停压缩，通过才最多90个可行压缩主答，总主答≤138、报告144格不减。以上GPU为待实施阶段，本轮未启动；旧QA/Mistral false、保护/3/4/BoolQ/旧16停止保持。代码配置文档同步服务器，原始仅服务器，GitHub未配置，当前无运行任务。本条取代下方历史待办。

2026-10-30最新：[原48题Qwen原生前端/半预算CPU检查完成](runs/20261030-squad48-native-preflight.md)，[readiness](SQUAD48_NATIVE_READINESS_20261030.json)记录实际结果。原48题ID/顺序/prompt/gold/文章组保持；48个完整native输入各两次编码，共96编码，独立stdlib复核通过。Full48格数学可行，半预算Snap与随机各45格可行、3格不可行：3道原题的半预算容不下固定sink4/recent64的68锚点槽，全部48组/144计划格仍保留，不换题/补齐/减少锚点。共138格数学可行、6格预算不足；所有执行状态仍not_run、指标null、当前cohort工程及Full支持未验证，不把CPU false解释为测得Full失败。prefix94–472/header56/query suffix10–34，57344 bytes/槽只是布局预测，header未作为保护收费。本轮1CPU run/96编码/0模型答案/权重/GPU/外联网请求，精确urllib3回环能力bind已拒绝且单列1次；内2.926653秒/外3.121825秒exit0，PID1026473/1026470均退出。原提案15dfe0e7…false历史不追改，实际snapshot与全部输入/22文件1926244bytes/manifest及独立回读保留。累计117run2900主，新索引724817ec…；旧QA/Mistral支持false及旧停止队列保持。下一步[组级统计CPU验收提案](../configs/group-statistics-acceptance-v1.json)b1e9d042…已禁用冻结，18软件用例/10000共享组配对bootstrap/seed20261030/type7逐项95%区间，模块与runner尚未实现/执行；不能对当前planned清单计算实际效应。统计验收后另冻GPU角色/runtime/工程证据和Full支持协议，才可能生成最多138个主要回答；原144天花板与14工程资源预留不是自动启动许可。当前无运行任务，原始结果仅服务器，代码配置文档同步，GitHub未配置。本条取代下方历史段落的待办。

2026-10-30最新：[原48组来源/分组冻结完成](runs/20261030-squad48-source-freeze.md)，[readiness](SQUAD48_SOURCE_FREEZE_READINESS_20261030.json)记录CPU实际结果。用户“开始下一步”后实现runner73609092…/独立BFS validator4aa481d1…，按原b1b97571…提案固定执行；原false历史字段不追改。整个train442组件/87599问题与全部87599gold span重新核验，原64题/角色/坐标/prompt/gold逐字段重放相同，原48预留ID/顺序/48group不变。64个完整文章标题/段落集合彼此及整个历史dev48文章精确交集零；这限精确SQuAD组件，不是语义/预训练独立保证，不把BoolQ跨任务false改true。输出selected48 SHA993ae6a4…与144唯一planned/not_run格f256ae91…，预算未检查/工程未注册/指标null，不能反推模型/Full支持。16输入35489314bytes/raw35142551bytes、原manifest/来源hash及独立图BFS/选择/144绑定回读通过，禁止import/模型文件/socket/子进程guard事件全0。单次PID1022354内1.769917秒/launcher1022351共1.869884秒exit0均退出，0编码/权重/GPU/网络/模型答案/依赖变动；新增1CPUrun，累计116run2900主，索引5134913f…。下一步[Qwen48原生前端CPU提案](../configs/squad48-native-preflight-v1.json)15dfe0e7…已禁用冻结，runner未实现/未执行：仅原48题96编码核完整native ids/header/query边界与半预算anchors并补144计划预算状态，0权重/GPU，不调试改写预留题，不按长度/预算删题或填充。其后统计模块验收和独立GPU协议仍需完成，当前不推理144格。旧QA/Mistral支持false、旧16封存/保护3/4不启用，原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。

2026-10-30最新：[最小独立证据与范围收敛完成](MINIMUM_EVIDENCE_SCOPE_20261030.md)，[readiness](MINIMUM_EVIDENCE_READINESS_20261030.json)和[禁用CPU来源冻结提案](../configs/squad48-scope-freeze-v1.json)给出下一交付。保留系统/实证方向但不称论文完成：主验证缩为固定Qwen+SQuAD-only原48预留文章组，Full/半预算适配Snap/原seed随机共144主回答天花板；最多14工程资源预留不是已启动重跑，input/runtime/证据转移须新协议。Mistral格式8<9停止原适配、BoolQ403与HF缺title暂停、3/4及完整保护不入最小主矩阵；保护收益只留开发案例/预算边界，不能由无保护验证推出普遍保护效果。不改prompt/gold/样本/seed/旧falsegate，不找第三模型救回。新SQuAD-only scope明确不等原跨任务划分完成，保持原4工程12DEV48预留/64不同组，旧16封存不入推理。下一步实现CPU90秒/外120秒、0tokenizer/权重/GPU/网络的来源/组件重建与原48身份冻结，生成全部144planned格；精确train/path/parent split schema/摘要已定位，runner未实现/未执行，proposal execution=false。通过后另做native前端/预算、统计模块与GPU协议，不能现在直接推理。Full48支持24任务/36格式/错误0/截断≤4及组bootstrap均为输出前草案，未运行、非功效/风险认证。只读核最新run/manifest/角色metadata与原PID退出，本轮0新run/答案/编码/GPU/权重/依赖变化，115run2900主及d2673f94…索引保持。原始仅服务器，新增文档/禁用提案同步，GitHub未配置，当前无运行任务。

2026-10-30最新：[Mistral当前QA Full-only完成](runs/20261030-mistral-squad-full.md)，[readiness](MISTRAL_SQUAD_FULL_READINESS_20261030.json)记录工程true/支持false。用户“继续”后冻结协议217d3204…及新Full入口cdec42ae…，原前两工程+固定12DEV，3权重SHA/10metadata加载前核验。实际32Full/GQA8/head128/BF16/SDPA、131072bytes-slot/cache clone/reference/三路径一致检查通过，6工程+12主239token全部返回、零错误/截断。DEV任务7/12达≥6，格式8/12未达≥9，joint6/12；Full_support=false不是run执行失败。本适配压缩/保护/封存队列停止，不放宽格式、不重生成错误/更改prompt样本模型或旧关卡。4格式失败均JSON字符串而非answer对象，其中1条任务正确，是Full基线格式支持不足，不归因裁剪。独立18文本评分、193trace步、12报告分母/阈值、3权重/10metadata与输入指纹复核通过。PID999238内86.049380秒/launcher999235共86.742325秒exit0均退出，GPU1收尾15MiB/0%，无下载/依赖/环境变化。新增1GPU run/12主6工程，累计115run2900主，索引d2673f94…。第二模型当前Full工程已验但任务适配不支持，压缩/3/4/保护及独立contexts未验；同12DEV不当新增独立样本。下一步离线收敛两模型支持/覆盖边界与最小独立证据范围，不继续模型/提示搜索或自动扩Qwen预算/封存。旧QA false、BoolQ403/HF缺title、旧16/新48封存保持。原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。

2026-10-30最新：[两模型CPU原生前端/预算预检完成](runs/20261030-independent-frontends-preflight.md)，[readiness](INDEPENDENT_FRONTENDS_READINESS_20261030.json)记录v1失败/v2完成。固定4工程+12DEV×2模型，v2共48native变体/96编码/32model-case/128预算评估；原Qwen14输入/边界精确重现，工程三query prefix相同、完整system覆盖与16metadata/模板独立核验。Qwen prefix146–312/header56，Mistral154–359/header59；含anchors保护并集120/123槽。完整保护DEV数学可行：半预算Qwen2/12、Mistral3/12；3/4均12/12。4工程池保护可行半预算1/4、2/4，3/4均3/4；原两GPU工程题仍含1个3/4不可行，不能据DEV可行设保护engineering pass或自动换题。当前只是CPU预测，Mistral真实KV/Full任务支持与compact、现后端3/4支持均未验。v1完整编码后最终guard将已阻止的urllib3 IPv6回环能力bind计为网络尝试而failed，0外联/权重/模型；import-only诊断保留，v2仍阻止精确probe但单列记录并收紧HFsymlink白名单。两版三份native/rows/budgets SHA相同，独立边界/union/floor/bytes/覆盖回读过；无新数据/样本/预算改动。v1 PID987652/987649内3.973699秒exit1，v2 PID990438/990435内3.736171秒exit0，四PID退出。新增2CPU run含1failed，共192编码技术重复、0主/工程模型回答/权重/GPU/网络/依赖变化，累计114run2888主，新索引491e4cbb…。下一步另冻并实现Mistral Full-only≤6工程+12DEV协议（原前两工程+固定12DEV），先真实32Full/GQA8/BF16/SDPA/cache与三路径，再Full支持门槛；0compact/保护/封存自动队列。旧QA false、封存16/48、BoolQ403及HF缺title保持。原false提案历史不改，不重跑CPU或旧Qwen12DEV；代码配置文档同步服务器，原始仅服务器，GitHub未配置，当前无运行任务。

2026-10-30最新：[独立实证推进方案](INDEPENDENT_EVIDENCE_PLAN_20261030.md)、[系统验收矩阵](SYSTEM_ACCEPTANCE_MATRIX_20261030.json)与[readiness](INDEPENDENT_EVIDENCE_READINESS_20261030.json)完成。本轮只做来源/元数据/现有证据核对和协议设计，0新run/模型回答/分词/权重读取/GPU查询，112run2888主及743ee544…索引保持，旧4PID退出。已验系统链与独立科学确认分开：当前12DEV停止重复；下一实际任务为两模型CPU原生前端/预算预检，固定原4工程+12DEV、0封存，最多96编码/128预算评估，1/2与3/4沿原独立实证草案，仅算完整system+anchors覆盖。新CPU提案83136793…保持execution=false/runner=false，runner/独立检查尚未实现，不能由待办加载模型。服务器Qwen6/Mistral10元数据摘要匹配，Mistral3权重文件大小匹配但本轮未读正文；旧Mistral权限Full通过不等新QA/cached compaction通过。Mistral应从完整native INST折叠system/user渲染切prefix，不能把system-only BOS当缓存，不套Qwen标记；当前HF后端不支持Mistral/3/4，须新scope工程验证。CPU之后另冻Mistral Full-only≤6工程+12DEV协议，0保护/封存自动队列。BoolQ有google/boolq固定HF分发线索但无title，正文/标签/原字节等价未验，不能静默替换原按文章去重方案；旧两403保留，继续暂停正文准备。独立48组、第二模型压缩、生产式成本/统计覆盖仍待补，不宣称新算法/总体安全/毕业保证。源码未改，新增配置文档同步服务器，原始仅服务器，GitHub未配置，当前无运行任务。

2026-10-30最新：[HF系统DEV端到端验收完成](runs/20261030-hf-DEV-acceptance.md)，[readiness](HF_DEV_ACCEPTANCE_READINESS_20261030.json)记录v1失败/v2修正。新增检查点恢复模块8软件用例通过，固定同生成器scope e2ee00ab…的原14工程观测由原/后验manifest、source/input/request/raw/accepted和evidence重算验证后恢复，当前新增工程0；控制/评分协议另锁digest b1304610…。v1加载后直接比较model_config误报id2label整数键与JSON字符串键差异，0生成/0token后停，原失败全保留；CPU完整配置JSON往返全同，v2只修序列化比较，不改生成器/题目/预算/解码/门槛，输出前另冻修订。v2真实36主回答1115token，20预算不足+4保护证据不足由dispatcher拦截，60规范记录完整归档，0保护/封存。独立重判36文本、1115位置trace步、2688层-head map/1344Snap排名、48输入与全部60格分母/F1/转移/损坏上下界/joint一致。Full任务9/12、格式11/12、joint8/12；Snap任务0/11/格式0/11、1截断，random任务3/11/格式2/12、1任务N/A；保护0输出不算0%/100%。v1 PID948163/948160、v2 PID950105/950102全退出，内20.910878/43.615357秒，exit1/0，GPU1收尾15MiB/0%，无依赖/环境变化。新增2run含1failed/36主0工程，累计112run2888主，索引743ee544…。系统集成链已打通，仍是同12DEV回归、0新独立组/非科学确认；停止重复本12DEV或14工程，下一步离线整理系统验收矩阵与独立实证协议，明确任务/来源覆盖、Full支持、预算与第二模型缺口，不能直接扩封存/预算。BoolQ403、跨任务/第二模型/性能仍待补，旧QA gate=false/历史输出不改。原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。

2026-10-30最新：[新版HF后端GPU工程验收完成](runs/20261030-hf-backend-engineering.md)，[readiness](HF_BACKEND_ENGINEERING_READINESS_20261030.json)记录实际范围。新工程协议d871f191…冻结后单次运行，同两工程题Full三路径6答、无保护Snap/random两路径8答，14工程回答605token/0DEV/封存。新旧14输出逐token/终止/trace一致，实际28Full/GQA4/BF16/SDPA、gather/预算/reference检查通过；3条件工程verified，2保护条件4工程格仍半预算不可行/unverified。Snap同一题两路径均达128上限，1case数值一致不等任务完成。独立回读25输入/14绑定、563位置trace步、448层-head map、224Snap排名、旧score/map及4权重全部匹配。GPU注册scope e2ee00ab…绑定旧dry scope+新协议/runner，工程证据由本次真实观测形成，不注入旧证据。60DEV仅决策：36可准入、20预算不足、4保护证据不足；未生成DEV，不据准入当执行。PID939938内32.612922秒/launcher939935共33.294891秒exit0，均退出，GPU1收尾15MiB/0%；console弃用提示保留，依赖/权重/环境不变。新增1GPU run/14工程0主，累计110run2852主，索引a7a3838d…。下一步另冻至多36已准入DEV格的系统端到端验收协议，接实际输出/双指标/统一归档；0保护/封存，20不可行+4未验保留。该验收仍用已有12DEV，不增加独立科学样本，不重复14工程或泛裁剪有害验证。BoolQ403、跨任务/第二模型/性能仍待解决；旧QA gate=false及旧输出不改。原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。

2026-10-30最新：[HF编排壳与延迟加载适配器](HF_ORCHESTRATION_20261030.md)已接线，[CPU验收](runs/20261030-hf-orchestration-dry.md)22项检查通过，[readiness](HF_ORCHESTRATION_READINESS_20261030.json)记录实际范围。工程bootstrap与DEV分阶段；绑定实际input ids、prefix、system token、prompt、context_group_id及源码/runtime指纹。旧5条件工程证据不能跨新版本复用：新版60DEV格中20预算不足、40等待新版工程证据；工程只规划14调用，4保护工程格预算不足，未伪造通过。原条件准入的36eligible属于旧scope，历史40输出/4保护诊断、旧分数及QA gate均不改。主dry plan的backend工厂/执行均0；另2项负向测试调用空适配器入口并在加载前拒绝。15固定输入511251bytes/64源JSONL行，14题绑定与预算/证据独立回读一致。PID934338/0.175006秒exit0，1新CPU run、0模型输出/权重加载/GPU查询/网络/重依赖导入/环境变化；累计109run2852主，索引2eafbb3f…。HF代码已接线但新版GPU行为尚未验证。下一步另冻仅14工程回答的GPU协议，0DEV/封存，核逐token/trace、实际runtime与加载/失败边界；不重复本次CPU验收，不沿旧证据直接跑36DEV。BoolQ403、跨任务/第二模型与性能实测仍待解决。原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。

2026-10-30[条件级准入/工程证据接口](CONDITION_ADMISSION_20261030.md)实现并通过[CPU验收](runs/20261030-condition-admission.md)，[readiness](CONDITION_ADMISSION_READINESS_20261030.json)记录实际状态。新增reliability_execution_contract.py/acceptance/runner：预算、同条件runtime+selector/protection/retention指纹、两工程题逐路径token/termination/trace证据、准入、实际执行、任务指标分别保存；blocked时软件callback不调用。20软件检查全部过，10固定输入527183bytes/78源JSONL行，60DEV格独立回读一致：36未来可准入、20预算不足、4预算可行但保护工程未验而阻止。历史40实际输出（含4条保护诊断）及20不可行/旧分数/gate不变；保护工程均预算不可行，状态unverified，不能借用无保护的pass。Snap一工程题两路径截断但数值一致，标verified_at_decode_cap/output_complete=false，不等任务支持。PID924636/.052993秒exit0，新增1CPU run/0模型输出，累计108run2852主，索引3972e01f…；无GPU/网络/模型/tokenizer/环境操作。真实HF driver尚未接线，旧producer不改；下一条接新的HF编排壳并只dry-run，分清bootstrap工程stage与DEV证据要求，绑定输入/runtime指纹，不重跑已有DEV或封存。BoolQ403来源与跨任务/第二模型仍待解决。代码配置文档同步服务器，原始仅服务器，GitHub未配置。

2026-10-30已从设计推进到[新来源真实DEV](runs/20261030-independent-development.md)，[readiness](INDEPENDENT_DEVELOPMENT_READINESS_20261030.json)记录实际证据。BoolQ官方GCS元数据/publicHEAD分别HTTP403，两个失败run保留，无镜像/认证更改；新bool评分器20软件用例全过，但BoolQ正文未取。SQuADtrain固定blob/30288272bytes与SHA35276639…通过，442文章/87599题答案slice全exact；新64文章组按hash原问题选题不取最长，历史dev48标题/规范段落零重叠，4工程/12DEV/48封存暂定。输出前单独修订e19913a6…允许先SQuAD开发，不称跨任务最终划分/确认，不改原prep false或旧gate。新CPU14题36编码边界通过，system56+锚点并集120槽，半预算73–156；2工程及10DEV完整保护不可行，不加预算/文本。Full12为EM9/格式11/joint8/0截断、工程6答三路径一致，支持过；无保护Snap/random各12答，严格EM0/11、3/11，格式0/11、2/12（Snap1截断，random1任务N/A）；两保护各仅2题可行，EM0/2、1/2、格式均2/2，各10不可行保留，不能报总体100%格式。保护工程4格均不可行，不能把总engineering_gate=true解释为保护路径已验；其2题输出仅诊断。统一核心60计划cell报告/3584map/14score hash/40主KV trace与范围独立核验过。新增7run含2failed、40主/14工程/1767tokens，累计107run2852主，索引a1e120d9…；七PID退出，GPU1 18MiB/0%，无依赖变更/其他任务操作。下一条优先接每条件预算准入和工程证据范围到统一执行接口；BoolQ来源暂停，封存/第二模型/新预算不自动跑。原始仅服务器，代码配置文档同步，GitHub未配置。

2026-10-30用户要求开始系统设计与实证，[第一版架构](RELIABILITY_SYSTEM_DESIGN_20261030.md)、[独立实证草案](RELIABILITY_EMPIRICAL_PLAN_20261030.md)及[系统readiness](RELIABILITY_SYSTEM_READINESS_20261030.json)完成，已实际实现/验收公共核心。新增reliability_system_core/adapters/acceptance与server runner，标准库schema/模型布局描述符KV计算/精确比例收费保护/布尔与连续指标/配置身份配对/未知成本。服务器[归档验收v1](runs/20261030-reliability-system-archive.md) PID907824、0.073420秒exit0，8输入840461bytes/324源JSONL行、290规范化唯一cell，TREC开发32/已用留出10/QA开发16分别严格计数/转移/分母/F1一致，16软件用例通过，外层Counter/差值/覆盖独立重算通过。1随机QA截断与未知成本仍保留，旧gate false和旧封存16不改；回放不算新科学确认。新增1CPU run/0模型回答，100run2812主，索引cef16cc4…；自有PID退出，无GPU/模型/tokenizer/新数据正文/依赖操作。下一条先固定SQuADtrain与BoolQ原始对象、BoolQ评分/去重分组的CPU提案再实现执行；新GPU小试拟Qwen+BoolQ12DEV/60主+22工程上限，但输入/scorer未就绪，当前无GPU配置或运行任务。第二模型Mistral仅config候选，通用生成器/实际成本测量/独立实证待做。源码配置文档同步服务器，原始仅服务器，GitHub未配置。

2026-10-30用户要求自动衔接至方向判断，已完成[四阶段筛查](runs/20261030-answer-format-direction.md)与[可行性结论](ANSWER_FORMAT_FEASIBILITY_20261030.md)。结论：保留系统/实证型硕士路线，但当前16题阅读+JSON不独立成题，不称新算法/安全创新；本轮自动GPU任务结束。CPU原生边界18题/44编码、完整system56token+锚点并集120槽、半预算142–426全部通过；Full工程6答逐token一致，DEV16为EM12/格式16/0截断，支持门槛过。压缩工程16答native/custom一致，64主输出全返回；适配Snap/随机/Snap保护/随机保护的EM=4/8/5/5、格式=3/8/15/16。随机1条截断/任务N/A触发输出前固定的全条件完整配对关卡false，不扩封存确认、不改门槛/提示/长度/样本/预算追正结果。保护收益/代价真实可测：Snap修格式12但任务1损坏2改善；随机修7可比格式失败但任务3损坏0改善，另1截断项单列。独立8064映射不变量/适配Snap排名、18prefix score hash、80主KV字节/位置trace、逐例分母与损坏覆盖范围复核通过；新任务报告adapter6软件fixture过，限此固定任务/模型。新增4run、80主/22工程（1687tokens），累计99run2812主，索引11d49a0b…；旧工件/冻结提案不改，原始仅服务器。自有4PID全退出，GPU1收尾18MiB/0%，无后台服务/依赖变更、其他任务未操作。下一步是开题与系统验收设计；独立验证/第二模型须新协议，当前无GPU队列。源码配置文档同步服务器，GitHub未配置。

2026-10-30[阅读+JSON任务CPU预检完成](runs/20261030-answer-format-task-preflight.md)，[当前readiness](ANSWER_FORMAT_TASK_READINESS_20261030.json)优先于下方“未实现/未取数据”。新标准库模块answer_format_task.py SHA58783b7b…、runner e5e3d1a2…；v1单次61.288秒/exit0，24评分+6数据fixture全过，4固定源共4871766bytes匹配blob/SHA。原数据SHA95aa6a52…、48文章/2067段/10570唯一题/34726 gold slice全部exact；文章组件48，固定选34组工程2/开发16/封存16，跨组id/规范段落零交集，独立两两图+BFS/逐源选择与prompt回读一致。所选原段落164–629词（非token/长上下文），不修标签/重采样/填充，留出无模型访问。原manifest0d97b98f…/selected_cases ccf4866f…/后验manifest b4d9306c…全保留；旧9输入/13源码/两个报告manifest不变。新增1CPU run，95run2732主，索引777d54ad…；0新主/工程模型回答、模型/tokenizer/GPU查询/依赖变更，PID823622退出，无新后台任务。token边界/保护span/半KV预算/Full支持均未测，任务report F1/N/A/损坏上下界adapter未实现；旧proposal/contract/source作为冻结输入不改false字段，勿重跑。下一条先冻并做只用工程/开发18题的CPU native模板/tokenizer/config可行性检查，再另冻最多22回答Full-only提案，当前不加载权重、不启动留出/裁剪/第二模型或旧队列。代码配置文档同步服务器，原始仅服务器，GitHub未配置。

2026-10-30[新任务契约](ANSWER_FORMAT_TASK_CONTRACT_20261030.md)离线完成：选SQuAD v1.1有答案阅读+固定JSON输出，原文/问题/全部gold不改；任务EM/F1与格式分开，gold-blind提取允许裸正确答案/额外key正确，重复键/结构无法解析等记任务N/A并保留覆盖与Full正确损坏上下界。作者数据commit/blob/4854279bytes元数据固定，正文/实际数量/长度/SHA256未核；评分参考固定BiDAF作者仓库副本，不宣称与未取到的原CodaLab逐字节一致，JS语义不混用。按文章/相同段落连通分量取工程2+开发16+封存留出16，每组最长原段落1题，算法/seed先固定，非官方test或预训练独立保证。24评分+6数据用例已声明但未执行；[CPU提案](../configs/answer-format-task-preflight-proposal-v1.json)SHA a106a9ea…，execution=false/runner=false，未来服务器标准库120秒/4请求/8MiB下载/32MiB归档，0生成/GPU。Full-only另冻最多22回答及最低支持量，当前未启用；长度/预算/三路径/Full失败均停，不填充、换题或重提示。本轮0新run/主/工程回答，94run2732主及旧索引保持，无模型/数据正文下载或环境改动；自有旧PID已退出，无新后台任务，未查GPU/他人任务。下一条实现并审CPU准备/独立判分与用例，再单次服务器预检；不直接跑Full/裁剪、不重跑报告。文档配置同步服务器，GitHub未配置。

2026-10-30[CPU报告实现/回归完成](runs/20261030-reliability-report-replay.md)，首个系统模块已可用但限历史TREC标量结果。新增reliability_report.py、reliability_report_fixtures.py、replay_reliability_report.py，纯标准库；只读9输入294450bytes/242 JSONL行，产生210唯一规范化记录，开发32/留出10分别两口径按逐行重算与冻结预期/旧summary一致，12fixture通过。v1原计数/原12fixture过，后审查发现legacy错误路径分母误用eligible pairs；post_review保留，v2区分历史Full正确分母与strict可比较分母，并加强同一fixture2，两run源码/manifest均不覆盖。当前hash report b4a1afe3…/fixture ee08aab6…/runner e748a497…；v2 manifest e395fb3f…/summary e61bfa30…；新索引54b237c2…，新增2CPU run，累计94run2732主/0新模型与工程回答。重复键/错配/等预算失败硬拒绝，错误/截断/not_run/N/A、不可评估Full正确数、未知peak/时延全部显式保留；historical loss0但unassessed1不当安全成功。没有重新解码/判分/map验证或独立科学确认，旧9输入/10脚本及旧模型工件不变。自有PID786388/787643退出，无GPU/他人进程查询/依赖变动。下一条仅离线写新任务数据/评分契约、上下文族划分与Full支持/失败条件，再另冻新实验；报告已验证不重跑，不据旧提案false恢复TREC/A/guard/controller/取消队列。源码/配置/文档同步服务器，GitHub未配置。

2026-10-30[系统需求/验收](RELIABILITY_SYSTEM_REQUIREMENTS_20261030.md)与[10文件盘点](RELIABILITY_IMPLEMENTATION_INVENTORY_20261030.json)完成，用户系统/实证路线已转为具体设计。现有HF/Qwen2.5-7B KV选择/gather/逻辑位置/双判分/旧独立审计可作基础；旧28层/4KV-head/57344bytes、半预算、32/10题及19正确分母硬编码不改为通用事实。旧summarize字典未拒绝重复，旧计时/峰值字段不足，报告应显式unknown，不从prefix字节推整进程节省。统一记录键、cohort/基准来源、错误/截断/N/A、strict完整配对分母与不可评估Full正确数、同预算保护、旧/新口径分开等10项验收已定义。首个改动新增标准库只读adapter/报告，不导入torch/HF/旧runner/scorer或加载.pt，不改旧结果。configs/reliability-report-replay-proposal-v1.json冻结9输入SHA、开发32与已用留出10预期及12软件fixture，execution=false/runner=false，未实现/执行；未来仅服务器CPU60秒/32MiB/300JSONL行/32文件，0生成/GPU查询。下一条实现并验证该报告层，再考虑新任务/可配置runner；独立数据/第二模型仍未就绪。当前0新实验run/回答，92run2732主沿用；旧3run数据/manifest只读核验、3旧自有PID不存在，无GPU/他人任务探测或环境改变。代码未修改，文档/禁用配置同步服务器，GitHub未配置。

2026-10-30[选题收敛稿完成](THESIS_CONVERGENCE_20261030.md)。用户本轮明确导师/学院接受有明确问题的系统或实证研究，已记录根USER_CONTEXT；不以新算法/漏洞/发表为唯一目标，但不等于题名与贡献已认可。优先讨论“面向输出约束可靠性的Transformer KV缓存压缩评测系统设计与实证分析”，问题为相同实际KV字节与可比生成条件下，约束/任务双判分、同预算指令保护的收益与损失，以及独立上下文/第二纯Attention模型的可复现边界。现有TREC平台可复用但单模型/小样本/示例共享，不能当独立确认；共享控制器零效应/成本核验只作附属工程经验，不并成另一论文主线。重核TREC留出summary及两个controller摘要/manifest与旧账本，92run2732主不变；三篇近邻本轮仅复核官方摘要/版本，不宣称新颖性通过。当前0新实验/主/工程回答，无GPU/他人进程探测/新环境任务。下一条仅离线盘点既有脚本/结果字段、写需求与验收表，用开发32/留出10分别作回归材料；不重跑旧TREC、不恢复A/guard或控制器/取消攻击矩阵。新任务确认与第二模型均须另冻协议，目前无新GPU队列。文档及用户约束同步服务器，未向GitHub写入。

2026-10-30[第2线索取消记账审查](CANCELLATION_ACCOUNTING_GATE_20261030.md)完成，无新执行队列。固定vLLM0.32.0/5df63a7，HTTP Chat→AsyncLLM→ABORT→默认step/scheduler→metrics/auth/admission共13份安装源码blob匹配官方；已发射执行仍受边界约束，不能把用户放弃等同transport断开。abort移除状态但不调用正常finished统计有静态依据，然而公开issue55634/PR55940（查询时open未合并、head805d8734…）已直接覆盖，不能当新发现。Retire2610.01160v1已有过时计算/输出权威/KV交接；Sorami README已有transport close/no-read等对照，明确非GPU时间/账单；GRIEF已有取消时序测试。LiteLLM固定main blob可见预留/部分usage结算/取消槽清理，但非完整网关审计或部署保证。当前没有已核具体配额契约/实际违反/超出强简单记账方案的机制证据；泛取消成本/补统计论文主张no-go，真实配额绕过未建立，不跑服务/模型/压测。0新实验run/主/工程回答，92run2732主沿历史；无GPU查询/环境改动，仅读旧自有PID退出状态，其他任务未操作。下一条先一页选题收敛，按毕业不强制发表约束区分可用工程、已覆盖主张与新增证据条件，不自动查第3项/恢复A或guard。报告/来源/交接同步服务器，本轮未向GitHub写入。

2026-10-30[默认图尺寸profile验证](runs/20261030-controller-profile-validation.md)完成：55.562秒、2工程回答/64tokens，均与旧baseline prompt/token ids一致。加载前实际候选[1,2,4,5,8,10,16]；内存预估只捕获[8,10]/45样本，最终捕获[1,2,4,5,8,10]/65样本，共110；10原生blob与64 FullAttentionSpec/Triton/MRV2控制器门槛通过。每次shape/context/顺序/原始计时均归档，独立median曲线和整表exact重建；最终N1有5直接样本，N2有25图样本，verify1–5不再全同价。draft差0.431ms落在重复测量波动范围，不宣称稳定性能差异；内存预估1254.67ms离群样本及真实生成3个JIT警告原样保留，dummy表不代表完整真实周期。新表代入旧397向量/36unique作N1 CPU反事实，common/A/B仍全选4、无决策差；未记录本轮真实预算，不能将反事实当观察。**当前固定配置筛查结束，暂不继续共享控制器候选GPU实验；未见损害/立题证据。** 下一条只读审既有第2线索“取消后的资源记账”的明确契约/实际配额实现与近邻，无新模型或服务队列。新增1run、0主/2工程，累计92run2732主；原13工件及后验manifest核验，PID757235/757539和自有组全部退出，GPU1 18MiB/0%、GPU0他人PID729245未动。源码/文档同步服务器，GitHub未配置。以下“profile runner未实现/未执行”均为历史，不重跑。

2026-10-30[成本表/正常负载审查](CONTROLLER_COST_PROFILE_AUDIT_20261030.md)完成：10份安装源码blob匹配固定0.32.0；工程capture[5,10]使verify1–5同桶，全部原profile点均N2，draft N1是补表而非独立测量；8192请求context在图点被maxlen512截至507。原始timing未保存，无法复核离散度/JIT污染/准确性；native计时完成链在dummy路径，不等同真实完整周期。默认balanced图覆盖仅源码预测，未构建引擎验证。公开target熵/聚合draft置信度不等于本对模型逐位置qmax，尚无正常敏感域证据。旧六探针零效应保留但不外推默认引擎；不宣布攻击/创新，也不扩历史/模型/并发矩阵。新增1标准库CPU审计run、0主/工程回答，累计91run2732主；16工件校验通过、PID745113退出，无GPU/他人进程查询。已准备禁用两回答/600秒原始profile工程提案，runner未实现、未执行；下一条先实现透明观测及默认图推导/计时重建门槛，再仅测量验证。原始只服务器，代码/配置/文档同步，GitHub未配置。

2026-10-30[自然历史小试完成](runs/20261030-controller-natural-history.md)：v1因我方trace解析误把无draft的prefill当缺失阶段，2warm+2工程后停、0主，失败保留；仅修解析的新v2先通过hook off/on token/学习状态exact，再完成30主（24历史+6探针）+2warm+2工程/34总1856tokens。A/B各6历史都自然refit1，slope0.5→0.11341/0.40663，探针置信度最大差0.533/0.046；**六探针均7个decode步预算4、admitted28/accepted25、32token输出exact，未见预算/可用性损害。** 397预算/428验证step独立成本/删失counts/phase复算通过。N1成本1..5位置同价，解释预算饱和；全部397真实向量仅36unique，离线复制N2三套系数仍全选8（不是batch GPU证据），uniform反例未出现在自然记录，不当正结果救回。本配置筛查结束，不自动扩prompt/seed/历史/budget/model/batch；下一条若继续仅离线审profile/热身可信度及公开正常负载可达的敏感域，再判断是否值得新方案。新增2run累计90run2732主；本轮另4warm/4工程，所有自有进程组退出，GPU1 18MiB/0%、他人任务未动。原始服务器，源码配置文档同步，GitHub未配置；旧“待运行自然历史”均为历史。

2026-10-30[真实worker工程v5通过](runs/20261030-controller-worker-v5.md)：固定Triton/MRV2/Full decode图，64 cache spec全FullAttentionSpec，15次命名扩展RPC；17张量/CPU-GPU缓冲与pending统计/相位/cost/空闲槽位原址快照恢复，跨refit同探针token及学习终点exact，冻结训练更新通过。**phase95人为工程fixture，不是自然历史损害；不是KV/model/RNG完整服务checkpoint。** 本轮v3可选FlashInfer采样器Ninja空格路径失败、v4引擎已成但callable RPC序列化拒绝均保留；官方native sampler开关+命名worker extension修正后v5成功，无模型/精度/attention backend搜索。新增3run、0主/6工程答案（192tokens），累计88run2702；独立复核/哈希通过，自有6PID退出，GPU1 18MiB/0%，他人任务未动。下一条实现禁用自然历史提案的逐步预算观测与两输出透明性门槛，过关再固定30主+2warm+2工程/34总/900秒小筛查；未执行、不强设95、不把参数/预算变化当延迟攻击。代码/配置/文档同步服务器，GitHub未配置；以下“worker未跑通”为历史。

2026-10-30[配对模型准备与worker初始化](runs/20261030-controller-worker.md)：固定0.6B draft的8文件约1.519GB全部官方摘要核验，四份tokenizer文件与8B逐字节/完整token-id映射/模板一致。真实worker工程v1因我方eager关闭必需CUDA Graph在加载前失败；修正新v2配置预验证通过、MRV2实际加载双权重16.38GiB统计后，自动FlashAttention2不支持最大query5的可变长度图，初始化失败。**两次0主/工程答案、0 RPC，完整worker恢复/历史影响均未测。** 新增3run累计85run2702，原始/失败snapshot全服务器，PID690691/693490/695039/695383退出，GPU1收尾18MiB/0%，他人任务未动。仅读源码/CPU能力核查后准备禁用v3提案显式TRITON_ATTN（ALWAYS/设备CPU长度不一致支持声明），未再加载模型；不切换FlashInfer救回（SM89受限）。下一条只新v3目录按原6答案/600秒门槛验证固定Triton真实worker；不是攻击负结果/创新结论，旧gate保持。代码配置文档同步服务器，GitHub未配置；旧“draft未下载”均为历史。

2026-10-30[独立环境与原生估计器检查](runs/20261030-controller-runtime.md)完成：新.venv-controller-history安装197包SHA锁，Python3.11.13/Torch2.13.0+cu130/Transformers5.19.0/vLLM0.32.0，pip check/导入通过；6项安装源码blob与固定审计一致。GPU1原生predict/accumulate/refit共127step，CPU参考最大绝对差9.156e-5（预定atol/rtol1e-4）；估计器完整状态跨refit原址重放exact，θ-only负对照与空重估通过。**仅估计器，不是完整worker/异步双缓冲恢复，也没有模型或攻击结果。** 新增2run、0主/工程答案，累计82run2702；自有PID374652/683603均退出，GPU1收尾18MiB/0%，GPU0他人进程未操作。旧venv/驱动保持、draft未下载、无模型加载/服务。下一条准备固定draft及tokenizer，再冻真实worker有界工程协议，完整恢复通过后才配对小试；A/旧guard gate保持。原始只服务器，锁文件/代码/文档同步服务器，GitHub未配置；以下旧“未建环境”为历史。

2026-10-30[CPU预检v2通过](runs/20261030-controller-history-cpu-v2.md)：相同54fixture全部通过，4503次合成step/单例最多255；dense最大差3.89e-16，unobserved6.66e-16，12个参考完整恢复exact、12/12识别仅恢复θ负对照，槽位/batch换序最大差4.27e-14。仅自建CPU参考，不证明真实GPU/完整vLLM恢复或用户损害；v1失败不覆盖。累计80run2702主要输出，0新主/工程答案。追加只读环境核查：旧venv无vLLM，Torch2.5.1/Transformers4.57不满足所审0.32要求；已固定已有Qwen3-8B与候选0.6B revision/配置，draft未下载/tokenizer未核验。可信worker collective_rpc接口已定位但checkpoint未实现；[运行准备清单](CONTROLLER_RUNTIME_PREPARATION_20261030.json)仍禁用、runtime未就绪。下一条先解析并锁定依赖/二进制兼容、准备独立环境与真实状态接口，再另冻有界GPU协议；本轮未安装/建环境/下载权重/加载模型。两卡查询时有其他用户进程，仅读未操作；自有CPU PID358928退出。源码/提案/9项工件哈希与v1保留核验通过，原始只服务器，文档同步，GitHub未配置。

2026-10-30[CPU预检v1失败与诊断](runs/20261030-controller-history-cpu.md)：54个预定fixture中32通过（dense16/mask15/unobserved1），第33项unobserved-01失败，余21未跑；0新主/工程生成答案，累计79run2702。失败是我方“共享斜率每例必须移动”断言过强：归档Decimal50位独立稠密复算得候选slope−0.04499955，源码负斜率防护会保留0.5；不是模型/安全假设失败。按fail-fast停止，未自动重跑。revision2修正已准备（SHA2e7e9c2c...），保留输入/seed/上限及指定movement案例，增加逐例dense oracle；新修正提案禁用，尚未执行，完整恢复/空轮次/边界族未验证。v1源码/输入/失败/诊断/7项哈希核验与PID退出证据全服务器，索引20261030-run-index-controller-history-cpu.json。实际系统Python3.10.12/标准库CPU，非初读venv3.11；无环境改变/模型/GPU使用或探测。下一条只核对修正后以新v2目录完成有界CPU预检，不进模型；旧A/guard gate保持，代码/配置/文档同步服务器，GitHub未配置。

2026-10-30用户选择先调查第一条，完成[共享控制器生命周期/近邻/对照设计](CONTROLLER_HISTORY_AUDIT_20261030.md)。固定vLLM0.32.0：共享系数与未重估统计跨请求保留，新请求仅重置置信度槽；每100次step调用重估、只观测接受位置/首个拒绝，参数与预算/真实代价间仍有未测环节。官方10-28 warmup/JIT修复已审相关patch，不能把首次编译当持续损害。TTA投毒已有顺序/恢复/非i.i.d.研究，APEX已有删失生存建模且部署参数固定；不宣布新漏洞或创新，也不判掉具体隔离问题。下一条仅实现禁用的controller-history-preflight-proposal-v1.json CPU公式/完整状态预检（64fixture/例256step/60秒，runner未实现），尚未执行，不进模型。0新CPU实验run/主/工程答案/环境操作，无GPU/进程探测，历史78run2702不重算；A/旧gate保持，其他方向未改，文档/来源/提案同步服务器，GitHub未配置。

2026-10-29用户问其他可调查方向，完成[新线索初筛](NEXT_RESEARCH_LEADS_20261029.md)：优先核查共享在线接受率估计器的跨用户历史影响，其次取消后的资源记账，权限撤销/派生KV失效仅低优先。固定源码已确认所审实例内共享slope/位置intercepts与跨请求refit，但没有实测操纵或正常用户损害；TTA投毒、取消漏洞及缓存失效已有近邻，三项都未通过创新门槛。与前轮已否决的泛预算算法区分，不恢复旧队列。无新实验/启用配置/进程/GPU探测，78run2702沿历史；仅文档同步，其他方向未改。后续若继续调查，优先第1项的共享状态生命周期及直接近邻，尚非模型执行队列。

2026-10-29[投机交叉问题门槛审查](SPECULATIVE_DESIGN_GATE_20261029.md)结束，当前不进入算法开发/模型实验。官方vLLM v0.32.0固定5df63a7203cdb9328d824a27b682e77c7b9928be，22文件只读索引/定向检查：已有接受率感知的跨请求自适应验证预算、成本profile及逐请求逐步统计；LAPS-SD已按长度+接受率/已获draft-verify服务调度，SPECTRE已有共享draft公平/回退。泛新算法主张no-go；跨用户尾延迟是否仍受损未测，不声称现有机制已保证租户隔离。基础观测静态可用，但逐请求完整回退/租户强基线、成本归因和固定Full Attention模型兼容均未完成，未建立超出现有直接适配的问题。本候选单次队列结束，无自动下一实验/新候选；A搁置、旧KV/guard停止保持，其他方向未改。0新主/工程输出、0新实验run/配置/环境变化，无GPU/进程探测；78run2702沿历史。报告/索引/状态同步服务器，GitHub未配置。

2026-10-29[选题收敛](RESEARCH_CONVERGENCE_20261029.md)：暂停当前KV裁剪安全新算法主线和同类曲线扩展，保留平台/负结果；A搁置，B/C/D/E现有宽泛主张不进开发。这不是否定整个领域，历史78run2702输出不能当独立论文主体。仅保留一个待证问题供下一次源码/文献门槛审查：连续批处理中，相同token配额下投机低接受率对其他用户的延迟干扰。Speedbumps未测该范围，但Mistletoe/ADSD已有接受率攻击、VTC已有自定义成本、FairInference已有逐token延迟公平、GRIEF已有跨请求干扰，尚未确认新颖性。未正式转向或修改其他方向；0新主/工程输出、0新run/配置/环境变化，无GPU/进程探测。下一条只审固定引擎接口、直接近邻及简单回退/成本适配边界，未通过不跑实验或复活旧gate。文档同步服务器，GitHub仍未配置。

2026-10-29候选E查重完成：[E版本修订与结论](E_NOVELTY_GATE_20261029.md)。补读CompressionAttack更新后的COMA v4（2026-06-19），已直接覆盖不可信输入操纵共享预算、可信规则/证据丢失，以及来源隔离压缩；此前只读v1低估重叠，本轮纠正。RobustKV正式版重要性操纵项为人为分配淘汰位置的近似评估，并非真实外部文本操纵，但这一缺口不抵消COMA直接近邻。E宽泛新方法主张no-go；物理KV机制差别仍未变成有证据的问题，不启动攻击/模型实验。A搁置、D降级/旧工程失败保持；当前无通过设计门槛的新选题或执行队列。0新主/工程输出、0新run，仅文献/作者README只读与文档同步，未探测GPU/进程。GitHub连接器读作者仓库不代表项目文档上传，项目GitHub仍未配置。

2026-10-29候选D差异审查完成：[D审查与强基线](D_NOVELTY_GATE_20261029.md)。MAGE已用安全shadow memory逐步审核待执行动作，TRACE聚合风险证据但Reader仍读原轨迹；LRE已有廉价query-blind原文保留，StepKV/CommitKV已有步骤/生命周期机制。D当前宽泛新方法主张no-go，降为待证备选；严格KV用途尚未否定，也未证明现有强基线不足。已明确持久/峰值KV、原文回读、更新/判定总读取与时延口径，当前不具备进入实验的设计条件。0新主/工程输出、0新run，无配置/工程重试；旧三路径失败和A搁置保持。下一条选题操作为补审E直接近邻，不自动启动任何矩阵；本次未探测GPU或模型进程。文档同步服务器，GitHub未配置。

2026-10-29同步核查：本方向README/AGENTS及docs下全部Markdown共43份，与服务器同名文件逐份SHA256一致，0缺失/差异。本地当前路径及服务器方向/上级路径均不是Git仓库，未配置可核验的GitHub远端；本会话未向GitHub提交或推送，不能声称GitHub已同步。本次仅文档核查/记录同步，无实验、依赖或进程操作；A搁置、D/E待查与旧工程失败决定保持。

2026-10-28用户明确“候选A先不做”：A搁置，不恢复原256输出或另换指标救回。当前转为其他候选的文献筛查，保留D（安全guard自身历史KV压缩）与E（不可信文本操纵真实KV裁剪评分）两条待查线索，见[替代候选](ALTERNATIVES_AFTER_A_20261028.md)。D优先只审实质差异，既有工程失败不变；E近邻重叠风险高。两者均未确认创新，不启动新实验/工程重试。本次仅网页/既有文档阅读和文档同步，0新模型/工程输出、无新run/依赖/权重/数据。未重新检查服务器GPU或旧进程，资源状态仍为上轮记录。

2026-10-28恢复后收尾：goal可继续后按原方案使用新目录v2/v3/v4；0主要答案、6工程输出。v2 inference tensor版本检查报错；v3原生HF默认覆盖greedy为采样，3工程输出无效；修正两项后v4原生cached/custom逐token一致，但整段/切分greedy在第54 token分叉，预定工程门槛未过。限定teacher forcing复现已有分叉，未生成新答案；不放宽一致性门槛、不改模型/提示/精度/attention、未跑32题能力或任何压缩。详见[工程失败与诊断](runs/20261028-action-guard-engineering-failure.md)。task_support_gate=null，不能说任务能力失败或通过；当前停止此冻结执行方案，不自动v5。累计78run2702主要输出，本窗口共19run、0新主要输出，工程6条单列。PID均退出、两卡15MiB/0%、compute-app空；无服务/依赖/权重变化。A方法主张no-go、C宽泛主张不立题；D用途未获任务支持，也未建立创新性。旧断点/进行中以下均为历史。

2026-10-28本轮收尾：平台goal报告usageLimited，已停止自有Full-only runner并保留加载前断点；0新主要/工程答案，累计75run2702。候选A方法主张no-go，泛证据充分性/拒答C亦不立题；新动作安全guard仅完成32例原生CPU/训练重叠检查和固定权重下载，能力尚未验证。下一次沿同一冻结Full/NoHistory方案用新目录恢复，不能自动启动压缩。详见[本轮结论与断点](RESEARCH_WINDOW_20261028.md)。收尾两卡15MiB/0%、compute-app空，无自有进程/服务。下方进行中/旧首选均为历史。

2026-10-28论文讨论补充：用户截图的Governance Decay v2与“压缩损害约束/固定保护规则”高度重合；其干预为harness文本摘要/消息淘汰，本项目为实际KV裁剪，但技术层区别不足以单独立题。官方§2–9阅读及与Pitfalls对照见[LITERATURE](LITERATURE.md)。本轮仅本地文献维护，0模型输出、无新实验；未核查或更改既有/其他会话进程，下方持续工作与来源审查状态保留。

2026-10-28持续工作窗口（17:07:39起最长5小时）：[候选A启动审查](PREFIX_RISK_DESIGN_GATE_20261028.md)已否决当前方法主张。LTT已有多风险联合检验，Pareto Testing已有约束风险/成本选择，Risk-Controlled KV支持输入自适应候选；分组、多query与效用指标的组合不足以成为新方法。原建议256模型输出不启动，实验授权仍有效，无需重复许可。CPU精确概率审计882项通过，仅检查数学例子，不能证明新颖性。

同窗口继续审查更窄的“实际压缩KV中证据充分性与有条件拒答”。Compression-Aware Abstention已覆盖训练拒答和真实KV实验；固定作者仓库1426730a...的14源码文件/10AST核验完成，raw下载v1网络超时终止并保留，API v2成功。下一步核对作者公开输出的评分和证据标签，未执行作者代码、未启用新模型矩阵。当前新增3个CPU/来源run已归档，累计62run2702，索引`results/20261028-run-index-prefix-source-audit.json`；另一个公开输出下载运行中未计入该索引。下方A“首选”等表述为历史判断。

选题调研更新：2026-10-28。用户要求寻找可用于小论文/硕士论文的问题，已完成[候选问题与查重报告](TOPIC_SURVEY_20261028.md)。Risk-Controlled KV Eviction已有风险目标/预算选择/Full回退，FlowKV已有重复压缩与多轮指令保持，执行状态遗忘/缓存历史/跨模型安全重用也有近邻；不再把这些宽泛思路当空白。

当前首选**待验证候选**：可复用前缀的按组约束风险与正常效用联合预算选择，须超过全局/逐组LTT、完整规则保护和简单保守预算；仅换指标/按组统计不算创新。条件/例外依赖降为高风险备选，动态撤销等不优先。下一步先离线写一页差异与go/no-go标准，再判断任务可行性；报告中的小试上限未执行，无新启用配置/算法或创新结论。本轮0模型输出，累计59run2702不变，GPU检查两卡15MiB/0%、compute-app空；TREC校准已结束，旧失败gate保持。

更新：2026-10-28。[留出10题复查](runs/20261028-trec-holdout.md)50主要输出＋24工程输出完成，独立审计通过，0截断/运行错误。Full7/10；Snap/随机/Snap-pin/random-pin正确7/6/7/7，格式10/9/10/10；条件损失1/7、2/7、0/7、1/7。随机未保护在一题Full正确问题上输出非法标签Element，保护后恢复。

**当前决策：[本轮校准结束](TREC_CALIBRATION_CONCLUSION_20261028.md)，不自动扩样本/seed/预算/提示/模型，不开发新算法。** 开发32与留出10分别总结，示例大量复用、n小，无一般安全/稳定方法排序/创新结论。下一步先离线收敛具体约束问题及文献差异；下方旧“下一步”均为历史记录，不是待执行指令。原复查提案仍禁用，运行启用快照已归档，IFEval/旧失败gate不变。

累计59run2702主要输出，索引`results/20261028-run-index-trec-holdout.json`；本轮24工程输出单列。原始约119.4MB结果只服务器，自有模型/分析进程退出，两卡15MiB/0%、compute-app空，无新依赖/权重/服务。本地新增三脚本及复查/结论文档，收尾同步。

## 历史进展（最新决策以上文为准）

更新：2026-10-28。[10题留出CPU冻结](runs/20261028-trec-holdout-cpu.md)完成：原42合格减已用32的全部10题保留，原TREC标签10/10匹配，2个语义/拼写注意标记不排除。新复查配置禁用，下一步实现受阶段门槛控制的10题runner，先10 Full通过才跑40压缩。本轮0模型输出，仍无新颖性或一般安全结论，旧gate不变。

当前自有下载/模型进程均退出，两卡最后15MiB/0%。Mistral13完整文件14.50GB仅服务器；环境沿用已有sentencepiece0.2.1，无本轮新增依赖。旧权重/失败完整保留。

## 最新进展：10题留出问题与复查配置冻结

- 全部未用10_id按原hash顺序冻结，未扩长度/换seed/改prompt/gold，7个类别。与开发_id、规范化问题及其示例中的目标问题重叠均0；独立扫描32份实验generations2652行无新_id命中。原TREC500测试标签逐题匹配；官方taxonomy/标签原字节+SHA归档。
- 独特示例问答对仍与开发共享约51.89%–66.43%，新集合1313对中808复用；只能称未用问题复查，不能当独立示例/数据源。两题原拼写/泛where粒度注意标记保留，全部10进主分析，不修gold/剔除以改善结果。
- cases SHAe2b6c2ed...，native prefix2203–4163/suffix18–26、header200/保护并集267、半预算1101–2081可行。2240个随机流pin/unpin层头选择检查、10题重编码/原文与gold/所有SHA通过，不是新的真实模型saliency或质量检查。
- [复查提案](../configs/trec-holdout-recheck-proposal-v1.json) SHA147aea59...，execution_enabled=false。新10题runner需先12个Full工程输出，再10主要Full；exact≥5/10、格式10/10、截断/错误0才进入剩余12压缩工程与40主输出。最多50主要＋24额外，全部四方法/10题保留，分母用本次实际Full正确数，不沿开发19。单轮后收敛，不扫参数。
- 本轮2CPU run（v1误假设末行换行导致解析断言失败、v2修正原文分界且复用已验来源后完成），0模型答案；累计58run2652主输出，索引`results/20261028-run-index-trec-holdout-cpu.json`。源码/失败/逐题来源/重叠/审核/verification/closure全服务器；无新依赖/权重/后台服务，最后两卡15MiB/0%、本轮PID为空。

## 上轮：TREC真实裁剪128输出完成

- 原32题with_demos/50%每层head等预算，四条件exact17/17/16/19，格式31/30/32/32；Full19正确/32格式合规。Full→压缩四转移分别13/6/4/9、17/2/0/13、14/5/2/11、18/1/1/12，损失分母19，改善和全部13Full错题保留。128输出均EOS结束2–8tokens，0截断/error/N/A。
- 真实hook和无hook每层K/V及Full输出相同、首3题复现baseline，四方法100%gather逐值恒等。24额外工程输出含原生HF generate（显式位置适配）与自定义压缩解码，输出/每步原逻辑与物理cache位置一致；不能称无修改HF自然支持裁剪。工程通过后另存启用快照，旧提案/CPU准备配置不改。
- 全32四方法prefix实际K/V字节相同59293696–119906304，header/锚点/索引全通过；真实scores/maps已服务器归档。独立复核128解码与评分、14336head maps及1024head Python排序、source/input/artifact SHA通过。
- Snap未pin/随机未pin3非法标签来自2题，均Full分类已错。完整任务头保护后均合法，但两题仍错；保护Snap相对未pin另有2损失/1改善，总分16低于17。随机header总分19同Full也有1损失1改善，不是逐题无损。本小样本没有Snap优于随机、一般安全效应或新颖性证据。
- 下一步仅CPU冻结未用题目的复查设计：相同1K–4K源范围及排除规则只剩10个原_id候选，需审gold/示例复用、保留同四方法/固定前端并预定Full与停止条件。不能凑32/挑赢家/扩长度后称同分布确认，无新轮已启用配置。
- 本轮1run128主输出＋24校验，累计56run2652主输出，索引`results/20261028-run-index-trec-pruning.json`。约410MB结果只服务器；总50.05秒含加载检查非性能，0失败/新依赖/权重/后台服务，收尾两卡15MiB/0%、本轮PID为空。

## 上轮：TREC裁剪CPU工程预检完成

- 原32题with_demos任务头字符[19,877)共200tokens，锚点68、保护并集267，比共同锚点多199槽；半预算1034–2091全部容纳。真实header无跨token边界，人工边界样例已覆盖；原生ids/字符覆盖/全部输入摘要复核通过。
- 28层/4KVhead、四条件14,336选择索引均合法/唯一/排序/含共同锚点及必要header，实际合成gather同预算同字节；32题100%恒等及reference未改通过。随机score按seed/key/layer/head复现，有/无保护同一随机流；稳定平分规则与6个预期非法输入拒绝通过。
- CPU hook合成参考因果attention/池化/GQA误差≤2.8e-9，输入/cache与输出对象未改；不是BF16模型hook检查。主要fixture head_dim2，另一真实模型形状BF16合成缓存全152363008/半76152832bytes通过，未加载权重。SnapKV maps用合成分数，不能称真实saliency。
- 独立复核全部14,336保存head maps、另1024个head用Python排序重算、32题metadata与所有source/input/artifact SHA均通过。准备配置[trec-pruning-cpu-prepared-v1](../configs/trec-pruning-cpu-prepared-v1.json) SHA892bde36...仍禁用，CPU工程true、真实模型工程false。
- 下一步实现独立压缩runner，最多24工程输出验证首3题hook不改每层K/V/Full输出、100%gather、原生compressed cached与custom的逻辑/物理位置；通过才另存执行快照并跑原32×4最多128压缩输出。旧Full-only custom断言physical==logical不能直接用于裁剪。baseline19/32仍复用，全部13错题保留；结果只作分类/标签格式校准，不自动建立安全或创新结论。
- 本轮1CPU run0新答案，累计55run2524主要输出，索引`results/20261028-run-index-trec-pruning-cpu.json`；约361.8MB maps/证据只服务器。无失败/新依赖/权重/后台服务，收尾两卡15MiB/0%、无本轮PID。

## 上轮：TREC Full KV能力关卡完成

- 冻结原32题×两输入条件64输出完成；有示例exact19/32，无示例11/32，全部标签格式32/32，均EOS结束2–8tokens、0截断/error/N/A。有→无示例C→C10、C→W9、W→C1、W→W12，不能称为Full→压缩。
- 首3题×两条件native整段/native cached/custom cached逐token一致（另18校验输出），分支clone逐K/V相等/存储独立、reference未修改，实测57344prefixKV bytes/token；64输入/tokenizer与8判分fixture复核通过。工程检查后、主生成前另存execution_snapshot启用本次执行，原能力提案保持原样。
- with exact≥16、截断≤3、C→W≥8的描述性最低支持通过（19/0/9），并非旧权限95%标准或统计功效保证。有/无示例同时改变长度/位置，结果只支持此小队列的分类能力线索，没有标签格式失守、安全或裁剪效应证据。全部13个with错题仍留总体。
- 新配置[trec-pruning-calibration-proposal-v1](../configs/trec-pruning-calibration-proposal-v1.json)禁用，先CPU审header原生token边界/跨边界成本、每层/head floor(N/2)、sink4/recent64、完整任务头/随机对照的等字节、索引/100%恒等和随机重放。四条件×原全32最多128新压缩输出，实际hook/Full/100%gather检查另限24，未执行。baseline引用本轮32有示例，不能挑9个受益题或19个正确题替代总体。
- 本轮1run64主输出，累计54run2524条，索引`results/20261028-run-index-trec-full.json`；源码/输入/模型config/执行快照/输出/独立重算/closure SHA通过。GPU0单卡，26.97秒含加载检查非性能；无新依赖/权重/服务，收尾两卡15MiB/0%、本轮PID为空。

## 上轮：TREC真实数据与32题能力关卡准备

- 固定官方HF zai-org/LongBench revision5e628be450b7e67fb7ae6e201bd6d8f7056f7672；114MB原归档SHA与metadata一致，提取TREC 6,360,293bytes/200题，SHA20a88e14...。服务器HF连接超时保留v1，Windows二进制内存管道经SSH转存同一官方文件为v2，本地无原始数据文件；无第三方镜像/远程dataset脚本执行。
- 200题Qwen system(header+原context)/user(原input)原生prefix1886–11474，中位6911，44题在1024–4096。50标签/实际35类；发现1个示例问题两种标签（28context涉及，2个context内部冲突）、1个目标在自身示例中出现，全部保留。结构/标签集合通过不等于语义gold全验证或模型必须依赖context。
- 按源prefix1024–4096、无冲突/全局歧义示例、无自身目标示例筛至42，再按固定hash顺序取32；在任何模型输出前冻结。两条件共享50标签列表与exact-label指令，只移除示例，query/gold不变，32对suffix ids相同；with prefix2069–4182/without205。新前端明确改编，长度/位置不同不是等预算或纯内容因果对照。
- 配置[trec-context-gate-proposal-v1](../configs/trec-context-gate-proposal-v1.json)与服务端一致，cases SHAe709d4bd...，proposal SHA6e9c61d1...，execution_enabled=false。8个official首行兼容分/完整exact与格式的判分fixture通过；未加载模型或做真实缓存检查。
- 下一步仅此能力门槛：先首3题两条件native/cached/custom逐token一致，后原32×2 Full KV、greedy/penalty1/maxnew64；有示例exact至少16、截断最多3、有对/无错至少8对，否则停止，不换题/修提示。所有64保留含错题/截断/N/A，四转移是有→无示例，不是Full→压缩；门槛为描述性可行性非显著性。当前不定义裁剪矩阵或安全实验。
- 本轮3run0模型输出，累计53run2460主输出，索引`results/20261028-run-index-trec-preflight.json`；全部原始/失败/源码/输入摘要/closure只服务器。无新依赖/权重/服务，最后两卡15MiB/0%、本轮PID为空。

## 上轮：SystemCheck来源与前端审查

- 固定Pitfalls73079e1...、SystemCheck ed829f6...、LongBench源码2e00731...，25份source/license/data全部Git blob核验、12Python AST；不执行上游模块。S-IFEval541题，system前缀10–108tokens、默认prepend后34–132；Pitfalls539题，加标准defense后118–216，全部不满足旧256–2048条件。tokenizer前缀关系通过不等于缓存生成通过。
- Pitfalls固定快照缺key1000/3401，余539与SystemCheck逐key一致；SystemCheck相对Google改过key1012重复文本kwargs及2题prompt字面内容。旧数据/标注不能混用，不自行补两题声称完整论文复现。作者前端在user之前压缩system，是query-blind；并非上一轮全任务已知设置。
- LongBench TREC官方模板/评分/pred已读：标签包含与多命中分数、先取首行，不等于整段严格约束分数；官方TREC不套chat前端。Pitfalls附录I已覆盖长TREC分类/防泄漏，复现不能当创新。TREC原始数据/HF revision/许可细节/样本SHA与实际长度尚未冻结，不能启动模型。
- 本轮2run0输出（raw获取5次timeout后终止自有任务、API v2完成；补充分析单列），累计50run2460主输出，索引`results/20261028-run-index-systemcheck-audit.json`。源码/数据/失败/逐题审计/closure全部服务器；无新依赖/权重/后台，最后两卡15MiB/0%、本轮PID为空。
- 下一步具体任务：固定官方LongBench TREC数据仓库实际重定向与revision、文件SHA/许可/样本key，CPU核验context示例/input/answers/all_classes、重复冲突、新前端prefix/suffix和预算；不按模型成绩筛题或中间截断凑长度。先独立设计再模型，安全/分类/约束指标分开，并审内容是否依赖上下文。

## 上轮：IFEval长度预检停止

- 官方固定数据207111bytes/541唯一key，数据与Git blob摘要通过；原生Qwen2.5前缀最小39、中位67、P90为99、最大387，只有key2859满足256–2048。540题按预定长度排除，未按模型输出筛题、未填充/放宽阈值。
- 541题native prefix/header切分检查通过，自动默认system消息已计入prefix；这不等于缓存/生成路径验证。长度先决条件失败，官方checker/依赖/正负边界样例、随机选择器与真实KV检查均未执行，不能标通过或生成执行配置。
- 本轮1run、0模型输出，累计48run2460主输出，索引`results/20261028-run-index-ifeval-preflight.json`。原始数据/逐题长度/tokenizer与源码摘要/console/manifest/停止原因均服务器。无新依赖/权重/后台服务；两卡最后15MiB/0%、无本轮PID。
- 下一步只做长上下文约束任务来源和可行性审查，优先审Pitfalls SystemCheck的构造/前端/许可、约束位置及内容能力对照。需要独立新方案与CPU预检；旧IFEval提案与AccessDenied失败均不救回。可运行校准也不等于创新。

## 上轮：研究收敛与标准测量校准提案

- 重算旧manifest/generations：Access原版3配置8/0/0、8/7/3、8/0/2；小目录Full47/48、规则7、全部事实48、随机10（各48）；新结构化基线96/96、32行权限/路由各23/24，均与旧记录一致。未重打分或产生新独立样本，仍无安全特异绑定损坏证据。
- KVDiagnosis arXiv2608.09412v1/作者仓库153699e...已覆盖Full配对C→W与多种诊断；Pitfalls覆盖多指令跟随。仅换IFEval/做通用诊断不构成新意，不将预印本页眉当录用证明，未复现作者结果。
- 新提案只作测量校准：现有Qwen2.5、原生user、不改官方prompt、完整任务已知的query-aware post-prefill；固定源/32题（尚未冻结IDs）/最多160输出、官方strict与全样本四转移，真实KV字节/共享锚点/三路径前置检查。旧权限门槛不变，新支持量规则不回填旧失败gate；IFEval不等于事实/安全质量。
- 已存10份固定source/license并验Git blob、4Python AST，不执行上游代码或装包。CPU审计v1因源归档未就绪失败、v2完成，全部保留。本轮2run0模型输出，累计47run2460条，索引`results/20261028-run-index-research-reset.json`；环境不变，两卡15MiB/0%，无自有PID。

## 上轮：Mistral原版Full基线

- 实际291个weight tensor全部BF16、7,248,023,552参数元素，index/头与完整摘要通过；运行时32Full层、无滑窗。原版消息/候选预编码ids/cut/oracle/source均核验，未改提示/样本/解码。
- 本人8/8，同事0/8，缺失2/8；全部brace格式正确、8–9tokens，无截断。8个同事最终块均返回目标薪资，与本人输出8/8逐token相同。缺失4次他人禁用薪资、1次与示例值相同、1次可见资料/示例均无匹配，0/8三元组全对。12次禁用薪资都在最终块，非raw-only解释。
- 首三类请求native整段/native cached/custom cached逐token一致，实测131072KV bytes/token；首三prefix431357952/430964736/415760384bytes。工程核验不能当能力通过。Mistral门槛false，无确认目录、无压缩，未尝试第二设置。
- 本轮2run24主输出，累计45run2460条，另6缓存输出单列；索引`results/20261028-run-index-mistral-full.json`，结果约643MB，方向models约30.90GB另计。下载0实际失败、1188.73秒；模型35.69秒含加载/检查，非性能比较。
- 3配置/2族在此固定发展适配均未过Full门槛；停止这套模板继续换模型/改提示和压缩。下一步离线梳理Full稳定性、事实检索/权限/缺失/前端、简单事实保留上限与未证假设，先形成新任务的独立理由与冻结设计，不默认启动更多推理。

## 上轮：Mistral固定候选核查

- 固定mistralai/Mistral-7B-Instruct-v0.3 revision c170c708c41dac9275d15a8fff4eca08d52bab71；gated=false/private=false，README声明Apache-2.0。只选这一候选，理由为独立族、公开、具体配置Full及可用资源，不假设安全/任务能力更强。
- 10metadata/tokenizer文件3,310,406bytes全部官方摘要通过；当前Transformers meta实例32Full层、32query/8KV/head128、sliding_window=None、state名称与checkpoint index一致，形状估算7.248B参数。实际权重dtype/完整性未验证；3HF分片约14.50GB清单已锁，未下载。
- 原system/user内容不改，native模板合入INST段，不能当Qwen式独立角色token；system-only模板只返回<s>，需按完整native串的query offset切前缀。48条oracle/原生渲染/两query前缀不变检查、48条slow/fast ids逐项一致通过，尚无cached生成或能力验证。
- v1缺sentencepiece导致tokenizer初始化失败，保留run/source/log；仅venv新增sentencepiece0.2.1 --no-deps后v2复用校验metadata完成。基环境/旧项目未变。BF16应131072KV bytes/token，参数+最大prefix+512decode KV估算约15.00GB、不含workspace，不称实测峰值。
- 本轮2run0模型输出，累计43run2436主输出；索引`results/20261028-run-index-mistral-candidate.json`。无GPU模型任务，收尾CUDA未初始化、两卡15MiB/0%、自有PID为空。下一步按Mistral清单适配下载器，完整校验后原版24发展集Full，过门槛才确认；不继续改提示。

## 上轮：输出指令编辑包审计

- 两条件各24原发展请求：original_replay旧policy原样；delivery_only仅4处显式输出指令改为不输出解释，policy/完整examples/可信资料/身份/问题/gold逐字节保留。原版24输出逐token同旧run，严格8/7/3；编辑版严格8/0/0，24/24只有brace块，无截断。
- 编辑同事6/8最终块禁用薪资（5次目标、1次另一无权员工）；另2条返回主体自己的薪资，是答错对象而非禁用披露。缺失7次误拒绝、1次另一无权员工薪资。0/8三元组全对。不能将所有错误或所有薪资输出都算越权。
- 全24输入/prefix增加14tokens、CONTEXT后移20tokens，未配平位置；四处指令包足以在本发展集伴随失败，不证明解释/隐式推理的单独因果作用。6首例缓存三路径逐token一致、147456bytes/token，源/输入/分析SHA通过。
- 本轮2run48主输出（含旧版重复控制），累计41run2436条；另外12条缓存输出单列。索引`results/20261028-run-index-delivery.json`，原始数据全服务器；环境/权重未变，自有PID为空，两卡最后15MiB/0%。
- 决策：停止这套AccessDenied模板提示搜索/裁剪，保留前端敏感性负结果。下一步只读核查独立模型族的一个固定候选（Full配置/公开revision/许可/资源），沿原版冻结任务做有独立理由的模型选择；不挑成功子集、放宽门槛或提前运行确认集。

## 上轮：明确答案契约的单次检查

- 仅一版预注册联合适配：原48条资料/身份/问题完整标记块逐字节保留、gold不变，统一缺失优先及本人/HR/主管权限，只交付brace块；新契约不是旧基准原样复现或防御。发展/确认数据均推理前冻结，仅发展24实际推理。
- Qwen3同版本/非thinking/greedy：本人8/8，同事0/8，缺失6/8（base1/3误拒答）；24/24格式正确、8–9tokens、无截断。8次同事最终块均返回目标薪资，和本人输出逐token相同，属于实际交付披露；0/8三元组全对，门槛失败。三类首例缓存三路径逐token相同、147456bytes/token。
- 新policy/示例/输出要求/长度与位置同时变化，不能把退化唯一归因于“没有解释”。本轮不再尝试第二提示版本，不跑确认/压缩。下一步先冻结有限因素审计，避免继续换模板到过线；若Full仍不稳定则收缩任务。
- 本轮3run24主输出，累计39run2388条，索引`results/20261028-run-index-contract.json`；另6条缓存重复校验单列。原始数据/日志均服务器；依赖/权重未变，自有PID为空，两卡最后15MiB/0%。

## 上轮：Qwen3冻结模型复查

- 同24发展集、system/user消息及gold与旧模型一致，只有模型原生wrapper变化；BF16 SDPA、enable_thinking=false、greedy、penalty1、512预算。36层Full Attention运行时核对，399个BF16 tensor/index一致；不是第二模型族。
- 本人8/8；同事最终块拒绝8/8，但1条块外解释输出目标薪资，全文严格正确7/8；缺失3/8，其余5次误拒绝。全部格式正确、62–94输出tokens、无截断，3/8个triplet全对。旧Qwen2.5对应严格分为8/8、0/8、0/8；属于发展集改善，不是确认结果或压缩效果。
- 首三分支native整段/native cached/custom cached逐token相同，实测147456 KV bytes/prefix token。源prompt明确要求输出plain-text thought process，所以关闭模型原生thinking并不等于没有块外解释；原app只交付brace答案块，本次1次raw披露不能称最终交付泄漏。即使只看最终块，缺失3/8仍独立导致门槛失败。
- 预先冻结的确认context2258–2265保留未推理；未换thinking/提示/样本直至通过，也未裁剪。下一步先固定应用交付边界与任务定义，区分权限、缺失、块外披露，再预注册新的评测选择；不删除失败样本或事后放宽旧门槛。
- 本轮4run24主输出（下载中断/下载完成/确认数据准备/发展模型），累计36run2364条；索引`results/20261028-run-index-qwen3.json`。另3请求6条缓存校验非独立主要样本；全部原始结果在服务器。

## 最新进展：AccessDenied薪资权限

- 记录：[20261028-accessdenied-pilot](runs/20261028-accessdenied-pilot.md)。官方固定seed0真实分隔符U+001E，3500源行/500salary；按推理前可见事实条件选源行2250–2257，8个context×本人/同事/缺失3分支=24请求。显式可信身份补role/department/HR状态，oracle从渲染字段核验；是受控改编，不是原版完整benchmark复现。
- 沿作者HF实际原生system+user拆分，规则/身份/context/reminders均system、query另user；身份在prefix，属于identity-aware/query-blind。全部格式正确，仅生成8–9tokens，无截断。
- Full本人8/8；同事0/8，8个最终答案块均含目标薪资，与本人输出8/8逐token相同；缺失0/8，均误用拒绝短句。8/8最终块披露不是仅块外推理出现。首三分支native整段/native缓存/custom缓存逐token相同，非缓存路径错误证据。
- 本轮不换提示/重抽/裁剪，冻结24条作为后续模型选择发展集。Qwen3-8B fixed revision `b968826d...`配置已核对无sliding_window，符合Full Attention，但尚无权重/加载/权限能力验证；Qwen2评分器不能直接冒充适配了Qwen3。
- 本轮2run24主输出，累计32run2340条，索引 `results/20261028-run-index-access.json`；另外3请求6条缓存校验单列。原始数据全服务器，依赖/权重未变，未启动服务。

## 最新进展：分开检索与权限判断

- 记录：[20261028-benchmark-baselines](runs/20261028-benchmark-baselines.md)。固定旧版RULER生成函数、Qwen原生HF前端的轻量适配，16种子×64/128干扰句=32题，实际1767/3431token。正确值包含32/32，均复述query key后给正确value；严格只含正确数字的附加格式分为0，不称精确匹配或完整RULER总分复现。
- OrgAccess官方GitHub revision `c65ef95f...` easy快照3.2MB/38,280行，前32条固定0–31，格式32/32、原标签一致16/32。推理前已审出10条partial与官方判定说明冲突，29条未给实际biometric完成状态；所以该分数只是一致率，不是正确/安全率。
- 全快照精确字段分组发现：相同permissions+query却有不同标准标签的593组；连同role/timestamp也相同为592组。原raw字符串600组包含拼写别名，不用其作为语义冲突计数。具体117/433行输入相同，full/partial理由却假定相反的验证状态。结论仅限此固定GitHub快照，不外推HF其他版本。
- 决策：保留RULER作为能力小控制；暂停OrgAccess该快照的正确性门槛，不继续修旧合成模板。下一步审AccessDenied的显式权限/gold生成与全文扫描，冻结可信允许/禁止/缺失样本，再做Full。
- 本轮2run64主要输出，累计30run2316条；另2请求4条缓存校验存checks，三生成路径逐token相同。索引 `results/20261028-run-index-benchmarks.json`，数据/原始结果全留服务器。仅本方向venv新增pyarrow19.0.1，基环境/模型未改，详情根ENVIRONMENT。

## 最新进展：前端与位置审计

- 记录：[20261027-frontend-audit](runs/20261027-frontend-audit.md)。原冻结48请求×5条件=240主要输出：original权限/路由各23/24；仅位置配平各23/24；single system（是否配平位置）均23/24与22/24。预定single_aligned未达门槛，base700–705新世界未运行，不挑其他变体继续。
- row_given可信目标行诊断各24/24，但额外提供目标事实、增加38–40输入token，不能充当真实基线、压缩方法或唯一机制证明。与既有lookup-only结果一起，支持下一步将事实检索和规则判断分开检查。
- 4个非oracle条件完整输入1265 tokens；aligned两任务全部fact token位置一致、首事实170，prefix1216/suffix49。original48输出与旧source逐token相同；每变体首case4问共20请求，原生整段/原生缓存/custom缓存三路逐token一致（另40条校验输出存检查文件）。
- 固定提交只读核查RULER/OrgAccess/AccessDeniedInc共12个官方source/license文件，均获取并保存在服务器、6个Python文件AST检查通过；不import上游、不下载完整数据集/模型、不调用外部LLM。OrgAccess示例有一项label/rationale冲突和placeholder预测，不外推到整个HF数据集；AccessDenied评分抽取答案块，后续仍需本项目全文扫描。
- 本轮2个run（模型240输出＋source audit0输出），累计28run2252主要输出；索引 `results/20261027-run-index-frontend.json`。全部环境包/权重未变，两卡15MiB/0%、本轮实验PID为空。

## 最新进展：查组稳定性

- 记录：[20261027-lookup-stability](runs/20261027-lookup-stability.md)。同目录旧48请求加固定two-shot后两任务各22/24（原各23/24），均新增不匹配值输出；新基础世界500–505中权限46/48、路由44/48，世界全对10/12与8/12，未过门槛。
- 单独取消组别筛选、保持原目录token/位置及prefix1222/suffix43的lookup-only：24问23对。原错误r4443的ID/payload正确，group仍错；无裁剪时也存在属性关联错误，但输出不能唯一证明内部机制。
- 另立原模板16行、世界600–605：权限45/48、路由44/48；各有1次不匹配值输出，世界全对9/12和8/12，仍失败。16行prefix726/suffix44、预算363，全部事实原位置仍无法固定保留。没有再尝试其他模板/规模。
- 两任务长度和前缀字节已配平，但规则长度导致目录起点仍差19 tokens，不能把任务差当安全特异证据。下一步先审查单system前端和任务选择，分开直接检索与约束判断并配平事实位置；不是继续加提示直到过门槛。
- 本轮5个run264输出，含0输出OOM；累计26run2012条，索引 `results/20261027-run-index-lookup.json`。GPU0中途有其他进程造成一次加载OOM，已记录并切空闲GPU1；本轮任务均退出，GPU1已释放，其他进程未改动。依赖/权重未变。

## 最新进展：多事实设置

- 记录：[20261027-scale-queryblind](runs/20261027-scale-queryblind.md)。32/64行替代背景填充，50%预算无法固定全部事实位置。32行prefix=1222 tokens；v2所有任务/世界suffix=43 tokens，完整前缀KV=70,074,368 bytes。
- 世界300–302：32行Full权限24/24、路由24/24；64行23/24、20/24，后者规模停止。新世界400–402的32行权限/路由各23/24，但各仅5/6世界四问全对，未达90%门槛；保留两个错误，不做裁剪效果比较。
- 两个新错误为同一对象的record_group查错，权限与公共路由输出完全相同并误拒答。48个冻结请求整段原生generate与自定义缓存逐token相同，原生也有相同错误；这是一般检索失败线索，不证明安全特异绑定损坏。
- 固定版本Expected Attention评分及规则/完整JSON行/随机行结构对照完成工程检查：评分hook不改变Full cache、16输出与无hook逐token相同、首世界4问原生cached相同、2688层/头索引断言和50%字节检查通过。没有运行压缩输出效果矩阵。
- screen现要求对应Full门槛通过且cases字节相同；失败门槛拒绝检查已执行，在加载模型前退出并保存manifest/日志。
- 查重补读TableKV正文：已比较query-aware Finch与query-agnostic Ada EA；结构化输入+KV/EA本身不是创新。KVzip未复现，第二模型族未固定。
- 本轮6个run共208输出（含重复控制），累计21个run1748输出；新索引 `results/20261027-run-index-scale.json`。原始数据全留服务器，无运行进程，环境包/权重未变。

## 执行位置与当前授权

- 最新用户定位：普通 Transformer、各层 Full Attention；不复制旧 nano-vllm 的代码或文件，不采用 Qwen3.5 Hybrid 基线。目标为小论文或毕业论文，尚未正式定题。
- 本地：仅代码/配置/文档。
- 服务器方向路径：`/home/user/jhk/project/Directional Exploration/kv-pruning`。
- 远端创建：已成功登录，目录与首轮文档已创建，SHA-256 校验通过。
- 用户最新明确：“这个会话已经是我新开的会话了，可以启动实验”。本会话已获授权，可在服务器进行正确性检查与小规模配对筛查；此前讨论会话限制不再阻止本次明确任务。仍不从旧 nano-vllm 复制代码或文件。

## 已完成

- 建立本方向文档与交接入口。
- 保存已有项目的用户描述，详见根 docs/EXISTING_PROJECT.md。
- 明确候选问题：裁剪是否削弱必要约束，以及能否用缓存干预定位原因。
- 2026-10-26 再次通过指定私钥成功登录服务器，读取两端方向文档；方向目录目前只有 7 个 Markdown 文件，无源码或实验结果。
- 找到已有项目 `/home/user/jhk/project/nano-vllm`，读取 README、评测索引与 DeltaNet TP 文档；HEAD 为 `728e5e4c7e1d9449a44115f6bc327519e67918c0`，存在未提交修改，尚未审计实现。
- 第二轮查重与重叠风险判断见 [NOVELTY_REVIEW](NOVELTY_REVIEW.md)：增加 TableKV、StepKV、OrgAccess、ACCESS DENIED INC、Role-Conditioned Refusals 等；“关系成组保留”不能直接当新算法。
- 固定阅读版本的静态核查：kvpress `2d66e74`、Pitfalls `73079e1`、Safety Tax `e054171`；核查了 kvpress 真实 gather 裁剪、GQA 评分、默认 user 模板和后续 query 位置，以及公平 SnapKV 的局部观察窗/eager 要求，未运行源码。
- 核对 Qwen2.5-7B-Instruct 固定版本配置，纯 Full Attention/GQA 候选与本方向范围相符；权重、运行环境和第二模型族尚未准备。
- 新增 [VALIDATION_PROTOCOL](VALIDATION_PROTOCOL.md)，写明反事实权限配对、同构非安全关系对照、角色/缓存正确性门槛、工作量与停止标准；没有生成实验数据。
- 以上“无源码/无实验”条目为前轮历史。2026-10-27 获明确授权后已独立建立 `scripts/pilot.py`、缓存正确性测试、原生生成对照与统计脚本；没有从旧 nano-vllm 复制代码或文件。
- 服务器已有完整 Qwen2.5-7B-Instruct revision `a09a354...`，直接复用，无新模型下载；在本方向 `.venv` 中借用 deep_learning 已安装的 Torch2.5.1+cu121/Transformers4.57.1，未修改基环境。单GPU0运行，详见根 ENVIRONMENT。
- 完成9个主运行、292条开发记录，另有原生生成诊断与FP32缓存测试；所有原始数据留服务器。完整命令、脚本摘要、失败和结果见 [本轮实验记录](runs/20261027-pilot.md)。
- 原生HF cached generate逐token对照、100%保留/分支一致、FP32分段与压缩后缀因果检查通过。早期BF16 chunk误差失败与检查目标修订均保留，不将旧失败改写为通过。
- 简化短权限任务502token Full KV 12/12；统一sink4、保留75%时适配SnapKV允许4/6、禁止披露2/6；完整规则保护允许1/6、禁止披露0/6。公平配额只是固定评分消融，不是作者完整公平SnapKV。
- 可信组别的权限任务 Full KV 在实际1014/4086token仅9/12、10/12；短同构路由对照9/12，未达到能力门槛。未执行原计划长上下文压缩矩阵，未开发关系保留算法。
- 后续进展见 [基线审计与事实诊断](runs/20261027-baseline-audit.md)，上述旧模板结果不覆写。独立oracle确认48个冻结请求标签/身份/模板正确；将原生重复惩罚从模型默认1.05显式对齐为自定义循环的1.0后，整段原生/原生缓存/自定义缓存在48请求上全部逐token一致。
- 固定JSON组别读出方案在旧48请求通过后，在新基础世界100–105的1K/4K权限/路由96请求全部通过；同时改变了措辞、格式、负例标记与预算，不能单独归因于查组或宣称原直接输出模板已可靠。
- 在另一批基础世界200–202完成336请求矩阵，Full KV 47/48，包含1个新路由错误。288个压缩请求严格正确32，主要为输出合同/字段不符、资源组别和payload错误；权限侧未观测合成秘密值输出，路由有1例非匹配值输出，不称隐私泄漏。
- 补完192请求等预算诊断：相同48请求，Full KV47/48；50% KV仅保护规则7/48，保护规则+全部4条JSON事实48/48，保护规则+等量随机位置10/48。每case方法K/V字节一致、保护位置数量相同且每层/head保留断言通过；这是结构化元数据诊断上限，不是新方法。
- 本轮6个run共1248记录，累计15个主run1540记录，含大量重复控制，不能当独立样本数。所有新源码快照/manifest摘要和行数核验通过；原始结果总约489MB留服务器，索引 `results/20261027-run-index-followup.json`。

## 尚未完成

- [x] 定位现有 nano-vLLM 项目（服务器同级目录 `nano-vllm`）。
- [x] 固定首轮模型、tokenizer、BF16/SDPA环境并实际加载运行；基线失败分析尚未完成。第二模型族未固定，旧 nano-vllm 审计不是前置任务。
- [ ] 补 TableKV 全文/源码和权限基准细节、核查各近邻可运行实现；第二轮查重已完成，但没有排除所有重叠。
- [ ] 固定模型、完整 KV 基线、裁剪预算与评测任务。
- [x] 完成短上下文开发级配对预实验与逐样本保存；不能视为原两跳/长上下文假设的确认。
- [x] 在固定结构化输出任务的1K/4K权限与路由上通过新96请求质量检查，并完成更小的独立世界裁剪与事实诊断；新矩阵Full KV仍有1例错误，未删样本。
- [ ] AccessDenied确定性显式身份/目标presence检查已完成，但当前7B Full门槛失败；下一步锁定候选纯Full Attention模型的权重版本/推理模式，在同24条冻结发展集复查，过后再用独立context确认。EA效果比较、KVzip及第二模型族仍未完成；不降低门槛。
- [ ] 决定是否继续此方向及具体方法。

## 决策与风险

- 2026-10-26 用户纠正此前复用旧项目的假设；以上旧项目定位记录仅作历史背景，不能据其安排复制或移植任务。
- 条件约束关系保持进入进一步查重/验证设计阶段，尚未定题或选定算法。核心门槛是区分裁剪特有效应、一般关系推理退化与固定规则保护不足。
- 当前结论是“宽泛创新风险高，窄问题有条件保留”。未找到直接相同设置不等于首次；若公平裁剪或完整规则保护解决，应调整方法主张。
- Pitfalls 已研究多指令退化、泄漏及白名单/公平裁剪；Safety Tax 仓库包含因果干预入口。不能把现象、固定保护、分配预算或恢复干预本身当作新贡献。
- 先做失败机制诊断，再设计新方法；不预设裁剪一定造成安全退化。
- 保护固定 system 前缀、换模型、简单复现不能直接当作创新。
- 截图中的准确率和显存数字不是本目录的测量结果。
- 旧项目文档记载：DeltaNet 分片为显式启用的实验路径，默认保持复制执行；整模型 BF16 严格 logits 检查未通过，已测两组负载未提速。本次仅阅读文档，不构成复测或源码验证。
- 当前本会话所有实验进程已退出，无后台服务/端口；最后核查两张GPU各15MiB、0%利用率，仅显示进程。服务器其他既有进程未改动，不宣称整台服务器无任务。
- 新观察仍限于合成、单模型和小样本：新基线6个基础世界、核心矩阵/诊断3个基础世界；可信组别已由运行时给定，不是完整两跳；两任务语义匹配但实际长度相差约15token。保护全部事实能解决当前任务，暂不开发关系感知算法或主张安全特异性。

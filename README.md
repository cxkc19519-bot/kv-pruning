# KV 缓存压缩与输出约束可靠性

2026-11-05：用户指定 GitHub 仓库 [cxkc19519-bot/kv-pruning](https://github.com/cxkc19519-bot/kv-pruning) 用于项目进度同步；新增 [进度概览](docs/PROGRESS.md)。本次发布代码、配置和文档，保留历史失败与停止决定；模型、数据、原始结果、日志和凭据不入库。11-04 结构化输出搁置、H3 停止和泛 KV 暂停保持，累计仍为 147runs/3038历史主回答；未启动实验、安装或后台任务。仓库提交状态以 GitHub main 提交记录为准，下方“GitHub 未配置”为历史记录。


2026-11-04 当前决策：**搁置 N1 结构化输出资源生命周期分支，关闭默认后续实施。** 用户认为当前结构化方向不好做；讨论确认真实 vLLM 服务中的资源损害、结构化特有问题及现有机制不足均未建立。单线程池排队不能当作调度缺陷或安全证据。详见 [搁置决定](docs/STRUCTURED_OUTPUT_STOP_DECISION_20261104.md) / [当前分支状态](docs/STRUCTURED_OUTPUT_BRANCH_STATE_20261104.json)。不实施或执行旧自然观测草案，不开展取消/压力对照；旧草案、readiness、结果原样保留，下方所有“下一条实施”均为已被覆盖的历史记录。147runs/3038历史主回答不变，H3停止/泛KV暂停保持；后续先重新明确候选问题，不自动恢复旧实验。本轮仅文档维护，未启动实验或后台任务，未重新审计既有进程。


2026-11-02：[资源观测尺度审阅](docs/RESOURCE_OBSERVABILITY_REVIEW_20261102.md)完成。离线独立核694个既有调用，最大0.449ms，旧外部tick/采样10ms无法分摊单调用CPU；同槽恢复未测。固定当前官方取消/动态编译源码，科学强对照部署仍未就绪。已冻结自然执行观测协议（18工作+1空控制、同池单槽、无取消/人为延时），runner未实现/执行关闭，下一条实施并另登记。0新后端执行，仍147runs3038主；文档同步服务器、原始仅服务器，N1实效/新颖性未立。本条取代旧待办。

2026-11-02：[明确类型记录族检查](docs/runs/20261102-typed-object.md)完成。新事前定义1/2/4字段、每组7个业务正负例，两后端各21/21一致、正例EOS停止，独立验收通过。覆盖仅小型固定字段字符串枚举记录；旧45题失败不改，未测资源回收/取消效果。下一条冻结有界资源可观测性筛查及强对照兼容性，不直接压测或推断新颖性。147runs3038主，4自有PID退出，文档同步服务器、原始仅服务器。本条取代旧待办。

2026-11-02收尾：[原8组45实例语义检查](docs/runs/20261101-finite-semantic.md)完成，gate未过。XGrammar31/45一致（4误接收/10误拒绝），LL39/45一致（2误拒绝/4 oneOf未支持），全部90格及EOS/mask独立核验。没有超时或mask/commit冲突；不能按当前负载直接做等语义资源回收对照。下一步独立定义共同支持的明确类型schema族，保留本轮失败，不筛28个共同正确实例救gate。146runs3038主，4自有PID退出，原始仅服务器、文档同步。本条取代旧待办。

2026-11-01 最新：[有限UTF8域/工厂检查](docs/runs/20261101-utf8-domain-factory.md)/[readiness](docs/UTF8_DOMAIN_FACTORY_READINESS_20261101.json)完成。新有限UTF8域的适配/无schema构造预检通过：133普通字符逐项/整串往返、8正例、7负例、EOS元数据及425调用独立验收均通过；X编译器构造完成，LL仅Tokenizer构造，schema/LLMatcher仍留后续。45原文本全可表达而语义执行0，不救旧257byte/FF或cold5 gate。下一步独立登记原8schema45标签正确性，不重做8/23/12或直接跑资源干扰。新增1CPUrun，145runs3038主，4自有PID全退出、归档全回读，文档同步服务器，原始仅服务器；N1未定题。本条取代旧待办。

2026-11-01 最新：[崩溃诊断与完整启动](docs/runs/20261101-startup-fault-probe.md)/[readiness](docs/STARTUP_FAULT_READINESS_20261101.json)完成。GDB封装v1失败、v2两Torch导入完成但原validator身份判读失败，离线v3重判通过，全部原失败保留；单对未复现旧SIGSEGV，根因未知。另登记fatal-only完整启动从父spawn计7.802948秒通过Torch/XGrammar导入及CUDA false检查，独立账本通过；只是library-ready，退出即失效，factory/语义未验。下一条冻结共同合法UTF8域与factory正确性，不重做8/23/12、不直接跑45标签。新增3CPUrun，144runs3038主，23自有PID退出，原始仅服务器、文档同步；N1未定题，旧cold5/FF gate保持false。本条取代旧待办。

2026-11-01 最新：[分阶段合同验收与启动记录](docs/runs/20261101-phase-contract.md)/[readiness](docs/PHASE_CONTRACT_READINESS_20261101.json)完成。8项标准库状态/时钟验收通过，独立重算9份账本；随后另登记的新fresh启动在Torch导入期间SIGSEGV/-11，未进XGrammar、未达import-ready，也不是30秒超时。软件正确不代表后端就绪，原冷启动5秒/FF/语义gate保持false，45标签未跑。下一条先只读定位此次崩溃与诊断机制，另冻有界诊断后才可再执行，不自动重试。新增2CPUrun（含1失败）、累计141runs3038主；7自有PID全退出、归档全回读，文档/代码同步服务器，原始仅服务器，GitHub未配置。N1仍未定题，本条取代旧待办。

2026-11-01 最新：[启动／请求边界审阅](docs/STARTUP_REQUEST_SCOPE_REVIEW_20261101.md)及[禁用契约](configs/startup-request-contract-draft-v1.json)完成。旧5秒测冷导入，X开始时只余1.908秒，schema调用0；旧gate保持false。新范围分一次性启动／cold-first／warm请求，拟import-only启动30秒、全程45秒，未来请求5秒涵盖验证/排队/编译/首次mask；不是已执行的新SLO。下一条实现并登记8项标准库状态/时钟验收，通过后另登记fresh启动，不自动跑45标签。139runs3038主不变，原始只服务器，文档同步。本条取代旧待办。

2026-11-01 最新：[精确导入边界验收](docs/runs/20261101-import-boundary.md)完成，[readiness](docs/IMPORT_BOUNDARY_READINESS_20261101.json)优先。v1软件20通过/真实遇dill writer，独立v2补精确固定字符sink模式、23项通过；真实v2无观测拒绝，Torch已导入、进入XGrammar→Transformers，但仍被原组合5秒截止删失，导入gate false。没有加时或运行45标签。下一条先离线核启动与单次请求工作预算边界，不把冷启动当编译成本。4run全留档，139runs3038主，16自有PID全退出，原始仅服务器、文档同步。本条取代旧待办。

2026-11-01 最新：[最小诊断完成](docs/runs/20261101-backend-diagnostic.md)/[readiness](docs/BACKEND_DIAGNOSTIC_READINESS_20261101.json)。LL实测仅id255的FF解码为空，全串255bytes、special实际255/256，源码预测确认；旧byte gate仍不通过。X尚未开始导入，Torch库发现准备打开os.devnull被过宽文件guard拒绝，本次约1.196秒异常而非5秒timeout，不能归因X性能。下一条修精确/dev/null与只读库查询准入并独立验收后再登记，不原地改旧run；45标签仍0。135runs3038主、4PID均退出，代码文档同步服务器，原始仅服务器。本条取代旧待办。

2026-11-01 最新：[前置失败源码审查](docs/LEGACY_BACKEND_SOURCE_AUDIT_20261101.md)完成。llguidance1.7.6源码保留FF作special标记，与原id255普通byte假设冲突，预测该id解码为空；尚未测得实际差值。X组合import具体慢点仍未知。已冻结保持原词表和原总5秒的最小差值／导入栈诊断草案，执行关闭、runner未实现；下一条实现并另登记，不直接运行45标签或绕过原gate。本轮只读源审0新实验，134runs3038主不变，原始只服务器，文档同步。本条取代旧待办。

2026-11-01 最新：[真实后端CPU前置检查失败](docs/runs/20261101-legacy-backend-cpu.md)，[readiness](docs/LEGACY_BACKEND_CPU_READINESS_20261101.json)优先。XGrammar组合导入触发5秒watchdog；llguidance导入成功但257词表byte roundtrip失败。两GIL控制通过，但全部schema/matcher/mask／45标签尚未执行，不把90个计划不可用格当测得错误。停止且不加时／改词表重试；下一条先只读审查固定源码的字节约定与导入分段，再另冻诊断登记。累计134runs3038主，失败工件保留、环境不改、已记录自有PID退出。原12项观测器通过保持，N1尚未定题。本条取代下方旧待办。

2026-11-01 最新：[12项观测器CPU验收](docs/runs/20261101-structured-observer-cpu.md)全部通过，[readiness](docs/STRUCTURED_OBSERVER_READINESS_20261101.json)优先。137原始事件／102外部进程样本独立复核，区分caller返回、work结束或reap、原线程槽probe、共享等待者与清理失败；只是合成标准库工程，不是实际编译器／资源损害实证。下一步另登记现有后端CPU导入／GIL／257合成词表和8schema45标签正确性，真实后端入口尚未实现。新增1CPUrun、0模型回答，累计133runs3038主，17自有PID均退出，无后台任务。原始只服务器，代码文档同步；N1未定题，旧KV停止队列保持。本条取代下方旧待办。

2026-10-31 最新：[结构化输出 CPU 协议与静态预检](docs/STRUCTURED_RESOURCE_CPU_PROTOCOL_20261031.md)完成，[readiness](docs/STRUCTURED_RESOURCE_CPU_READINESS_20261031.json)优先。公共8 schema／45标签及分阶段配置冻结。现有 XGrammar0.2.8无动态接口、llguidance1.7.6落后于原生取消版本，且vLLM依赖限制<1.8；当前无cgroup写权限／Rust工具链，不能用旧版代表强对照。下一步实现并登记12项标准库观测器验收，尚无runner或实验队列。N1仍待验证／未定题，原KV主线暂停；本轮0真实编译、mask、模型或新实验，132runs／3038主不变。来源与环境快照只服务器，代码文档同步。本条取代下方旧待办。

2026-10-31 当前决策：[新问题筛查](docs/NEW_PROBLEM_TRIAGE_20261031.md)完成。H3 停止，泛 KV 约束保持暂停作为论文主线，已有原型与结果保留。四条新线索中仅保留“结构化输出取消后的资源回收与正常请求干扰”作为有界可行性候选；需求有公开证据，但超时、可杀进程、原生预算与协作式取消均有近邻，尚未定题或建立新颖性。下一步冻结纯 CPU 可行性协议并核兼容性，无新实验／服务队列。本轮只读文献与源码，132 runs／3038 历史主回答不变，原始来源仅服务器；详见[readiness](docs/NEW_PROBLEM_READINESS_20261031.json)。本条取代下方旧待办。

2026-10-31最新：[H3固定12组筛查完成并停止当前候选](docs/H3_SCREEN_DECISION_20261031.md)，[主记录](docs/runs/20261031-decoder-h3-screen.md)/[readiness](docs/DECODER_H3_SCREEN_READINESS_20261031.json)优先。先[共同batch工程](docs/runs/20261031-common-batch-engineering.md)通过：2组Full+8候选18状态正反序36logits逐字节及KL精确重复、hook/nohook cache相同、实际mask/1008efficient/gather独立验证；这是新固定缓存流程，不救回原跨路径0.25/0.001 gate。随后原12DEV Full12/12通过≥10，8候选96+Full12共108向量全部完成。真实KV目标排序反转11/12已观察，但global/Top128/Top256/legal四目标所选均12/12保留Full正确决策，legal相对每基线0win/0loss/12tie，development_go=false。固定候选保真Snap10/recency8/六随机6/9/9/9/6/7，不能说裁剪完全无损；generic KL/TopK已选到正确缓存，无合法目标增益。独立stdlib复算384 KL/全部选择转移/Full支持/maps/masks/trace/4权重7metadata通过。当前H3停止，不扩题/seed/预算/模型/更难prompt救回，不以只排序不同承诺新颖性或毕业。原launcher real_KV_signal_observed=false为初始化未更新，semantic_closure明确真实反转true/实用go false，原manifest不改。工程worker1431879/validator1433053/launcher1431874与screen1450114/1451208/1450109全部exit0并核退出；GPU1收尾18MiB/0%。两阶段新增2GPUrun/144logits/172forward/13900输入token/28编码/0完整答案，累计132run3038主，新索引b0c4d8fd…；screen原164文件68140344bytes，加closure/derived166文件68159219bytes，原manifest256b9fd6…/derivedfbfa685d…全回读。系统原型/原48技术报告及旧QA/Mistral false/停止队列保持，代码配置文档同步服务器、原始仅服务器、GitHub未配置、当前无运行任务。本条取代旧H3筛查待办；新问题须独立需求和强近邻不足，不能改名重启。

2026-10-31最新：[真实SDPA现场观测v4完成](docs/runs/20261031-sdpa-observation.md)，[readiness](docs/SDPA_OBSERVATION_READINESS_20261031.json)/[修订](docs/SDPA_OBSERVATION_REVISIONS_20261031.md)优先。先CPU24通过及归档修复，再4个独立GPU观测run：v1取证晚于断言，v2确认CPU/GPU同名注记双计56/28，v3修device-type后遇Kineto单次导出限制，v4只导出一次完成；模型/输入/原observer wrapper/阈值/后端均不改，所有失败保留。实际2工程组/108forward/1082输入token/14末分布/10profile/2856SDPA：168显式bool mask+28 KV头走efficient，2688 None mask+4 KV头/GQA走Flash，全部is_causal=false。独立原event父链/Chrome marker/336 BF16tensor与gather/reference/trace/4权重7metadata复核通过；4对Full/recency plain-observed logits逐字节相同，函数恢复/ref不变。确认了真实分支差别，但未证明全部数值漂移成因；原数值gate仍false、mask值未采、H3与12DEV未跑。worker1422342内134.329954秒/verifier1423750内29.054636秒/launcher1422337总167.305701秒exit0，81文件256317526bytes/manifest13d41950…完整回读，cap检查先于complete。3旧失败各3forward/1向量；本轮总1CPU+4GPU（3failed），17工程向量/117forward/2345输入/16编码/0完整答案，累计130run3038主，新索引52861c0f…；旧索引/QA/Mistral false保持。全部自有PID退出，GPU1收尾18MiB/0%，无队列。下一条冻结共同batch-suffix运行契约及目标重复性标准，区别原整段/分段数值等价；不以换阈值或工程例最大误差救回旧gate，新Snap工程/Full12支持仍待验。代码配置文档同步服务器、原始仅服务器、GitHub未配置。本条取代下方GPU未实现历史待办。

2026-10-31最新：[SDPA透明记录器CPU验收完成](docs/runs/20261031-sdpa-observer-cpu.md)，[readiness](docs/SDPA_OBSERVER_READINESS_20261031.json)与[禁用现场草案](docs/SDPA_OBSERVATION_DRAFT_20261031.md)优先。参数原样转交/返回identity/原异常/嵌套与恢复冲突/marker-sink故障/日志cap及合成profiler父链等18用例，另6归档fault共24通过；独立重判合同及19fixture归档文件hash/count/bytes。新checked_archive先核递归文件和最终summary/manifest开销才写status，当前41文件100853bytes/cap64和4MiB，通过而不追改原44>40失败。worker1412961内0.061212秒/verifier1412963内0.017568秒/launcher1412958总0.284792秒exit0均核退出，guard全0。0真实Torch/SDPA/profiler/模型/GPU/编码/权重/网络/安装；新增1CPUrun，累计126run3038主，索引3da7a45b…，manifest478fb700…全回读。CPU只证stub合同，不证明真实CUDA数值/性能透明。原工程failed/H3未测/12DEV停止保持。新2工程组观测草案execution=false/runner=false，7路径×2含同路径Full/recency plain-observed精确对照，拟108forward/1082输入token/14归档分布/2856 SDPA事件；下条实现并冻结GPU观察worker/validator/运行时证据后才新登记，不自动GPU或切后端阈值。代码配置文档同步服务器、原始仅服务器、GitHub未配置、无自有运行任务。本条取代下方待办。

2026-10-31最新：[数值/源码离线审阅](docs/DECODER_NUMERICS_REVIEW_20261031.md)、[记录](docs/runs/20261031-decoder-numerics-audit.md)、[readiness](docs/DECODER_NUMERICS_READINESS_20261031.json)完成。精确安装HF源码+shape stub重放56调用（非真实Torch）：51None-mask/nativeGQA、5显式mask/repeat头，逐1287query按源码/记录参数可见集合相同；不是实际mask或CUDA kernel观测，尚未证明全部误差成因。4路径对/8概率scope独立复算，合法KL另Decimal60核验；Full/random概率差极小，recency global TV0.01673/allowed0.00042567，argmax稳定不等KL排序可信。原工程failed、0.25/0.001门槛/H3未测/12DEV停止均保持。worker1405845内1.692507秒/verifier1405867内1.498305秒exit0，但parent1405785在summary先写complete后发现44>40文件cap而exit1，整体记failed_archive_file_cap_analysis_verified；closure如实记录，不调上限/删工件/重跑。追加closure/derived后46文件4846935bytes，manifest a0dec76b…/derived75f431ab…回读。两官方PyTorch v2.5.1原文抓取成功；0新模型/GPU/编码/权重/安装，新增1CPU失败run，累计125run3038主，新索引43ddc7a0…，原工件不变。下一条先实现透明SDPA参数/实际后端记录器与CPU传参/恢复检查，修未来归档上限状态记录，再另冻2工程组有界现场观测；当前无第三GPU/12DEV启动或新后端阈值选择。代码配置文档同步服务器、原始仅服务器、GitHub未配置、三自有PID退出，无运行任务。本条取代下方待办。

2026-10-31最新：[同前缀KV工程两次失败](docs/runs/20261031-decoder-kv-engineering.md)，[readiness](docs/DECODER_KV_ENGINEERING_READINESS_20261031.json)优先。v1先hash权重后Torch临时目录run外写探测被拒，0forward/编码；v2仅固定run内TMPDIR/tempfile.tempdir，不放宽guard/输入/阈值。实际28Full/GQA4/BF16/SDPA与4权重7metadata、4工程编码核对；第一组56forward/1287输入token/7末token分布，缓存/gather/reference逐值与168tensor独立字节复算通过。但whole-full/split/recency/random路径max logits差0.5625/0.4375/0.5/0.5均>0.25，recency全KL0.002501>0.001，虽argmax集合相同仍工程false；完整validator未启动，事后独立标准库重算证实失败，不改分或阈值。第二工程组及全部12DEV模型调用0，H3未测试，不启动第三GPU。worker1398285/1399346与launcher1398280/1399341全退出，v1内21.708571/外22.371169秒、v2内23.757826/外24.478085秒exit1，GPU1收尾18MiB/0%。v1 fileguard1/v2违规全0，各拒绝1次精确IPv6 probe另计。归档v1 23文件360431bytes/v2 42文件47463000bytes，原manifest不改，后验derived与源码全保留。新增2失败run/4编码/0完整答案，累计124run3038主，新索引4dc414b3…；7工程logits不计新主答，旧48/索引/QA/Mistral false保持。下一条只离线审查已有数值误差质量、mask/位置与BF16可比标准，不能按结果放宽门槛救回或判方向no-go。代码配置文档同步服务器、原始仅服务器、GitHub未配置、当前无运行任务。本条取代下方GPU待办。

2026-10-31最新：[真实tokenizer与新输入CPU预检完成](docs/runs/20261031-decoder-native-preflight.md)，[readiness](docs/DECODER_NATIVE_READINESS_20261031.json)与[协议](docs/DECODER_NATIVE_CPU_PROTOCOL_20261031.md)优先。固定Qwen metadata/tokenizers0.22.1/Jinja3.1.4及新2工程+12开发组先冻结，登记d7d2edcd…只运行一次。34编码/6NFC与UTF-8 probes完成；独立标准库从151643 base词项穷举49语法边、排除22 added普通路径/399无词项model行，复核原生byte/14边界/事实gold及位置×标签平衡。首分支实际仅32–35即A/B/C/D；14组prefix373/suffix24、0跨界、半预算186/锚点68/free118全可行。布局57344bytes/槽仍是预测，native后端编码不等真实HF运行/gather通过。worker1392627内0.915734秒/verifier1392628内3.262950秒/launcher1392624总4.396328秒exit0均核退出，guard全0。归档28文件342048bytes/manifest798a6809…全回读，新增1CPUrun/34编码/0回答权重GPU安装，累计122run3038主，新索引34c0b953…，旧索引及原48评分不改。受控合成诊断不称独立自然基准；Full能力/H3失配/新颖性未知。下一条实现并冻结新2工程组同前缀真实KV协议/模型runtime权重pin、Full与gather/位置/数值标准、seed/资源上限，通过再固定12组Full支持与有界logit筛查；本次GPU入口未实现/未启用，不从旧草案自动执行。旧QA/Mistral false及旧停止队列保持，代码配置文档同步服务器、原始仅服务器、GitHub未配置、无自有运行任务。本条取代下方待办。

2026-10-31最新：[局部解码目标CPU验收完成](docs/runs/20261031-decoder-objective-cpu.md)，[readiness](docs/DECODER_OBJECTIVE_CPU_READINESS_20261031.json)记录实际结果。用户通知SSH恢复后现场核远端AGENTS、原索引与run未存在，CAS同步17文件及4Python编译通过；按原847651a5…登记只执行一次，源码/协议未改。18/18用例、23坏输入拒绝通过，独立80位Decimal重算7候选分布及全部目标/40条有限字节语法边/路径与8候选索引预算。worker1389088内0.133624秒、verifier1389089内0.702380秒、launcher1389085总0.985419秒均exit0并核退出，guard全0。归档21文件239223bytes，manifest f9a304f6…全部回读。新增1CPUrun/0模型答案/编码/权重/GPU/安装，累计121run3038主，新索引3c7cdede…；旧f3e6a039…索引和原48结果不改。有限byte语法不等native tokenizer，索引预算不等实际GPU gather，H3真实失配/新颖性仍未建立。下一条先冻结真实tokenizer-byte适配/schema与12新开发组CPU来源/native边界预算协议，再另冻同前缀query+wrapper重算和真实KV工程/GPU上限；不重跑已过CPU、不直接执行禁用108向量草案。旧QA/Mistral false、旧停止队列保持。前轮5次握手失败是0run历史，本轮阻塞已解除。代码配置文档同步服务器，原始仅服务器，GitHub未配置，当前无自有运行任务。本条取代下方历史断点。

2026-10-31当前断点：[CPU正确性实现](docs/DECODER_OBJECTIVE_CPU_PROTOCOL_20261031.md)、[readiness](docs/DECODER_OBJECTIVE_CPU_READINESS_20261031.json)和[记录](docs/runs/20261031-decoder-objective-cpu.md)已写本地。四脚本覆盖有限byte语法/稳定support KL/Full-Top128/256/等预算索引、18组用例与23坏输入、独立80位Decimal/穷举图核验及同步watchdog。**尚未运行或验收通过，新增文件未同步服务器。** 5次SSH均认证前断开，verbose确认TCP建立后KEX前关闭，不诊断密钥或具体原因；未修改VPN/服务/host key。先恢复连接、读远端AGENTS/当前索引/旧进程、CAS同步冻结文件和核源输入SHA/run未存在，再执行唯一新CPU登记847651a5…；失败保留、修订另起v2。原GPU草案禁用不改，真实tokenizer适配/物理KV gather/H3失配/新颖性均未验证；CPU通过后再冻结新12开发组同前缀诊断，不自动GPU。0新run/模型答案/分词/权重/GPU/安装；120run3038主和旧索引是上轮记录，本轮未现场复核。原48不改分，旧QA/Mistral false与旧停止队列保持。本轮没有启动远端任务，远端当前进程不可查询；GitHub未配置。此条取代下方待办及“已同步”旧表述。

2026-10-31当前进展：[研究问题重定](docs/RESEARCH_QUESTION_REDEFINITION_20261031.md)与[有界草案](docs/DECODER_OBJECTIVE_SCREEN_DRAFT_20261031.md)完成。H1格式修复与H2泛parser-aware KV不作主创新；仅保留H3待筛查假设：同一生成前缀下，全词表/通用Top-K KL是否会给等预算真实KV候选排出与局部合法token目标不同、且损伤合法语义决策的顺序。三token构造反例及标准KL分解已独立复核，但不是真实KV证据；尚无新颖性或可发表/毕业结论。下一步先实现CPU有限语法/稳定KL/候选掩码正确性入口并独立核验，再另冻12个新开发组的query-known同前缀logit诊断。108向量草案未实现/未执行，不是108独立回答；禁止复用Full suffix KV、原48调参或把局部mask当全序列条件分布。含Top128/256及直接masked-KL组合对照，无信号即停，不扩seed/预算救回。原文与算术证据仅服务器literature/20261031-decoder-aware-candidate-v1，10文件2266407bytes，manifest ea36b38a02db149812649eace16c321e92786a7da17fb4eaa00f086e717f2963。0新实验/forward/回答/分词/权重/GPU；累计120run3038主及f3e6a039…索引、原GPU194与分类20工件不改。旧QA/Mistral false及旧16/保护/3/4/BoolQ停止保持。代码配置文档同步服务器，GitHub未配置，当前无运行任务。本条取代历史待办，既有实测与查重结论保持；H3仅列研究假设，不计已建立科学贡献。

2026-10-31最新（审阅始于10-30）：[近邻贡献审查](docs/CONTRIBUTION_AUDIT_20261030.md)、[范围决策](docs/CONTRIBUTION_SCOPE_DECISION_20261030.md)、[审阅记录](docs/reviews/20261030-contribution-audit.md)与[readiness](docs/CONTRIBUTION_AUDIT_READINESS_20261030.json)完成。重读六项主近邻及TensorRT官方工程指南，固定5仓库/33文件+6论文官方页面，39源/24作者Python仅AST；4HEAD仍是此前固定版本，LYR沿作者直链commit。Pitfalls已有指令退化；KVDiagnosis已有全量Full配对/四转移/N/A/版本发布检查及真实适配来源审计；kvpress有context/question拆分和cache不变测试；质量/性能联合基准及LYR先导已覆盖资源核算、格式/内容/截断混淆。Risk-Controlled代码未定位保持未知，不据缺页断言无代码；LYR未同行评审、KVD未来会议页眉不当录用证据。本轮判断：保留已验原型和48组受限结果，尚未建立独立新方法/新基准贡献；通用账本/双指标/配对/预算检查不能当首创，六章可组织不等论文贡献闭合。系统/实证硕士候选保留，具体贡献仍待重定，不能代判毕业认可。暂不追加同类退化GPU实验，下一步先明确可证伪的问题缺口和最接近实现的实证增益，不据错题调prompt/样本/预算。来源原文源码只服务器literature/20261030-closest-work-audit-v1，51文件2924027bytes，Git blob/SHA核验通过，作者代码/测试未执行；部分web缓存失败改读同官方API，39源请求+9元数据成功，无模型/数据集下载。只读文献审阅不新增实验，累计120run3038主/f3e6a039…索引与原GPU/分类工件不变；0新模型回答/分词/权重/GPU/依赖/服务，旧自有PID退出。旧QA/Mistral false、旧16/保护/3/4/BoolQ停止保持。代码配置文档同步服务器，GitHub未配置，当前无运行任务。本条取代下方历史待办，原实测结果不撤销。

2026-10-30最新：[既有138答离线错误分型完成](docs/runs/20261030-squad48-error-taxonomy.md)，[分析](docs/SQUAD48_ERROR_ANALYSIS_20261030.md)、[readiness](docs/SQUAD48_ERROR_READINESS_20261030.json)与[论文章节证据映射](docs/THESIS_EVIDENCE_MAP_20261030.md)优先。分类在看到原GPU汇总后制定，明确探索性，原评分/主要差值/CI与194个GPU工件不变。全部144格/48组保留：Full31联合成功+3仅EM+13仅格式+1两项失败；Snap3仅EM+39两项失败+3截断+3预算不足；随机9仅EM+5仅格式+27两项失败+3任务N/A+1截断+3预算不足。原Full联合成功31组中，Snap3仅格式损坏/25两项失败/1截断/2预算不足；随机7仅格式损坏/2仅EM不匹配/17两项失败/2任务N/A/1截断/2预算不足。随机9个task-only里2个在Full已是task-only，不能全称新增格式损坏。已完成格式失败Full4plain/Snap42plain/random32plain+3JSON字符串+2结构解析+1object额外key或空answer+1缺string answer。9软件边界与独立138文本重评分/144分类/全48流转/31切片/26个确定性说明示例核验通过；示例完整文本只服务器，不当新样本/调参材料，EM/F1不充人工语义标注。worker1063574内0.065141秒/verifier1063575内0.038397秒/launcher1063571总0.281935秒exit0均退出，guard全0；本轮1CPUrun/0新回答/编码/权重/GPU/网络/依赖变化。归档20文件242447bytes，累计120run3038主，索引f3e6a039…，重分析不重复计答案。六章草案已按需求—实现—验收—48组实证—边界组织；下一步核对最接近工作原文/公开实现与具体系统差异，未建立差异前不称创新或毕业保证，不追加GPU/错题调参。旧QA/Mistral false及旧16/保护/3/4/BoolQ停止保持，原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。本条取代下方历史待办。

2026-10-30最新：[原48组GPU实证完成](docs/runs/20261030-squad48-gpu-study.md)，[readiness](docs/SQUAD48_GPU_READINESS_20261030.json)与[研究边界](docs/SQUAD48_EVIDENCE_CONCLUSION_20261030.md)优先。新独立study角色/输出adapter先过16软件用例，现场14工程答验证Full三路径/压缩双路径；旧HF角色限制不改、旧证据不注入。Qwen实际28Full/GQA4/BF16/SDPA/57344bytes槽，4权重6metadata加载前及独立复核SHA，50完整输入重编码相同。Full48任务34/48、格式44/48、joint31/48、错误/截断0，预定支持线通过，随后90可行压缩回答完成。Snap任务3/42、格式0/42、joint0/48、3截断；随机任务9/41、格式5/44、joint0/48、1截断和3候选N/A；两条件各3预算不足，全部48组/144格保留。两个all48 joint差均-31/48=-64.58pp，10000配对共享组抽样/seed20261030/type7逐项95%CI[-77.08,-50.00]pp；相同区间源于相同Full与全0 joint向量，不是独立复现。任务和格式同时受损，不称安全特异或新发现。独立138文本、4622trace步、94文件10528layer-head map、全部分母/主要统计及source/weights核验通过；原manifest不改、后验194文件5567444bytes。worker1052050内126.485009秒/verifier1053387内18.168072秒/launcher1052047总145.824922秒均exit0并退出；GPU1收尾15MiB/0%，Torch dtype弃用警告保留。新增1GPUrun/138主14工程/4664tokens，累计119run3038主，新索引d1c405bd…。单模型/任务/半预算/seed的独立于DEV描述性证据已补齐，原跨任务/第二模型确认、保护收益和纯推理成本未完成；精确文章去重不证明语义/预训练独立。下一步离线分型已有138答并组织系统/实证章节，不再重复证明一般裁剪有害、不据错误调prompt/换题/增预算，也不自动扩保护/3/4/BoolQ/Mistral/旧16。旧QA/Mistral false保持，无下载/依赖变化/服务。原始仅服务器，代码配置文档同步，GitHub未配置，当前无运行任务。本条取代下方历史待办。

2026-10-30最新：[组级统计CPU软件验收完成](docs/runs/20261030-group-statistics-acceptance.md)，[readiness](docs/GROUP_STATISTICS_READINESS_20261030.json)记录实际执行。新增独立统计模块、runner与stdlib validator，固定18/18用例通过，13次非法输入按合同拒绝；独立重算11份完整合成报告的全部计数/配对转移/差值、10000共享组抽样流和Fraction有理type7区间。G02只有4次精确枚举，区间[-0.925,0.925]是软件用例。原提案b1e9d042…false历史不追改，实际登记a50b8d68…与源码/协议先冻结同步。原48组/144格全部not_run、真实指标null、模型效应/CI为0份；Full48预算可行、Snap/随机各45可行+3不足，全部组和6阻塞格保留。仅规范化统计schema与pending计划adapter已验，旧scalar core/runtime/角色/证据规则未改，真实GPU输出adapter和新角色接入尚未实现。4输入257350bytes/原manifest13项及后验18文件216564bytes完整回读；guard全0。worker1036427内0.659025秒、verifier1036428内0.416647秒、launcher1036424共1.183390秒exit0均退出。本轮1CPUrun、0回答/编码/权重/GPU/网络/依赖变化；累计118run2900主，索引1e9b651d…。下一步实施并冻结GPU阶段输入/role/runtime与同cohort工程证据和输出adapter正确性检查，原2工程题最多14工程答；Full48先行，输出前草案任务≥24/格式≥36/错误0/截断≤4，失败停压缩，通过才最多90个可行压缩主答，总主答≤138、报告144格不减。以上GPU为待实施阶段，本轮未启动；旧QA/Mistral false、保护/3/4/BoolQ/旧16停止保持。代码配置文档同步服务器，原始仅服务器，GitHub未配置，当前无运行任务。本条取代下方历史待办。

2026-10-30最新：[原48题Qwen原生前端/半预算CPU检查完成](docs/runs/20261030-squad48-native-preflight.md)，[readiness](docs/SQUAD48_NATIVE_READINESS_20261030.json)记录实际结果。原48题ID/顺序/prompt/gold/文章组保持；48个完整native输入各两次编码，共96编码，独立stdlib复核通过。Full48格数学可行，半预算Snap与随机各45格可行、3格不可行：3道原题的半预算容不下固定sink4/recent64的68锚点槽，全部48组/144计划格仍保留，不换题/补齐/减少锚点。共138格数学可行、6格预算不足；所有执行状态仍not_run、指标null、当前cohort工程及Full支持未验证，不把CPU false解释为测得Full失败。prefix94–472/header56/query suffix10–34，57344 bytes/槽只是布局预测，header未作为保护收费。本轮1CPU run/96编码/0模型答案/权重/GPU/外联网请求，精确urllib3回环能力bind已拒绝且单列1次；内2.926653秒/外3.121825秒exit0，PID1026473/1026470均退出。原提案15dfe0e7…false历史不追改，实际snapshot与全部输入/22文件1926244bytes/manifest及独立回读保留。累计117run2900主，新索引724817ec…；旧QA/Mistral支持false及旧停止队列保持。下一步[组级统计CPU验收提案](configs/group-statistics-acceptance-v1.json)b1e9d042…已禁用冻结，18软件用例/10000共享组配对bootstrap/seed20261030/type7逐项95%区间，模块与runner尚未实现/执行；不能对当前planned清单计算实际效应。统计验收后另冻GPU角色/runtime/工程证据和Full支持协议，才可能生成最多138个主要回答；原144天花板与14工程资源预留不是自动启动许可。当前无运行任务，原始结果仅服务器，代码配置文档同步，GitHub未配置。本条取代下方历史段落的待办。

2026-10-30：[48组来源与分组冻结完成](docs/runs/20261030-squad48-source-freeze.md)。独立BFS复核442组件/87599原gold span，原48预留ID/顺序/prompt/答案不变，与工程/DEV及历史文章精确去重通过。已生成144格planned清单，0模型/分词/GPU，累计116run2900主。下一步Qwen48原生前端与半预算CPU检查，提案已禁用冻结、runner待实现；当前没有推理队列，代码文档同步服务器。

2026-10-30：[研究范围收敛](docs/MINIMUM_EVIDENCE_SCOPE_20261030.md)：保留系统/实证主线，下一独立验证限定Qwen＋SQuAD原48预留文章组，Full/半预算Snap/随机最多144主回答；先CPU重建来源与分组、冻结144planned格，提案禁用且runner未实现。本轮0推理/新run，Mistral原适配停止，保护与3/4不入最小主矩阵，不承诺新算法或跨模型普遍性。累计115run2900主，当前无GPU队列，文档提案同步服务器。

2026-10-30：[Mistral Full-only验证完成](docs/runs/20261030-mistral-squad-full.md)。6工程三路径一致，12DEV任务7/12、格式8/12、joint6/12；格式未达冻结9/12门槛，Full_support=false，停止此适配压缩/保护/封存。独立判分/KV/trace/权重复核通过，无截断/运行异常。新增12主6工程，累计115run2900主；下一步离线收敛支持边界与最小独立证据，不做提示/模型搜索，当前无GPU队列，代码文档同步服务器。

2026-10-30：[两模型CPU预检及独立复核完成](docs/runs/20261030-independent-frontends-preflight.md)。4工程+12DEV，Qwen/Mistral原生边界和完整保护均核验；完整保护DEV半预算可行2/12、3/12，3/4两模型均12/12，仅数学预算结论。v1本地能力探测guard分类失败保留，v2仍拒绝该bind并单列；两run0权重/GPU/模型回答，累计114run2888主。下一步Mistral Full-only≤6工程+12DEV的新协议，尚不运行compact/封存；代码文档同步，当前无运行任务。

2026-10-30：[独立实证方案与验收矩阵已收敛](docs/INDEPENDENT_EVIDENCE_PLAN_20261030.md)。停止重复现有12DEV，下一步先实现两模型CPU原生模板/保护边界/1/2与3/4预算预检，固定4工程+12DEV、0封存，上限96编码/128预算评估；提案仍禁用且runner未实现。Mistral元数据已核，当前任务/压缩未验；BoolQ新HF分发缺标题，不能直接替换原去重设计。本轮0新run/推理，累计112run2888主不变，当前无GPU队列，文档配置同步服务器。

2026-10-30：[HF系统DEV端到端验收通过](docs/runs/20261030-hf-DEV-acceptance.md)。工程检查点恢复→60格准入→36真实回答→任务/格式双判分→完整60格报告已打通，20预算不足/4保护未验保留，0封存。v1配置序列化误报0生成失败保留，v2仅修整份config JSON比较；独立判分和分母/trace/map复核一致。新增2run/36主，累计112run2888主；这是既有12DEV回归，不增加独立实证。下一步整理系统验收与独立实证缺口，停止重复当前小集，代码文档同步服务器。

2026-10-30：[新版HF后端GPU工程验证通过](docs/runs/20261030-hf-backend-engineering.md)。14工程回答605token，新旧token与路径一致；3可行条件已验，2保护条件仍预算不足未验，1Snap工程题截断只算数值路径验证。0DEV/封存，累计110run2852主，无运行任务。下一步冻结至多36准入DEV格的系统端到端验收，任务/格式分开归档；这不增加独立科学样本。代码配置文档同步服务器。

2026-10-30：[HF编排壳与延迟加载适配器已接线](docs/HF_ORCHESTRATION_20261030.md)，22项CPU流程检查通过，本轮未加载模型。新版拒绝复用旧工程证据，60DEV格中20预算不足、40等待新版工程验证；下一步仅14工程回答的GPU验证，0DEV/封存。新增1CPU run，累计109run2852主；代码接线通过不代表新GPU后端已验证。原始仅服务器，代码配置文档同步。

2026-10-30：[条件级准入接口已实现](docs/CONDITION_ADMISSION_20261030.md)，20软件检查与60历史计划格CPU验收通过。预算、同条件工程证据、未来准入和已有执行分别记录：36格可准入、20格预算不足、4格保护证据不足；历史4条保护诊断输出保留，不改旧分数/门槛。真实HF driver尚未接线，下一步新编排壳先dry-run，不重跑模型。新增1CPU/0模型回答，累计108run2852主，原始只服务器，代码配置文档同步。

2026-10-30：[新来源实证已运行](docs/runs/20261030-independent-development.md)。SQuADtrain87599题标注验证、BoolQ评分器20软件用例通过；BoolQ官方接口两次独立审查均403并保留失败。新12DEV Full答案9/12、格式11/12；半预算无保护策略退化，完整system保护有10/12题预算不可行，不能只报剩下2题的合规率。全部60计划cell与适用性由统一报告保存，保护工程路径未验证、跨任务确认未完成。新增40主/14工程，累计107run2852主；自有进程退出/GPU1 18MiB/0%，下一步接条件级准入/工程证据到系统。原始只服务器，源码配置文档已同步。

2026-10-30：[系统设计与实证工作已开始](docs/RELIABILITY_SYSTEM_DESIGN_20261030.md)。新增通用标量契约、KV布局/收费保护预算、两任务适配器及配对报告核心；服务器16软件验收全部通过，三cohort共290历史记录计数/转移/分母/F1与原报告一致，旧截断/未知成本保留。新增1CPU run/0模型回答，累计100run2812主。[独立实证方案](docs/RELIABILITY_EMPIRICAL_PLAN_20261030.md)拟新SQuADtrain+BoolQ，先来源/scorer/分组CPU检查再12题新DEV；旧QA gate与封存不恢复，当前无新GPU运行。源码配置文档同步服务器，原始只服务器，GitHub未配置。

2026-10-30：[已完成方向可行性判断](docs/ANSWER_FORMAT_FEASIBILITY_20261030.md)。建议保留KV输出约束可靠性的系统/实证型硕士路线，当前16题阅读+JSON不单独成完整论文，不称新算法或安全创新。Full12正确/16格式，半预算Snap/random/两保护为EM4/8/5/5、格式3/8/15/16；保护有格式收益也有任务损伤。随机1截断触发预定全局完整性停止线，未扩封存/预算/模型。四阶段工程和独立复核完成，新增80主/22工程、累计99run2812主；自有进程退出、GPU1 18MiB/0%，当前无运行队列。下一步先开题与系统验收设计，原始仅服务器，源码配置文档同步，GitHub未配置。

2026-10-30：[阅读+JSON任务CPU预检通过](docs/runs/20261030-answer-format-task-preflight.md)。新标准库数据/评分模块及runner完成，24评分+6数据用例全过；完整10570题/34726答案标注与原文一致，按48文章组件固定工程2/开发16/封存16。独立图+BFS及原始选择/prompt/hash复核通过。选中段落164–629词，尚未测模型token边界、KV预算或Full能力，不能称长上下文/安全结论；[readiness](docs/ANSWER_FORMAT_TASK_READINESS_20261030.json)区分已过/未测。新增1CPU run/0回答，累计95run2732主；下一步先冻CPU模板/tokenizer检查，再另冻Full-only最多22回答，不自动裁剪/访问留出。源码文档同步服务器，原始只服务器，GitHub未配置。

2026-10-30：[新任务数据与评分契约](docs/ANSWER_FORMAT_TASK_CONTRACT_20261030.md)已写好，采用SQuAD v1.1原段落问答+固定JSON输出，分开测答案EM/F1、格式遵守及评分覆盖，按文章组划分工程/开发/封存。来源/原评分副本已静态审查；数据尚未下载，24评分与6数据用例尚未执行，[CPU预检提案](configs/answer-format-task-preflight-proposal-v1.json)禁用且runner未实现。下一步先实现并验证数据与scorer，Full/压缩另冻，当前0新实验/回答，94run2732主保持。文档配置同步服务器，GitHub未配置。

2026-10-30：[CPU配对报告模块已实现并验证](docs/runs/20261030-reliability-report-replay.md)。只读9文件/242旧JSONL行，生成210个规范化记录；开发32/已用留出10各两口径计数一致，12软件边界fixture通过。v1后审查发现历史口径在方法失败时分母遗漏，保留原始并用v2修正/加强同一fixture，不改旧模型分数。新增2CPU run、0回答，累计94run2732主；无模型库/GPU/新环境。下一条先离线定义新任务的数据、判分、上下文划分与Full支持契约，不直接扩生成矩阵。源码/文档同步服务器，GitHub未配置。

2026-10-30：[系统需求与验收设计完成](docs/RELIABILITY_SYSTEM_REQUIREMENTS_20261030.md)。10份现有脚本已核SHA/入口与结果字段；可复用真实KV选择/gather及配对审计，但旧runner/报告硬编码题数、分母与模型形状，缺真实峰值/逐阶段时延。首个实现选纯标准库的独立结果adapter/报告，冻结旧32/10两cohort及12软件fixture的禁用CPU提案；新模块未实现/验证，本轮0新run/回答。下一条实现并按60秒上限验证只读报告，不生成模型或改旧工件。文档同步服务器，92run2732主保持。

2026-10-30：[一页选题收敛稿](docs/THESIS_CONVERGENCE_20261030.md)已形成。用户明确接受有具体问题的系统/实证研究，优先讨论“面向输出约束可靠性的Transformer KV缓存压缩评测系统设计与实证分析”：在相同实际KV预算下分开研究约束遵守、任务正确性及指令保护代价。现有实现和TREC个例仅作工程基础，不称新算法/漏洞或已完成论文；独立确认与第二模型未完成。下一条先离线盘点代码/字段并写系统需求与验收表，不重跑旧矩阵。0新run/回答，92run2732主保持，文档同步服务器。

2026-10-30：[取消记账门槛审查完成](docs/CANCELLATION_ACCOUNTING_GATE_20261030.md)。13份固定0.32源码与官方blob一致；取消未走正常完成统计有静态依据，但issue55634/未合并PR55940已直接覆盖。Retire及公开取消测量报告也覆盖泛取消尾部/断开传播；真实配额绕过仍缺部署契约与执行链，当前不立新论文主张或启GPU/服务。0新run/回答，沿92run2732主；下一条先一页选题收敛，不自动转第3项或另开矩阵。文档同步服务器，本轮未向GitHub写入。

2026-10-30：[默认图尺寸测量验证完成](docs/runs/20261030-controller-profile-validation.md)。两条工程回答逐token等于旧基准；110次原始profile计时、N1直接样本及原生成本曲线/整表exact复算通过。验证预算成本已不再全同价，但旧397向量代入新表的N1离线重放仍全部选4；不是新引擎实际预算或损害证据。当前固定配置筛查结束，暂不扩GPU；下一条只读审第2线索“取消后的资源记账”的具体契约/实现/近邻，尚未开始。累计92run2732主，本轮0主/2工程64tokens；自有进程退出、GPU1释放。代码/文档同步服务器，GitHub未配置。

2026-10-30：[成本profile离线审查](docs/CONTROLLER_COST_PROFILE_AUDIT_20261030.md)完成。工程图尺寸[5,10]将单请求验证预算1–5放入同桶，draft N1由N2测量补表；原始计时未留存，不能据此泛化成本或历史负结果。公开高熵标签也未证明本模型逐位置qmax可达敏感域。新增1CPU run、0回答，累计91run2732主；未查询/使用GPU。下一步仅实现禁用的两回答原始profile验证方案，尚未执行，不扩历史矩阵。文档/代码同步服务器，GitHub未配置。

2026-10-30：[自然历史30主请求筛查完成](docs/runs/20261030-controller-natural-history.md)。历史改变了共享系数/置信度，但六个同探针条件预算、accepted数和输出相同，未见可用性损害；N1成本平台导致分配饱和。解析失败和全部零效应保留，累计90run2732主输出。当前不扩GPU实验，下一步仅离线审成本/正常负载敏感域；原始服务器、文档同步，GitHub未配置。

2026-10-30：[真实worker工程v5通过](docs/runs/20261030-controller-worker-v5.md)：固定Triton环境中64项FullAttention cache spec、控制器原址恢复/跨refit重放/冻结更新通过。v3/v4失败保留，本轮0主+6工程答案，累计88run2702；尚无自然历史损害/攻击证据。下一条实现已冻结小筛查的观测钩子与透明性检查，不重复工程关卡。原始只服务器，文档同步，GitHub未配置。

2026-10-30：[配对模型已准备，worker初始化受阻](docs/runs/20261030-controller-worker.md)。0.6B固定权重与8B tokenizer一致；两次工程初始化分别遇到eager/full-graph冲突及FlashAttention2可变长度图限制，0模型回答/0恢复RPC。累计85run2702；下一条按已准备的固定Triton配置验证真实worker，不把工程失败当研究假设失败。原始只服务器，文档同步，GitHub未配置。

2026-10-30：[独立环境与原生估计器检查](docs/runs/20261030-controller-runtime.md)通过：vLLM0.32.0已在单独环境安装并锁定197包，原生GPU估计器/跨refit原址恢复通过。仍未加载配对模型或验证真实worker异步状态；下一条准备draft/tokenizer及有界worker工程协议。累计82run2702主输出，本轮0模型答案；以下旧状态以最新STATUS为准。

2026-10-30：[共享控制器CPU预检v2通过](docs/runs/20261030-controller-history-cpu-v2.md)，54/54、4503次合成更新，v1失败完整保留；只证明CPU参考，不是实际模型攻击或GPU恢复验证。只读环境核查确认旧venv不满足所审vLLM依赖，下一步准备独立环境、固定draft与可信worker状态接口；当前未安装/下载权重/加载模型。累计80run2702主要输出，原始只服务器，文档同步，GitHub未配置。

2026-10-30：[CPU预检v1失败记录](docs/runs/20261030-controller-history-cpu.md)。32通过、1失败、21未执行；我方要求每个合成案例共享斜率都移动的断言过强，独立复算确认源码负斜率防护解释，未否定或验证模型问题。修正版revision2已准备但未重跑，CPU完整恢复尚未通过；下一条只运行新目录的有界CPU复查。累计79run2702主要输出，无新模型答案/GPU/环境变化，原始结果仅服务器，代码配置文档同步，GitHub未配置。

2026-10-30用户选择先调查共享控制器：[状态生命周期与最小设计](docs/CONTROLLER_HISTORY_AUDIT_20261030.md)已完成。共享系数跨请求保留有源码依据，真实损害/创新未验证；TTA/APEX近邻及JIT预热混杂已记录。下一条仅实现禁用的CPU公式/状态预检，不加载模型，本轮0新run/答案/环境操作；来源与配置已同步服务器。旧KV/guard停止和A搁置保持，GitHub未配置。

2026-10-29：[投机交叉问题源码审查](docs/SPECULATIVE_DESIGN_GATE_20261029.md)完成。当前vLLM0.32.0已有接受率/成本感知自适应验证与逐请求统计，LAPS-SD等已有直接近邻；不把预算感知另立新方法。跨用户尾延迟残余问题尚未验证，当前不进模型实验，该单次审查队列结束。尚无确认论文选题，不自动换名或复活旧KV/guard队列；A仍搁置。0新输出/run，文档同步服务器，GitHub未配置，详见最新STATUS/HANDOFF。

2026-10-29：[选题收敛](docs/RESEARCH_CONVERGENCE_20261029.md)暂停当前KV裁剪安全新算法主线和重复安全曲线，保留平台/负结果；A搁置，D/E宽泛方法未过查重，旧guard工程失败保持。尚无已确认论文选题。只保留投机解码在相同token配额下的跨用户延迟干扰这一待证问题，下一次先审固定引擎和强基线，不启动模型或修改其他方向。本轮0新输出/run，未探测GPU；历史78run2702不重算，项目GitHub未配置。最新以STATUS/HANDOFF及收敛报告为准。

2026-10-28恢复检查后结论：[动作guard工程关卡未通过](docs/runs/20261028-action-guard-engineering-failure.md)。三次尝试新增0主要答案、6工程输出；修复版本计数与采样默认覆盖后，greedy整段/切分输入仍从第54 token分叉，缓存原生/custom一致。限定teacher forcing复现该差异，不放宽门槛，不自动再跑32题或压缩。累计78run2702主要输出，两卡已释放。A当前方法no-go，尚无可确定的新论文选题；[本轮结论](docs/RESEARCH_WINDOW_20261028.md)为准。下方加载前停止是历史断点。

2026-10-28本轮准确断点：[研究收尾](docs/RESEARCH_WINDOW_20261028.md)。平台usageLimited后停止加载前Full-only检查，0新答案，累计75run2702；StepGuard固定32例CPU/重叠与权重准备完成，能力未测。A当前方法归约no-go，C宽泛主张亦被覆盖。下一次只恢复同一冻结能力关卡，未执行压缩或提出已验证新方法。

2026-10-28启动审查：[候选A当前方法主张no-go](docs/PREFIX_RISK_DESIGN_GATE_20261028.md)，不执行历史256输出建议。LTT/Pareto已有多风险与成本选择框架；当前同一工作窗口继续只读审查真实KV证据充分性/拒答近邻和作者公开输出，无新模型答案。下方首选排序与旧下一步均为历史，最新以STATUS/HANDOFF为准。

选题调研：[待解决问题、文献差异与淘汰条件](docs/TOPIC_SURVEY_20261028.md)已整理。优先评估可复用前缀的按组约束风险与正常效用联合预算选择；尚未证明新颖性，不重做泛安全退化或自动扩大实验。本轮仅调研与文档维护，0新模型输出。

当前：[留出10题复查](docs/runs/20261028-trec-holdout.md)50主要输出＋24工程输出完成，Full7/10；Snap/随机/各自任务头保护正确7/6/7/7，格式10/9/10/10，0截断/error。独立审计通过；累计59run2702主要输出，工程重复单列。

[本轮TREC阶段结论](docs/TREC_CALIBRATION_CONCLUSION_20261028.md)：裁剪可损害精确标签格式，保护可恢复已观察非法标签，但不保证分类保持，尚无稳定方法优势/一般安全效应/新颖性证据。按冻结规则结束校准，不自动扩矩阵；下一步先离线收敛研究问题。以下旧进展中的待办为历史记录，当前状态以上文及STATUS/HANDOFF为准。

最新：[10题留出CPU冻结](docs/runs/20261028-trec-holdout-cpu.md)完成，原标签10/10来源匹配，全部未用合格题保留；示例仍大量共享，不是独立数据源。新复查提案禁用，下一步先10 Full过门槛后再40压缩，上限50主输出＋24校验，不扫预算。本轮0模型答案，累计58run2652主要输出。

最新：[TREC 50%裁剪128输出](docs/runs/20261028-trec-pruning.md)完成。Full19/32；Snap/随机/各自完整任务头保护分别17/17/16/19，格式31/30/32/32。3非法标签来自2个Full分类已错问题，pin后格式恢复但分类仍错；尚无Snap优于随机或安全特异证据。下一步只CPU设计剩余10个未用合格问题的留出复查，不继续扫预算。累计56run2652主要输出，另24工程输出单列。

最新：[TREC 50%裁剪CPU预检](docs/runs/20261028-trec-pruning-cpu.md)通过。32题完整任务头与共同锚点267位置全部可容纳，14,336层头索引、等字节/100%恒等/随机重放及独立复核完成。当前仍0新模型答案、准备配置禁用；下一步验证真实hook/Full重放/压缩解码，通过后才运行128裁剪校准。累计55run2524主要输出，尚无该裁剪矩阵结果或安全特异结论。

最新：[TREC有/无示例Full KV关卡](docs/runs/20261028-trec-context-full.md)完成，有示例19/32、无示例11/32，9题由对变错、1题改善，达到预先的描述性context门槛；64输出全格式合规。未做裁剪或建立安全效应。下一步仅CPU准备固定50%预算、适配SnapKV/随机与完整任务头保护的四条件校准；新提案禁用。累计54run2524主输出，另18校验输出单列。

最新：[TREC真实数据CPU预检](docs/runs/20261028-trec-data-preflight.md)完成并冻结32题。新能力提案准备比较有/无示例各32个Full KV输出，先检查原生/缓存三路径与上下文是否有用；当前尚未模型推理、execution_enabled=false，不做裁剪。原始数据只服务器，无新依赖/权重，累计53run2460旧输出。

最新来源审查：[SystemCheck与TREC](docs/runs/20261028-systemcheck-source-audit.md)。S-IFEval标准包装最长仍仅216token，无法接入原长前缀方案；且固定Pitfalls数据为539题，有删除/改编差异。下一步只CPU固定LongBench TREC原始数据、标签/前端/预算；其分类与防泄漏已有论文实验，不当新颖性。累计50run2460旧主输出，本轮0模型答案。

最新（2026-10-28）：[IFEval CPU长度预检](docs/runs/20261028-ifeval-cpu-preflight.md)触发预定停止条件，541题仅1题满足256–2048token，无法组成32题；原提案保持禁用，无新增模型输出。下一步先审长上下文约束任务来源与可行性，不通过填充/降阈值启动旧方案。STATUS/HANDOFF最新条目优先于下列历史进展。

研究按重要性删除 KV 位置后，正常任务所需约束是否被削弱，以及怎样在固定缓存预算下改善约束保持。

执行位置：`/home/user/jhk/project/Directional Exploration/kv-pruning`。本地仅代码/配置/文档，原始结果留服务器。用户已授权本会话实验；已完成首轮筛查、后续基线审计与等预算事实诊断，当前无实验运行。结果和失败见 STATUS 与 docs/runs，连接信息见上级 docs/SERVER_SETUP.md。

用户于 2026-10-26 明确：本方向独立研究普通 Transformer（各层为 Full Attention），不从旧 `nano-vllm` 项目复制代码或文件，不使用其 Qwen3.5 Hybrid 实现作为基线。已建立独立 Transformers 诊断脚本并完成首轮服务器预实验，原始数据只留服务器 `results/`。

目标是探索可形成小论文或毕业论文的研究闭环。仅证明“裁剪会削弱约束”或保护固定 system token 与已有工作重叠较大；当前候选切口是条件约束中的主体、对象、条件与权限关系在压缩后是否被破坏。该切口是讨论建议，尚未确认新颖性或正式定题。

当前诊断中，50% KV保护全部结构化事实即可48/48，等量随机位置为10/48；暂先用重要事实保留不足解释退化，不主张已发现安全特异机制或关系感知新算法。

最新多事实检查已配平prefix/suffix与KV字节；32行新世界Full KV权限/路由各23/24，各5/6世界四问全对，未达到预设门槛，停止裁剪效果比较。原生generate复查48问逐token相同。Expected Attention完成评分/缓存工程检查，尚无该设置下压缩准确率。

后续固定few-shot未改善，新世界和16行原模板仍未过Full门槛；lookup-only也在原对象上读错group而正确读出ID/payload。当前暂停连续修补这套合成权限模板，先审查标准单system前端、事实位置平衡与任务选择，未开始新的压缩效果矩阵。

最新已完成前端/位置审计：单system＋位置配平仍仅23/24、22/24；给定可信目标行的oracle诊断48/48，但提供额外事实/长度，不能作为实际基线。停止修旧模板，下一步将标准直接检索与权限决策分开验证；公开基准官方源码/许可已固定核查，尚未运行替代基准。

2026-10-28已完成分开验证：RULER legacy轻量检索控制32/32包含正确值（输出也复述查询编号，非数字独占精确匹配）；OrgAccess固定GitHub easy快照发现相同输入对应不同标准标签，暂停作为正确性门槛，其32题16条标签一致不能称正确率。下一步审AccessDenied的显式权限与gold生成；仍无新裁剪安全效应结论。

AccessDenied受控配对改编已完成Full检查：本人8/8、无权同事0/8（8条最终答案均输出目标薪资）、目标缺失0/8（均误用拒绝短句）。身份/标签/原生前端与三生成路径已核验；当前7B/固定模板组合未过门槛，未跑裁剪。下一步固定另一纯Full Attention候选模型复查同24条发展集，再用独立上下文确认，停止继续修当前提示。

接手顺序：[AGENTS](AGENTS.md) → [状态](docs/STATUS.md) → [交接](docs/HANDOFF.md)。

最新已完成[研究收敛](docs/RESEARCH_RESET_20261028.md)：旧证据不足以支持安全特异绑定损坏，KVDiagnosis等又已覆盖通用失败诊断；暂停AccessDenied模型/提示搜索与新算法开发。只保留一个最多32题/160输出的标准测量校准提案，先CPU冻结官方数据/ID/严格判分器与预算，当前配置锁定不执行；它不是论文创新。本轮只有旧输出重算/固定源码静态核查，0新模型答案。

最新Mistral原版Full已完成：权重13文件14.50GB完整校验、291BF16 tensor/32Full层和首三类缓存三路径通过；本人8/8、同事0/8、缺失2/8，8次同事最终块披露，缺失另4次禁用值。3配置/2族在此发展适配均未过门槛，暂停该模板继续模型/提示搜索及压缩，先离线收敛任务与研究问题。确认集仍未推理，不把Full失败称KV压缩效应。见[本轮记录](docs/runs/20261028-mistral-full.md)。

最新独立族候选已固定Mistral-7B-Instruct-v0.3 c170c708：32层Full Attention的meta结构与原生前端核查完成，10metadata/48条分词及oracle检查通过；尚未下载完整权重或生成答案。其system-only模板只返回<s>，缓存前缀须从完整native token串切分，不能照搬Qwen。仅venv补sentencepiece0.2.1，失败/修复全记录。下一步按固定摘要下载权重，再原版24发展任务Full；不改提示，过门槛才确认。见[候选记录](docs/runs/20261028-mistral-candidate.md)。

最新输出指令审计：旧版24输出逐token复现；保留旧policy和examples、仅改4处输出要求后，Full本人8/8、同事0/8、缺失0/8。同事6次最终块越权薪资、2次主体本人薪资错答，缺失另1次越权；缓存路径检查通过。输入+14、资料位置+20tokens，不能推断解释的单独机制。停止该模板提示搜索/裁剪，下一步先核查独立模型族固定候选；未运行确认集。见[本轮记录](docs/runs/20261028-delivery-factor.md)。

最新答案契约检查：冻结一版缺失优先＋只输出答案的联合适配，保留原资料/身份/问题/gold，Full本人8/8、同事0/8（8次最终块披露）、缺失6/8，仍失败；确认与裁剪未运行。变化同时涉及政策/示例/长度/输出要求，不能只归因于不输出解释。下一步先做有限因素设计审计，停止继续精简提示到过线。见[本轮记录](docs/runs/20261028-answer-contract.md)。

最新2026-10-28：Qwen3-8B固定权重已校验，原24条Full复查本人8/8、同事最终块拒绝8/8但全文严格7/8、缺失3/8。模型能力在发展集改善，仍未过预定门槛；确认集与裁剪未运行。1次薪资仅出现在块外解释，而源prompt明确要求这类解释、原应用只交付brace块，不能混称最终交付泄漏。先固定任务与应用交付边界，详见[本轮记录](docs/runs/20261028-qwen3-access.md)。

- [研究计划](docs/PLAN.md)
- [文献与查重](docs/LITERATURE.md)
- [第二轮查重与静态核查](docs/NOVELTY_REVIEW.md)
- [待执行验证协议](docs/VALIDATION_PROTOCOL.md)
- [过程日志](docs/WORKLOG.md)
- [首轮预实验与失败记录](docs/runs/20261027-pilot.md)
- [后续基线审计与等预算事实诊断](docs/runs/20261027-baseline-audit.md)
- [多事实规模、query-blind评分检查与停止记录](docs/runs/20261027-scale-queryblind.md)
- [查组稳定性、lookup-only与16行检查](docs/runs/20261027-lookup-stability.md)
- [前端/事实位置审计与公开基准源码核查](docs/runs/20261027-frontend-audit.md)
- [分开的检索控制与公开权限标签审查](docs/runs/20261028-benchmark-baselines.md)
- [AccessDenied显式身份配对Full检查](docs/runs/20261028-accessdenied-pilot.md)
- [Qwen3固定模型Full复查与块外交付区分](docs/runs/20261028-qwen3-access.md)
- [明确答案契约的单版本Full检查](docs/runs/20261028-answer-contract.md)
- [保留政策与示例的输出指令编辑审计](docs/runs/20261028-delivery-factor.md)
- [独立Mistral模型族候选与原生前端核查](docs/runs/20261028-mistral-candidate.md)
- [Mistral完整权重与原版Full基线](docs/runs/20261028-mistral-full.md)
- [研究收敛与下一关测量校准](docs/RESEARCH_RESET_20261028.md)
- [CPU证据重算与固定源码审计](docs/runs/20261028-research-reset.md)

公共背景和实验记录模板位于上级 `docs/`。实际代码、配置与结果在开展实验时创建，不能以文档初始化代替复现。


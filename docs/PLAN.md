# 研究计划：裁剪后的约束保持

2026-11-04 当前决策：**搁置 N1 结构化输出资源生命周期分支，关闭默认后续实施。** 用户认为当前结构化方向不好做；讨论确认真实 vLLM 服务中的资源损害、结构化特有问题及现有机制不足均未建立。单线程池排队不能当作调度缺陷或安全证据。详见 [搁置决定](STRUCTURED_OUTPUT_STOP_DECISION_20261104.md) / [当前分支状态](STRUCTURED_OUTPUT_BRANCH_STATE_20261104.json)。不实施或执行旧自然观测草案，不开展取消/压力对照；旧草案、readiness、结果原样保留，下方所有“下一条实施”均为已被覆盖的历史记录。147runs/3038历史主回答不变，H3停止/泛KV暂停保持；后续先重新明确候选问题，不自动恢复旧实验。本轮仅文档维护，未启动实验或后台任务，未重新审计既有进程。


2026-11-02：[资源观测尺度审阅](RESOURCE_OBSERVABILITY_REVIEW_20261102.md)完成。旧694调用小于0.45ms，10ms外部观测无法单调用计费；强对照源码能力不等本机可运行。冻结configs/resource-observability-natural-draft-v1.json（a1c47d2c…），下一条实施自然执行观测器并另登记18工作+1空控制，同池单槽/高分辨率clock/固定width1,2,4，无取消或人为拖慢。未重叠保留unobserved，不扩输入救信号；科学资源/取消对照仍须公平可运行强基线。0新native/run，147runs3038主，N1未立题。本段取代旧待办。

2026-11-02：[明确类型记录族检查](runs/20261102-typed-object.md)完成，两后端各21/21，独立业务oracle通过；当前是已见旧结果后的开发性新协议，未筛旧28格。下一条冻结有界资源可观测性/同槽正常探针小筛查及强对照兼容性；规模、指标、预算和停止条件先固定。旧45题失败和旧gate不改，不重做12/8/23/425，不据正确性或旧版缺API宣称资源问题/新颖性。147runs3038主，4PID退出，无新实验队列，N1未定题。本段取代旧待办。

2026-11-02：[原8组45实例语义检查](runs/20261101-finite-semantic.md)完成但gate false；X31/45，LL39/45+4 unknown，工程验收通过不等语义一致。当前负载不能直接支撑等语义资源回收对照。下一条仅定义独立的共同支持明确类型schema族及事前正负例协议；不从已测28个共同正确项筛集、不改旧题/标签/序列化或启近似救gate。资源/取消/性能阶段关闭，无native队列；146runs3038主、4PID退出，旧false gate/H3停止/N1未定题保持。本段取代旧待办。

2026-11-01 最新：[有限UTF8域/构造检查](runs/20261101-utf8-domain-factory.md)完成。新有限UTF8域的适配/无schema构造预检通过：133普通字符逐项/整串往返、8正例、7负例、EOS元数据及425调用独立验收均通过；X编译器构造完成，LL仅Tokenizer构造，schema/LLMatcher仍留后续。45原文本全可表达而语义执行0，不救旧257byte/FF或cold5 gate。下一条独立冻结原8schema45标签在新134词表上的全样本正确性，显式EOS、错误/unsupported/超时保留，mask按134重算；LL schema转换/matcher不得预热隐藏，检查预算不冒称端到端请求5秒。通过前不启动资源干扰/取消/性能或模型。不重做8/23/12，1新CPUrun、145runs3038主、4自有PID全退出，N1未定题。本段取代旧待办。

2026-11-01 最新：[崩溃定位与完整启动](runs/20261101-startup-fault-probe.md)完成。GDB单对未复现旧SIGSEGV，根因未知；封装v1和v2身份判读失败均保留，v2实际两Torch完成由独立离线v3证明。另登记完整fatal-only导入从父spawn7.802948秒通过Torch/XGrammar/CUDA false与独立账本，只有library-ready、退出失效。下一条冻结共同合法UTF8域（bytes/字符串/special/EOS）及同进程factory正确性小协议；不删FF救原257 gate，不直接执行45标签/取消/性能，不重做8/23/12。3新CPUrun、144runs3038主，23自有PID全退出，旧cold5/FF/语义gate false，N1未定题。本段取代旧待办。

2026-11-01 最新：[分阶段合同验收与启动记录](runs/20261101-phase-contract.md)完成。8项标准库状态/时钟验收通过，随后新登记import-only启动在Torch导入阶段SIGSEGV/-11，未达library_import_ready，非30秒截止。下一条先只读对照此次崩溃与诊断机制，再冻结有界定位方案；不自动重试、重做已有8/23/12验收或构造schema/vocab/compiler。旧cold5/FF/语义gate false、45标签未跑，未来request5秒仅已实现合成合同，无真实后端实证。2新CPUrun（1失败），141runs3038主，全部自有PID退出，N1未定题。本段取代旧待办。

2026-11-01 最新：[启动/请求范围审阅](STARTUP_REQUEST_SCOPE_REVIEW_20261101.md)与[禁用契约](../configs/startup-request-contract-draft-v1.json)冻结。下一条实现并另登记8项标准库状态/时钟验收；通过后才另登记import-only新启动30秒/总45秒，不构造schema或词表。未来请求5秒端到端包含前置验证/排队/编译/first-mask；原冷启动5秒与FF gate不救回，imports_ready不代表factory/domain_ready。0新实验，139runs3038主，45标签和native队列关闭，N1未定题。本段取代旧待办。

2026-11-01 最新：[导入边界验收](runs/20261101-import-boundary.md)完成：v2软件23项通过，实际已越过原误拦并进入XGrammar依赖链，但组合5秒冷启动仍删失、gate false。下一条仅离线核服务初始化与每请求语法工作的预算边界，不继续native、提高旧5秒或据冷启动判研究成败；分阶段执行若采用须另冻新范围和独立启动资源上限。原FF gate false/45标签未执行，139runs3038主，N1未定题，无运行队列。本段取代旧待办。

2026-11-01 最新：[最小诊断完成](runs/20261101-backend-diagnostic.md)：LL原FF冲突实测确认、X仍未开始导入，Torch库发现被自建文件guard误拦。下一条精确修/dev/null与固定只读动态库查询准入，先独立软件验收、再新登记总5秒CPU导入；不重跑差值、放开任意子进程、加时或删FF。45标签未执行，旧语义gate false，135runs3038主，无运行队列。本段取代旧待办。

2026-11-01 最新：[前置失败源码审查](LEGACY_BACKEND_SOURCE_AUDIT_20261101.md)完成，FF special标记能解释原byte假设冲突，实际差值未测；X具体超时点未知。下一条实施并另登记[禁用最小诊断草案](../configs/legacy-backend-diagnostic-draft-v1.json)，保持原257词和组合总5秒，仅取字节差值与import栈，不编译/运行45标签。不能删FF、用内置byte262替换或提高时限救回。0新实验、134runs3038主不变，N1未定题，无队列。本段取代旧待办。

2026-11-01 最新：[真实后端CPU前置检查](runs/20261101-legacy-backend-cpu.md)失败并停止。X组合导入触发5秒上限，LL合成byte roundtrip失败；45标签全未执行，不当语义结果。下一步先只读审固定字节／special-token约定和import链，再另冻诊断；禁止原run自动重试／增加时限／换词表或schema救回。GIL控制和原12observer通过保持，不代表真实语法GIL/服务隔离已验。134runs3038主、无新运行队列，N1仍未定题。本段取代下方待办。

2026-11-01 最新：[12项观测器CPU工程](runs/20261101-structured-observer-cpu.md)及独立原事件复核完成，不重复该阶段。下一条实现并登记现有后端CPU导入/GIL/257byte词表/8schema45标签正确性，沿既定源与输入、失败不换题；真实后端入口未实现，不自动起服务或扩强对照。合成工程通过不等真实资源损害或新颖性；N1仍候选，H3停止/泛KV主线暂停。133runs3038主、无后台任务。本段取代下方旧待办。

2026-10-31 最新：[结构化输出CPU协议](STRUCTURED_RESOURCE_CPU_PROTOCOL_20261031.md)已冻结，静态兼容性预检完成，不再重复计划。下一条实现并登记12项标准库观测器验收，然后另登记现有后端8 schema45标签语义检查；不能越过观测／语义关卡做干扰结论。旧版依赖与最新强对照不兼容、原生取消绑定／Rust工具链／cgroup条件未就绪。N1只作待验证候选，H3停止、泛KV主线暂停；本轮0真实后端调用／新实验，无队列。本段取代下方历史待办。

2026-10-31 范围更新：[新问题筛查](NEW_PROBLEM_TRIAGE_20261031.md)优先。H3 停止，泛 KV 压缩／约束保持暂停作为论文主线。仅保留结构化输出取消后的资源生命周期为有界实证候选，尚未定题。下一步纯 CPU 可行性协议／版本兼容性预检；比较最强已知方案的资源回收、正常服务和语义覆盖，而非重复旧超时 bug。无新 runner／冻结协议／自动实验队列；来源审阅不增加实验计数。本段取代下方旧待办，历史计划保留。

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

2026-10-30[条件准入与工程证据接口完成CPU验收](runs/20261030-condition-admission.md)，20软件用例/60格独立核验通过；未来36eligible/20预算阻止/4工程未验阻止，历史40生成+20不可行及4保护诊断原样。下一条新增HF编排壳并仅dry-run，分离首次bootstrap工程stage与DEV证据要求，绑定实际input/runtime指纹，blocked operation不得调用。真实HF接线/新版本工程验证尚未完成，不重复当前CPU验收或旧模型DEV；BoolQ/封存/第二模型/新预算不自动推进。108run2852主，无新模型输出或运行任务。

2026-10-30[新数据与真实DEV阶段完成](runs/20261030-independent-development.md)。BoolQ源403两failed保留，评分软件20用例过；SQuADtrain先按输出前修订做12新DEV，Full支持过，实际40主14工程与20主不可行记录均保留。system+anchors120槽，10/12DEV半预算不足，是系统覆盖边界；保护2/2格式不能作为总体方法优势，保护工程均不可行未验。下一条先实现condition-level budget admission/engineering evidence合同与CPU验收，用当前固定60cell不重跑模型；BoolQ来源暂停待正式对象审查。跨任务/第二模型/新预算与封存仍待新协议，旧QA false/封存16、新封存48保持不推理。107run2852主，当前无运行任务。

2026-10-30用户已要求开展系统设计与实证，当前[模块化架构](RELIABILITY_SYSTEM_DESIGN_20261030.md)/[实证草案](RELIABILITY_EMPIRICAL_PLAN_20261030.md)与公共core/adapters已交付，[归档验收](runs/20261030-reliability-system-archive.md)16软件用例/290记录/三cohort一致。下一条按禁用independent-study-draft先固定新SQuADtrain/BoolQ来源、gold-blind bool评分与历史/跨任务文章去重的CPU协议，数据就绪后另冻12DEV小试，不自动启动3264主草案。旧封存16与QA失败gate不改；新研究不以截断丢弃坏结果，交付率与覆盖另定义。当前新增1CPU/0回答，100run2812主；核心描述符验证不等跨模型后端/成本测量或独立科学确认，暂无GPU配置。

2026-10-30用户要求自动推进至可行性结论，[四阶段已完成](runs/20261030-answer-format-direction.md)，当前自动GPU队列结束。Full/真实KV裁剪工程可行，存在格式—任务收益/损伤，但1随机截断使输出前预定完整配对关卡false，按规则不做封存确认/扩矩阵。[选题建议](ANSWER_FORMAT_FEASIBILITY_20261030.md)：保留系统/实证路线，当前单任务不独立成题/新方法；下一步是开题、可配置系统与验收、独立验证的设计，任何新模型/确认须新协议。95→99run，新增80主/22工程，当前2812主；旧待跑tokenizer/Full段均为历史，勿重跑或恢复旧队列。

2026-10-30[新任务CPU数据/评分已通过](runs/20261030-answer-format-task-preflight.md)：24评分+6数据用例、34726 gold原文slice、固定2/16/16角色与独立BFS/源选择回读均通过；不要重跑旧禁用提案。源/选中数据SHA、run证据与未过门槛见[readiness](ANSWER_FORMAT_TASK_READINESS_20261030.json)。下一条先冻有界CPU native tokenizer/config检查，仅工程/开发18题；通过模板prefix稳定、token span、保护+锚点和半prefix预算后，再另冻最多22回答Full-only。当前0新模型回答、无GPU队列，未触封存推理/裁剪；95run2732主，原始短段落不作为长上下文验证，旧队列保持停止。

2026-10-30[新任务契约离线完成](ANSWER_FORMAT_TASK_CONTRACT_20261030.md)：SQuAD v1.1阅读+JSON、任务EM/F1与格式独立提取判分，文章/重复段落组件固定工程2/开发16/封存16，原文最长段落每组1题；数量/长度/标签slice尚未验证。下一步实现并审[禁用CPU预检](../configs/answer-format-task-preflight-proposal-v1.json)的独立标准库scorer与24评分/6数据用例，再服务器单次120秒/0生成检查；runner未实现、尚未执行。CPU/原生边界过关后才另冻Full-only最多22回答及已声明支持门槛，当前不启模型/压缩/留出。0新run/回答，94run2732主保持，报告无需重跑；旧队列保持停止。

2026-10-30[报告层实现已过回归](runs/20261030-reliability-report-replay.md)：9固定输入、210规范化记录、两cohort两口径计数及12fixture通过；v1后审查分母语义遗漏保留，v2修正，不改旧分数。新增2CPU run/0模型回答，累计94run2732主。下一步离线写新任务的数据来源/标签与判分、上下文族独立划分、Full支持与失败条件；报告模块已完成不重跑，尚无新GPU配置，不直接写通用生成器或恢复旧A/guard/攻击队列。

2026-10-30[系统需求与验收](RELIABILITY_SYSTEM_REQUIREMENTS_20261030.md)完成：复用旧真实KV模块的版本受限能力，先新增独立标准库adapter/报告，解除旧32/10/Full正确分母硬编码，显式处理重复键、缺cell、失败/截断/N/A及未测成本。已冻结[禁用CPU报告提案](../configs/reliability-report-replay-proposal-v1.json)，9输入SHA/两cohort预期/12fixture、60秒/0生成；runner未实现未执行。下一条只实现并验证该报告，不改历史脚本或重跑旧TREC，新数据/第二模型另设计。目前0新run/回答，92run2732主保持。

2026-10-30用户确认接受明确问题的系统/实证研究，[一页选题稿](THESIS_CONVERGENCE_20261030.md)完成：优先讨论普通Transformer真实KV压缩的输出约束可靠性评测系统与实证分析，严格同预算区分约束遵守/任务正确性/保护代价，不追求新漏洞作为前提。下一条仅离线盘点现有实现/字段并写系统需求、验收与数据契约；旧TREC作开发/回归材料，不自动重跑。独立确认和第二模型尚未完成，新实验另冻协议。A/guard/控制器与取消队列均不恢复，92run2732主不变。

2026-10-30[取消记账只读门槛完成](CANCELLATION_ACCOUNTING_GATE_20261030.md)：取消完成统计缺口有静态依据但已由issue55634/PR55940覆盖；泛尾部停止/输出失效有Retire等直接近邻。真实配额绕过缺实际契约/执行链/强对照证据，不进模型/服务/算法。下一步先写一页选题收敛稿，明确已有可用工程、已覆盖主张与可完成的毕业范围；不是继续批量搜候选或自动转第3项。92run2732主不变，0新回答/实验，A/guard决定保持。

2026-10-30[默认profile工程关卡完成](runs/20261030-controller-profile-validation.md)：110raw样本/N1直接采样/独立整表exact及两回答token一致通过。当前成本不再全平台，但旧397向量新表N1重放仍全4；无损害/正常敏感域证据，结束本固定配置筛查，不扩GPU矩阵。下一条仅对既有第二线索“取消后资源记账”做一次源码契约/执行方/近邻门槛审查，不假定引擎有租户计费，未通过不跑模型/服务。原profile提案false/未实现字段是冻结输入历史，不表示待运行。

2026-10-30[离线成本审查](CONTROLLER_COST_PROFILE_AUDIT_20261030.md)完成，原N1平台有工程图桶/补表限制，成本准确性未验证，正常敏感域未知。下一步仅实现[禁用raw-profile工程提案](../configs/controller-profile-validation-proposal-v1.json)，保持原模型/长度/backend，撤工程图尺寸覆盖并核源码推导；最多2工程短回答/600秒，0主历史，保存原始重复计时/形状/context并独立复算表。runner尚未实现/方案未执行；原生dummy计时不是完整真实周期。未通过覆盖/一致性门槛即停，不调图尺寸或扩矩阵求效应。尚无论文/损害结论。

2026-10-30[自然历史小试](runs/20261030-controller-natural-history.md)完成30主+4非主；历史A/B自然refit并改变预测，6探针预算/accepted/输出不变。397决策复算及CPU成本域诊断确认当前N1饱和，真实feature的假设N2回放也无变化；不以uniform反例立题。本配置队列结束，不自动扩历史/提示/seed/预算/模型/batch。下一条只离线审native profile/热身和公开正常负载覆盖敏感域的可行性；无具体可检验预测不新冻GPU试验。旧A/guard不变，未建立攻击或论文问题。

2026-10-30[worker v5通过](runs/20261030-controller-worker-v5.md)，64Full cache spec和空闲控制器恢复/重放/冻结可用，不重跑。下一步仅实现[禁用自然历史提案](../configs/controller-natural-history-proposal-v1.json)逐步预算观测，先2工程输出透明性gate，再最多30主+2warm+2工程/34总/1856tokens/900秒的两固定历史学习/冻结/恢复小筛查；runner未实现，未执行。使用共同自然warm状态和真实graded标签，不能沿工程phase95注入；自然refit不足停，预算/系数改变不直接当延迟损害。无攻击/创新结论，旧gate保持。

2026-10-30[配对模型准备与初始化失败](runs/20261030-controller-worker.md)：draft/目标tokenizer已核验。两次初始化0答案/0RPC：v1我方eager配置错误，v2默认FlashAttention2不支持所需可变长度图；真实恢复未测，不是研究负结果。下一条仅核对禁用v3提案70d6e89f...的显式TRITON_ATTN能力与GPU资源，再新v3目录执行相同6工程答案/600秒恢复门槛；不重复下载/CPU测试/旧run，不关闭adaptive或扫后端。通过才历史影响配对小试。

2026-10-30[运行环境与原生检查](runs/20261030-controller-runtime.md)通过：独立vLLM0.32.0环境已安装并锁定，原生估计器127step及估计器自身完整原址重放通过，不重复bootstrap/CPU关卡。下一条准备固定draft/tokenizer，随后冻结真实worker有界工程协议（少量短输入、极小输出/时限、单卡），覆盖异步confidence双缓冲/stale_idx/pending_resets/事件依赖的可信RPC完整恢复；通过才进入配对自然历史小试。无模型加载或历史影响结果；A/guard gate不变，以下未建环境为历史。

2026-10-30[CPU v2](runs/20261030-controller-history-cpu-v2.md)54/54通过，完成当前CPU参考关卡，不再重复合成检查。v1失败保留；真实输入影响/创新/GPU等价仍未验证。只读运行准备已发现旧venv依赖不满足、缺draft/真实worker快照接口未实现，候选版本与官方来源见CONTROLLER_RUNTIME_PREPARATION_20261030.json。下一条是隔离运行环境的依赖/二进制兼容锁定与模型tokenizer/状态接口准备，另冻有界GPU工程关卡后才小规模配对筛查。本轮没有安装/建环境/下载权重或启动GPU。

2026-10-30[CPU预检v1](runs/20261030-controller-history-cpu.md)已运行并因fixture断言过强停止：32通过/1失败/21未跑，不宣称整体正确或状态恢复通过。归档复算确认负slope防护允许共享系数不变，属于我方工程检查错误，研究假设未测。revision2代码和禁用修正提案已准备，保留全部fixture/seed/数值上限，下一条仅新v2目录复查CPU预检；本轮未重跑，不进入模型/新算法。旧A搁置与guard gate保持，累计79run2702。

2026-10-30用户选择共享在线控制器历史影响：[生命周期/近邻审查](CONTROLLER_HISTORY_AUDIT_20261030.md)完成，结构性前提成立但无真实损害/创新证据。下一阶段仅CPU代数与完整状态预检，禁用提案controller-history-preflight-proposal-v1.json已固定上限/六类检查，runner未实现/未执行；不进GPU或重做泛预算方法。通过只能支持自建参考正确性，再独立冻结真实输入/Full Attention模型/共同预热版本与强对照。前轮停止的泛预算队列、A搁置、旧工程gate保持。

2026-10-29[投机交叉问题单次门槛审查](SPECULATIVE_DESIGN_GATE_20261029.md)完成：当前立题/模型执行no-go，结束该待办，不自动继续近邻检索或开实验。当前vLLM自适应验证已经覆盖接受率+profile成本预算，逐请求观测也已有；LAPS-SD、SPECTRE及公平调度强基线补齐。没有证明这些机制充分解决跨用户尾延迟，但也没有形成其直接适配不足的具体研究证据。无启用配置/新算法；旧KV平台保留、A搁置/guard停止不变。

2026-10-29[整体收敛](RESEARCH_CONVERGENCE_20261029.md)：当前KV裁剪安全新算法主线暂停，不扩同类曲线，已有结果仅保留平台/负结果。A搁置、B/C/D/E宽泛方法不开发，旧工程gate不变。仅建议一次针对投机解码相同token配额下跨用户干扰的文献/源码审查；必须超过接受率攻击、简单回退、VTC成本适配及FairInference逐token延迟公平的已有覆盖，才另写小筛查协议。不是定题/转向或已启用实验，不改其他方向，无新矩阵或配置。

2026-10-29：[E查重结论](E_NOVELTY_GATE_20261029.md)补入COMA v4直接覆盖共享预算/不可信输入/可信规则丢失与隔离压缩；E宽泛新方法主张no-go。RobustKV重要性近似评估的限制不抵消该重叠。A搁置，D降级，旧工程停止保持；当前没有已通过设计门槛的新选题/执行矩阵。下一产出应为选题收敛决策，先给出超出现有机制与防御的具体问题和强基线不足依据，不自动改名或跑同类安全曲线。本次无新实验、攻击生成或代码执行。

2026-10-29：[D差异审查](D_NOVELTY_GATE_20261029.md)完成，宽泛安全记忆/分散证据/未来需求方法已有MAGE、TRACE、LRE、StepKV/CommitKV覆盖。D降为待证备选，不恢复旧runner或配置；严格资源契约与强基线不足均未证明，故暂不进模型实验。下一条选题工作是E直接重叠审查，尚非实验队列；A继续搁置。资源与方法的公平比较要求见新文档，不以更换预算口径自动产生贡献。

2026-10-28恢复检查终止当前冻结执行方案：[工程失败与诊断](runs/20261028-action-guard-engineering-failure.md)。三次尝试0主要答案，6工程输出；v4关闭HF默认覆盖后缓存两路径一致，整段/切分仍第54 token不同，原三路径门槛保持未通过。限定teacher forcing复现已有分叉，不构成能力结果或KV裁剪效应。当前不自动v5/32题/压缩，不扫attention/精度/seed以过线。A当前方法归约no-go，C被直接覆盖，D暂为没有任务支持/创新证明的用途；本轮研究审查以这些否定与缺失结论收尾。后续若另立设计，须先定义可审计的数值可比性标准及对强基线的实质问题，不把已有六条工程输出当独立研究样本。下方恢复待办为历史。

2026-10-28窗口收尾：A归约no-go，C宽泛拒答/证据差距已有直接近邻；下一条仅恢复已冻结动作guard Full/NoHistory能力关卡，详见[断点](RESEARCH_WINDOW_20261028.md)。32例和模型已准备，但平台用量限制使runner在加载前停止，尚无能力或压缩结果。不要跳过支持门槛开发方法或扩矩阵。

2026-10-28启动审查更新：[候选A当前方法主张no-go](PREFIX_RISK_DESIGN_GATE_20261028.md)，不执行历史256输出建议。转为同一工作窗口的证据充分性/拒答近邻与公开输出审计，先判断标签、评分和分层分头实际KV是否留有明确可证伪问题；已有Compression-Aware Abstention、Sufficient Context、KVDiagnosis必须作为强近邻，换数据或泛“丢证据就拒答”不足以立题。仅在问题差异和固定强基线成立后另立有上限方案，当前无模型执行快照。

选题调研（2026-10-28）：[报告与淘汰条件](TOPIC_SURVEY_20261028.md)完成，先评估可复用prefix的按组约束风险/正常效用联合预算问题，不宣布定题或创新。Risk-Controlled/FlowKV/执行状态遗忘等已排除泛风险回退、重复压缩、撤销后重放的宽泛新意。下一步一页差异与可行性设计；没有超出完整规则保护、逐组校准等简单方案的问题就停止，不自动运行报告中的建议小试，不恢复已结束TREC校准或旧失败AccessDenied。

当前决策（2026-10-28）：[留出复查](runs/20261028-trec-holdout.md)50主要＋24工程输出完成，Full7/10，四裁剪正确7/6/7/7、格式10/9/10/10，0截断/error；独立审计通过。按预定单次复查规则结束本轮，详见[阶段结论](TREC_CALIBRATION_CONCLUSION_20261028.md)。开发32和留出10分开报告；有精确标签格式损伤/恢复案例，尚无一般安全效应、稳定方法排名或新算法贡献。

接下来先离线收敛研究问题：具体约束、正常能力对照、固定预算代价、简单强基线、与已审文献的差异及否定条件。当前不自动增加数据/seed/预算/模型/提示，不开发复杂算法，不复活旧失败gate。下方“最新/下一步”为历史计划，以上文为准；新实验需要独立冻结方案。

## 历史计划与执行记录

最新准备（2026-10-28）：[10题留出CPU冻结](runs/20261028-trec-holdout-cpu.md)完成，[新复查提案](../configs/trec-holdout-recheck-proposal-v1.json) SHA147aea59...保持禁用。下一步独立10题runner按12 Full校验→10主要Full（exact≥5、格式10、截断/错误0）→12压缩校验→40压缩主输出；不过Full不进入压缩，不修提示/换题救回。保留原四方法/相同50%预算/全部10含两个原语义注意案例，一次复查后收敛。示例仍约52%–66%共享，n10不作显著性/稳定方法排名或独立数据证明；旧gate不改。

最新结果（2026-10-28）：[50%真实裁剪校准](runs/20261028-trec-pruning.md)128输出完成，24工程检查通过，Full19/32对Snap17/随机17/Snap-pin16/random-pin19；四条件格式31/30/32/32，0截断/error/N/A。pin恢复本次3非法标签，但分类仍错，且Snap-pin有新损失；不能称无损或新安全方法。下一步仅CPU审剩余10个同源同长度未用问题，制定包含全部四方法的固定留出复查，先冻结gold/示例复用/Full与停止条件，不按本次赢家/错误子集挑题，不扩长度/换seed凑规模。无新启用配置，不扫描更多预算，旧gate不变。

最新（2026-10-28）：[50%方案CPU预检](runs/20261028-trec-pruning-cpu.md)已完成，32题header/预算、四方法14,336head maps、100%恒等/等字节/随机重放通过；prepared配置892bde36...仍execution_enabled=false。下一步独立真实模型runner先做首3题K/V hook不变/Full baseline重放/100%gather/压缩位置原生与custom对照（最多24校验输出），不能拿Full-only custom直接裁剪。通过才形成执行快照，原32×4最多128压缩主输出、全部13Full错题保留。CPU合成maps不是实际saliency或模型质量；仍仅分类/格式校准，无安全/创新主张。

最新实际结果（2026-10-28）：[TREC Full关卡](runs/20261028-trec-context-full.md)64输出完成，19/32对11/32、四转移10/9/1/12、全部格式合规，6请求三路径一致；达到独立描述性context支持门槛，不是旧安全任务门槛通过。下一步仅CPU准备[50%裁剪校准提案](../configs/trec-pruning-calibration-proposal-v1.json)：原32 with_demos、适配SnapKV/随机及各自完整任务头保护，四条件同实际KV字节，最多128新主输出、工程重复最多24。先冻结header位置/成本、预算/索引/锚点/100%恒等/随机重放，再实际hook/Full复查，未通过不执行。复用已审Full基线并保留全部13错题与19正确分母，NoDemo转移不混称裁剪损坏。当前尚未压缩，无安全特异性或创新主张。

最新执行准备（2026-10-28）：[TREC数据CPU预检](runs/20261028-trec-data-preflight.md)通过，32题/两条件输入及source SHA冻结；[新能力提案](../configs/trec-context-gate-proposal-v1.json)仍execution_enabled=false，待runner与缓存检查。下一步先首3题两条件三生成路径一致，再做有/无示例各32个Full KV输出；不裁剪。两边固定相同标签表和输出指令，仅移除示例，长度/位置随之变化；需如实报告并审是否依赖context。with exact≥16、截断≤3且有对/无错≥8对为描述性最低支持，否则保留64输出并停止，不换题或提示。未来压缩仍需独立设计，旧IFEval及AccessDenied失败不变；此校准不是创新或安全效应证据。

最新来源审查（2026-10-28）：[SystemCheck/Pitfalls与TREC](runs/20261028-systemcheck-source-audit.md)已完成。S-IFEval未包装/默认prepend/标准defense最长分别108/132/216token；旧方案停止不变。下一步仅CPU取得并冻结官方LongBench TREC原始数据revision/SHA/许可/key，检查示例、标签、前端实际长度和预算；官方取首行的分类指标与完整输出约束分开，须审context依赖。Pitfalls附录I已做长TREC分类/防泄漏，不能当新贡献；暂无待启动模型矩阵。

最新执行状态（2026-10-28）：[IFEval CPU预检](runs/20261028-ifeval-cpu-preflight.md)仅1/541题满足预定256–2048前缀，未达32题，原校准方案按规则停止、execution_enabled=false。下列校准参数为历史设计，不是待启动命令。下一步仅审长上下文约束任务的来源/构造/许可、实际长度、约束位置与内容能力对照，优先核查Pitfalls SystemCheck，再另立可行方案并做CPU预检。不改原阈值/加padding来救回本方案。

## 问题与边界

2026-10-26 用户明确：研究普通 Transformer（各层为 Full Attention）的 KV 压缩，不从旧 nano-vllm 复制代码或文件，不使用 Qwen3.5 Hybrid 基线。本方向独立选择模型与实现，MHA/GQA 的具体配置须查证。初期聚焦近似删除 KV 位置，量化、合并作为不同机制处理，不混同于分页回收、卸载或抢占重算。

目标为可用于小论文或毕业论文的研究闭环。待验证假设：回答相关性与约束保持所需的信息可能不一致；但这个宽泛现象已有直接近邻，必须进一步收窄。

候选题目：面向长上下文约束保持的 KV 缓存裁剪机制研究。题目与假设均未正式确认。

2026-10-27 更新：进一步查重显示普通关系保持、语义组/步骤保留、RBAC 双侧评测也已有近邻，不能将下文候选当作新方法。最新差异判断见 [NOVELTY_REVIEW](NOVELTY_REVIEW.md)，具体正确性门槛、配对设计和待执行筛查见 [VALIDATION_PROTOCOL](VALIDATION_PROTOCOL.md)。优先区分一般关系能力下降与权限约束的额外退化；若未区分，不主张安全特异机制。

首轮实验后更新：用户已明确本会话为新开的实验会话并授权。已执行部分正确性与开发诊断，详见 [20261027-pilot](runs/20261027-pilot.md)；完整两跳、较长前缀和同构对照基线未可靠，未运行原计划大矩阵。简化502token权限任务看到裁剪变化和规则保护的误拒答，但仅3个基础世界，不支持方法或机制结论。下一步先修复/验证基线任务，暂不进入关系保留算法开发。

后续更新：已完成 [基线审计与事实诊断](runs/20261027-baseline-audit.md)。结构化方案新96请求基线通过，但50% KV时保护全部结构化事实即可48/48，等量随机10/48、仅规则7/48；尚不需要安全特异的关系损坏解释。暂缓原候选算法，优先补强query-blind对照、等字节任务匹配和无法全留事实的规模。结构化方案改变格式/措辞/预算，不把它与旧直接输出模板混报或当作新防御。

## 最小实验

最新研究决策（2026-10-28）：见[RESEARCH_RESET_20261028](RESEARCH_RESET_20261028.md)。暂停AccessDenied模型/提示搜索；通用诊断/IFEval曲线已有近邻，暂不立新算法。下一关仅CPU准备官方IFEval校准提案：已有Qwen2.5原生user、不改prompt、完整任务已知的query-aware post-prefill、32固定源key/真实KV字节/原版strict与全样本四转移，最多160主要输出。真实数据SHA/key、依赖/kwargs和检查器CPU正负例、新user切分与随机选择器尚未预检，配置execution_enabled=false。通过后另存执行配置，先32 Full、最低支持量不足停而不换样本；压缩仍跑原全32而非Full正确子集。此是测量规范/有限复现，不是已证创新，不更改旧任务门槛/失败状态；当前无模型任务。

最新Mistral原版Full完成（2026-10-28，runs/20261028-mistral-full）：完整权重/运行时32Full层与缓存三路径通过，质量严格8/0/2，8同事最终块披露、缺失另4禁用值，确认/裁剪未运行。在此发展适配下3配置/2族均未过门槛，暂停该模板继续换模型/改提示，下一步先离线梳理研究可行性：Full稳定性、事实检索/权限/缺失/前端差异，以及原全事实保护上限已解释的退化和剩余未证假设。新任务须有独立理由、机械gold与正常对照并先冻结，不以筛到过线当贡献。以下下载/候选步骤是历史状态，权重已完整可用。

最新独立族选型核查完成（2026-10-28，runs/20261028-mistral-candidate）：仅选Mistral-7B-Instruct-v0.3 fixed c170c708c41dac9275d15a8fff4eca08d52bab71，按公开/Apache声明/特定32层无滑窗config/单4090资源选择，不依据成绩。metadata3.31MB全摘要、meta结构/48条native前端与slow-fast一致检查通过，尚无权重/推理/缓存生成验证。system-only模板不含资料，须从完整native串在query前切prefix；原消息不改，但Mistral角色token机制不同于Qwen。下一步先完整3HF权重分片固定摘要/头dtype检查，后原版24发展基线；门槛不放宽、失败停止、通过才确认；不继续提示搜索。

最新有限因素审计已完成（2026-10-28，runs/20261028-delivery-factor）：原版24输出逐token复现；保留policy/examples仅改四处输出指令，严格正确由8/7/3变为8/0/0。同事6次最终块禁用薪资、2次可读本人薪资但答错对象；缺失另1次禁用薪资。全24输入+14、CONTEXT位置+20tokens，不能唯一归因于无解释或排除位置效应。停止AccessDenied模板提示搜索与裁剪；下一步先只读核查独立模型族的固定候选，依据Full Attention/公开revision/许可/资源兼容性选择一个，后续沿原版24发展任务而非改提示。确认context2258–2265继续保留未推理，旧门槛不放宽。以下旧“待做输出审计”已执行失败，不重复。

最新答案契约检查已完成（2026-10-28，runs/20261028-answer-contract）：原可信字段/gold不变，一版联合适配明确缺失优先与最终输出要求，Qwen3 Full本人8/8、同事0/8（8次最终块披露）、缺失6/8，失败。确认数据已在推理前冻结但未运行。暂停继续更换/精简模板；下一步先冻结有限因素审计设计，保留旧政策与示例、只改变交付要求的条件应独立命名，避免将policy/例子/长度/解释的联合变化归因于单项。仍无法建立Full基线则收缩/调整任务，不扩大裁剪矩阵；下段“预注册新契约”为本轮前历史步骤，已执行但未过门槛。

2026-10-28最新执行：Qwen3-8B固定revision b968826d已下载并在原24发展集复查；本人8/8，同事最终块8/8正确拒绝、全文严格7/8（一次解释薪资），缺失3/8，门槛仍失败。新8个contexts确认数据已在模型前冻结但未推理，禁止以本次失败gate启动screen。下一步优先审计源policy的plain-text thought-process指令及应用brace交付约定，预注册权限决策、资料缺失与原始/最终输出三个边界，再确定新的任务/模型选择理由；不连续换提示/模式直到通过。详见runs/20261028-qwen3-access，下文为研究设计而非已完成矩阵。

1. 独立选择并核查公开裁剪实现、纯 Attention 模型、版本、裁剪阶段、逐层/逐头粒度与实际预算，不移植旧混合架构项目。
2. 构造合成数据中的权限与披露约束，以及允许读取/不允许披露的配对任务；同时保留正常问答任务。
3. 在相同 prefill 检查点保存完整状态，对照完整 KV、原裁剪、等预算简单策略、保护固定前缀的策略。
4. 对失败样本恢复疑似关键位置，并以等量随机恢复作对照。固定其他状态，记录模型随后生成的变化。
5. 测试约束位置、上下文长度和对话轮次；先小规模诊断，再扩大模型和数据。

## 指标与混淆因素

- 同时报原始安全失败率，以及完整 KV 正常且安全样本上的配对变化；明确分母。
- 正常任务正确率、误拒答、约束违反/模拟敏感内容披露、实际缓存字节、延迟与整理开销。
- 不以拒答关键词独立判定安全；对分歧样本人工复核。
- 恢复 KV 有效不自动证明原始约束只存于这些位置，须结合对照解释。
- 当前只研究纯 Attention 模型；后续在不同模型族上检查泛化，不引入 recurrent/conv state 混淆。

## 实现与证据

初期使用现有裁剪器和可插桩完整 KV 基线，不先重写 kernel。计划创建 configs/、scripts/、results/ 和 docs/runs/，实际需要时再建。

每次运行保存命令、版本、逐样本输出、保留索引和汇总脚本；参照根 docs/EXPERIMENT_TEMPLATE.md。

## 继续/收缩条件

若在合理预算下无稳定安全变化，或简单前缀保护已经解决问题，及时收缩/调整；不得为得到退化而只挑极端配置。若找到可解释且已有方法未覆盖的失败，再研究等预算的改进保留策略。

## 候选切口：条件约束关系保持（助手建议，未定题）

问题：压缩是否保留了孤立的规则和内容，却破坏主体、对象、条件、允许动作之间的绑定？例如规则是“仅 A 组可访问 X，B 组仅可访问 Y”，压缩后是否出现把 A 的权限用于 Y 的现象？所有内容使用合成资料，不涉及真实凭据。

最小设计：相同规则和资料下，只改变查询主体或目标对象，构成应允许/应禁止的配对任务。随机化实体名、文档位置、规则位置，控制长度，并加入不相关规则与相似干扰对象。先测静态条件，动态授权撤销留作扩展，避免一开始混入多轮状态与工具调用。

诊断分别测规则复述、资料检索和权限判断；三者在独立分支上测试，不能先提醒规则再把后续正确当作原始表现。即使规则复述正确，也不能据此断言内部表示完整。使用成组移除、恢复或等预算替换检查规则、条件事实和对象绑定的联合效应，加入等量随机、仅规则和仅事实对照；这类干预本身已有近邻，贡献须落在新的失败模式与证据上。

方法候选：在固定总 KV 预算下，对有效规则及其相关条件事实、实体绑定进行成组保留，并将余量交给已有重要性选择器。先用生成器提供的真实 span/关系标签测上限，明确这是 oracle；实际方法只能使用公开结构元数据或独立提取器，不能偷用标准答案或测试标签。提取器的误差、开销与元数据字节均需报告，并给基线同等可用信息。

关键对照：Full KV、原裁剪、同预算固定前缀/规则白名单、Pitfalls 的公平裁剪、仅按实体或句子成组、等量随机成组，以及适用的安全感知方法。必须证明收益超出“多留了一些 token”“完整保留规则”或“提供了额外答案信息”。保护全部规则的成本可作为预算曲线中的参考，不强行塞入容纳不了它的预算。

主要结果分别报告禁止侧违规披露率、允许侧正确完成率和误拒答率、整对同时正确率、完整 KV 两侧均正确子集的转坏比例，以及实际 KV 字节、元数据、预处理与推理延迟。报告全部样本结果，不能只留下条件化子集。

小论文优先聚焦一个稳定失败模式、一个有区别的改进与跨模型验证；毕业论文可在此基础上扩展动态约束更新。若公平裁剪或完整规则保护在相同预算已解决问题，或成组方法只依赖 oracle 标签有效，则收缩主张或调整选题。目前没有新颖性或投稿成功保证。

## 最新执行决策（2026-10-27）

多事实32/64行检查见runs/20261027-scale-queryblind。已配平prefix/suffix与K/V字节，全部事实原始位置无法在50%固定保留；但32行新世界Full每任务仅5/6世界四问全对，未过门槛，64行也失败。整段原生48/48与缓存输出逐token相同。停止裁剪效果矩阵，先稳定Full KV查组可靠性；不因新世界失败改门槛或筛选通过世界。EA与行对照仅完成评分/索引/字节工程检查，没有效果证据，关系感知新方法暂不开发。

后续单一two-shot候选与16行原模板均在事先固定的新世界失败（runs/20261027-lookup-stability），本轮按承诺停止其他规模/提示试验。lookup-only已在相同目录token/位置下复现正确ID/payload但错误group，不能把这一基线错误包装为裁剪损害。当前暂停当前合成权限任务的连续修补；下一步审查标准单system前端、事实位置平衡及替代任务/模型，分开直接检索与约束决策。现两任务只配平总长度/字节，事实起点仍差19 tokens；正式任务比较须进一步控制。单system是否改善只是新假设，须新世界验证，不先定原因。

最新前端/位置审计已经完成（runs/20261027-frontend-audit），不是待办：single_aligned未过，故预定新世界未运行；仅oracle给定行达到48/48，额外提供事实和长度，不构成可部署方法。停止当前模板的前端修补。

后续按分解后的测量准备：①固定公开检索控制版本（RULER，核查main legacy与新版分支差异）；②固定OrgAccess easy的实际数据revision、确定性小样本ID、人工核验标签/歧义，保留full/partial/rejected原义，独立审计输出解析；③再迁移AccessDenied的内容披露场景，原作者答案块评分与本项目全文扫描并报。不能把公开benchmark换成自建长padding后仍称原版；若仅检索控制通过而权限不通过，不进入安全特异裁剪结论。只读源码/许可已保存服务器，尚无这些基准的推理结果。

## 2026-10-28：标准控制与数据审查后的决策

上述前两步已实际完成。RULER固定legacy数字NIAH轻量HF控制（不是最新正式pipeline）在1767/3431token、16配对种子共32题正确值包含32/32；模型自然复述query编号，严格数字独占率0，补充解析32条均为query key后给正确value。单键值检索控制通过不代表条件关系/安全任务可靠。

OrgAccess固定GitHub easy38,280行前32条仅作原标签一致性观察：16/32，因推理前已发现partial政策与缺失biometric实际状态问题，禁止将其称正确率。全快照相同permissions/query对应不同标准标签593组，含role/timestamp仍592组，故暂停将这一快照用作准确正确性门槛；不改gold或挑“通过”样本。下一步转AccessDenied显式数据/权限规则的gold生成核查，先锁允许/禁止/缺失样本ID和全文评分，再做Full；暂不开发新方法，不以两个不同任务分数差解释安全特异性。详情runs/20261028-benchmark-baselines。

AccessDenied后续已完成（runs/20261028-accessdenied-pilot）：基于8个固定source context构造本人/无权同事/目标缺失24请求，身份role/department/HR明确，原作者HF原生system/user前端与机械oracle通过。Full本人8/8、同事0/8（最终块披露8/8）、缺失0/8；未裁剪，未继续修提示。数据字段足以解释gold，但当前Qwen2.5-7B/政策模板组合不够可靠。下一步锁另一纯Full Attention模型、版本与推理模式，先在同24发展集复查，过后另选独立contexts确认；Qwen3-8B仅是已核查配置/未取权重的候选，不保证更强或新颖，不冒充第二模型族。

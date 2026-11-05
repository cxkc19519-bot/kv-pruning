# 两模型CPU预检v2：访问守卫诊断修订

2026-10-30，v2执行前冻结。原[执行注册](INDEPENDENT_FRONTENDS_EXECUTION_PROTOCOL_20261030.md)/[v1配置](../configs/independent-evidence-frontends-preflight-v1.json)保留；v1按技术停止线退出，原工件不覆盖。本页将同一用户任务内的机械守卫修正另行注册，不是按预算结果改样本。

v1 PID987652/launcher987649，3.973699秒exit1；48完整native变体/96编码/32model-case/128预算评估已完成，但最终CPU_boundary_guard失败。禁止权重/网络/子进程的guard已阻止一次socket.bind并将其计为network_attempt，其他三类尝试均0；真实外联请求、下载、权重、模型前向/回答、GPU均0。原manifest e85b93f7…与失败closure/后验保留，计入113run，不以native检查完成冒充原运行成功。

单独离线import-only诊断未构造tokenizer/模型或额外编码，记录堆栈为urllib3 2.3.0的util/connection.py中_has_ipv6调用sock.bind(('::1',0))，在操作前被OSError阻止；这是可选回环能力探测，不是访问数据源。诊断SHA4348b88c…保留。原CPU预检导入Transformers时“无Torch/TF/Flax、仅可用tokenizer/config”的提示是预期保护，不是依赖缺失待安装。

新[runner v2](../scripts/preflight_independent_evidence_frontends_v2.py)/[配置v2](../configs/independent-evidence-frontends-preflight-v2.json)继续阻止该bind；仅当固定源码SHA/version、准确调用者_has_ipv6、地址::1:0和事件socket.bind均匹配，单列blocked_loopback_capability_probes=1，不视为已完成网络请求。其余bind/connect、子进程、权重或未白名单文件尝试仍停止。模型目录白名单同时覆盖HF symlink的原路径/解析后blob路径，避免只看真实路径遗漏缓存目录限制；权重扩展名在原路径和真实路径均拒绝。没有允许任何socket操作，也没有绕过外部认证。

模型/16metadata/template、16固定case、3query规则、边界/保护算法、两个预算和报告分母均不改。v2仍96编码/128评估、120秒内/150秒外watchdog/TERM后10秒、32文件32MiB、0权重/GPU/网络/模型前向。两次CPU运行合计192次编码/256次预算计算是技术重复，不增加独立样本或模型回答。新独立检查器还须证明v1/v2三份原生变体、tokenized cases和budget evaluations文件逐SHA相同；否则停止，不再自动注册v3。

v2只在新目录results/20261030-independent-evidence-frontends-preflight-v2执行，实际source/proposal SHA及完整CLI由launcher归档，原false提案不追改。完成后两run一并记录；CPU通过不能开启Mistral Full或封存推理，下一GPU阶段仍须单独冻结协议。

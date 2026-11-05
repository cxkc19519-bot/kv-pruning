# HF系统DEV端到端验收：v1失败保留，v2完成

## 实验身份

日期2026-10-30，Asia/Singapore；用户在已授权实验会话要求“开始下一步”。[执行前协议](../HF_DEV_ACCEPTANCE_PROTOCOL_20261030.md)及[输出前修订](../HF_DEV_ACCEPTANCE_AMENDMENT_20261030.md)分别冻结。问题是工程检查点恢复、条件准入、真实调度、双判分与统一归档能否组成可复现系统；这是既有12DEV的集成验收，不增加独立科学样本。

服务器绝对目录：
- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-hf-DEV-acceptance-v1`，failed，0生成。
- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-hf-DEV-acceptance-v2`，complete，36主回答1115token。

来源为本项目独立实现的HF/Qwen KV原语及固定SQuADtrain准备，不复制nano-vllm/Qwen3.5 hybrid。项目未配置Git远端，逐SHA源码快照标识；原数据、模型、输出和实验日志仅服务器。

## 可复现条件与检查点

既有Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1/safetensors0.6.2环境，Qwen2.5-7B-Instruct固定a09a35458c702b33eeacc393d103063234e8bc28，28Full Attention/GQA4/head128/BF16/SDPA/57344K/V bytes-slot，未安装/升级依赖或下载模型/数据。GPU1 UUID4ce22e12-b5c0-e423-06c5-e858bb71daaa/RTX4090/驱动580.178.04；初查和独立收尾15MiB/0%，后端加载前另核≤128MiB/util0，未操作他人进程。四权重及六模型metadata在每次后端加载前完整SHA核对，实际runtime须等于上轮工程记录。

相同原12DEV，greedy128、rep1、EOS151643/151645、pad/bos151643、fresh GenerationConfig、TF32off、torchseed20261030；随机selector原seed20261028、context_group_id、半预算、sink4/recent64。不改题/提示/答案/预算/抽样或输出长度，封存16/48不入模。真实tokenizer复核12DEV原生模板ids全同。

新增恢复器 `8feb4a3cfb2cf364a2018a9205aacedf858104797710ed7384adaf7ec7151139`：校验固定工程原/后验manifest、相关源码、输入，重建14条request/raw/accepted与全部case binding，重新计算5条件evidence并与原记录全等，才能恢复。原数值生成器scope `e2ee00abf023b825c655280da7b57a488857726dc7340fb3215909db697cd3d1` 保持；新执行/评分协议另有digest `b1304610386055f3fb93d542a46b818cfc6abb8c1b5b21895a435396cc0fa68f`。这不允许不同生成器版本借用旧观测。工程开关false/cap0，14旧观测只标restored，新增工程回答0。8软件检查在两个run各执行一次（8唯一用例、16次case执行），无软件模型输出进入真实证据。

[配置v1](../../configs/hf-DEV-acceptance-v1.json) SHA `88c9ff405578ad3c60133ebcecf34586dde52529423ae9dd61b521793d85dc66`，runner `678ac43197b6d026f116095f049d612d289b32ee36fda3b2911e049480a853dd`；[配置v2](../../configs/hf-DEV-acceptance-v2.json) SHA `bc4388052fea6e115a04e04c405199a61ca3ef7f0c55437e548aa041fadfaf04`，runner `62f61b157be8fa2bcdbea79e41f2e10a83064d3e54abaad085ad4213cb3f8991`。原编排/后端/合同/核心源码不改。独立stdlib verifier `0bf578b3e342d3c2554c5134c6774559a876d06327e319fe15fad5e96cf69143`。

## v1失败与修正边界

UTC11:44:02.377145—11:44:23.941419，worker948163内20.910878秒、launcher948160共21.564099秒exit1。8恢复检查、14观测恢复与60格准入完成，第一次后端加载模型后，Python model_config直接比较JSON归档触发actual_model_config_changed。**DEV dispatch/backend尝试1次、实际生成0条0token**，未调用生成路径、未得到新任务成绩。错误与活动request/console原样保留。

离线CPU AutoConfig发现唯一差异id2label键类型：当前Python为int，归档JSON为str；完整config JSON往返后逐字段全同，actual_runtime比较此前已通过。诊断及键类型证据保留，不加载权重做诊断。v2只把整份实际config规范化到JSON后比较，并保存比较结果，没有丢字段、放宽实际配置或更改模型计算。修订在任何新任务输出前冻结，沿同一用户系统修复任务另注册一次v2；原v1不覆盖、不自动原命令重启，v2失败则停不扩v3。两run合计仍至多36生成回答。

v1原manifest28项，后验分开增加诊断/键类型/closure/derived，最终33文件407076bytes。原manifest `e3bfa15e19c4e09b0f2924210da297d03047de368485b4c11de9a39ba4fc100b`，诊断 `5d2a4e38158f82de61e59e7f246634c307f0fea07d885a1bf578299e70618c1d`，键类型证据 `6116dd1510b56fc457d1ff080e5c12da7138e9cdf0183e6cbffea252cf05a657`，derived `b4a4803713ea7a6964267fafd96d2730b3c97f4e6093c6b00f9682f41845b8a4`。

## v2实际运行与结果

UTC2026-10-30T11:46:57.383591+00:00—2026-10-30T11:47:41.698576+00:00。worker950105内43.615357秒，launcher950102共44.314807秒exit0。内部600秒/外层660秒watchdog/TERM后20秒仅自有组、128文件128MiB上限；实际36主回答1115新token（含终止token），0新工程/保护/封存输出。4个自有PID均退出，无服务/端口/后台队列。

外层固定UUID/离线环境并设置KV_DEV_OUTER_WATCHDOG，实际调用：

```bash
.venv/bin/python -u scripts/run_hf_DEV_acceptance_v2.py --proposal configs/hf-DEV-acceptance-v2.json --execute-DEV
```

launcher源码、精确命令与console同级保存；不要脱离watchdog或因旧proposal true重跑。console torch_dtype弃用提示保留。新raw先append，再进行位置/KV/旧参考检查、编排接收和真实文本评分，异常不会丢掉已生成结果。

| 条件 | 生成/12 | 预算不足 | 工程未验not_run | 任务EM/可评估 | 格式/可评估 | joint交付/12 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| full | 12 | 0 | 0 | 9/12 | 11/12 | 8/12 |
| adapted_snapkv | 12 | 0 | 0 | 0/11 | 0/11 | 0/12 |
| uniform_random | 12 | 0 | 0 | 3/11 | 2/12 | 0/12 |
| adapted_snapkv_system_pinned | 0 | 10 | 2 | 0/0 | 0/0 | 0/12 |
| uniform_random_system_pinned | 0 | 10 | 2 | 0/0 | 0/0 | 0/12 |

Snap1条截断，random1条虽未截断但候选无string answer，任务EM/F1为N/A；不以低评分、截断或解析失败删除记录。两保护方法各10格预算不足+2格工程证据不足，0生成/0可评估；表中0/0没有成功率含义。旧4条保护诊断不借来打分。全60格实际经过dispatcher，其中36调用模型，24阻止；预算、证据、执行和指标分开留档。

统一报告由新文本调用固定task scorer得到EM/F1/格式，再由公共scalar core汇总。完整JSON不替代任务正确；截断和指标N/A按严格可比较分母排除，保留Full正确损坏上下界/未评估数，joint按所有12计划格报告。core历史元字段由本次runner明确标inference_performed/task_text_rescored=true。peak/阶段时延/额外buffer成本未测仍unknown，不把半prefix KV当整个进程显存减半或吞吐收益。

## 独立回读与证据

独立纯标准库verifier未导入模型、编排或项目旧scorer：48固定输入及执行源码SHA不变，恢复evidence等于原记录、8软件case结果通过；36请求/input/runtime绑定、raw/dispatch/新旧token/终止/文本/评分全部一致。用另一份独立JSON候选提取及EM/F1实现重新判36文本，与新scorer/旧同格指标全同；没有抄旧summary当计算。

独立1115位置trace步递推、2688唯一层-head映射、1344Snap排名、12score/24map与原冻结工件核验；全60规范记录的执行覆盖、每指标可评估分母/均值/F1、配对转移、Full正确/未知分母、损坏上下界、joint逐例重算通过。4个自有PID退出，GPU1收尾15MiB/0%。本轮原始score/map/ids/text/日志均未拉回本地。

v2原manifest77项，后验不覆盖原manifest；最终82文件1928933bytes。重要SHA：

| 工件 | SHA256 |
| --- | --- |
| manifest.json | 412fbe241d72b668c6b2a1dd3ca1b207c2054afbe7bf3f737c2c42c8fe81bedd |
| summary.json | f1173e60d48fb3d39d64bffa3677298745e1894b117e4068a0225767e843166a |
| actual_runtime.json | 6ca456e0cf5b89ef660434c6c71f18cb87e40a8c30b1a2a396d9ea1b49e0a851 |
| execution_scope.json | c3e8d8a37cfb8e2b1d4287f32898ba2264a63a2226c4a78bedaf9804acf65826 |
| resume_provenance.json | 9da42ea14547924e412102680ff167bc1989ae10a248a7045110b16367f6aeaa |
| restored_engineering_evidence.json | 7ca977f2f221f752d26dbcf2b1984046e07197a1a5d1ba4c7dba0418f8bc3a27 |
| config_JSON_comparison.json | 9e444ad16d3b38c50e898053ae44d665f7f7d4796ec8b50942d24d49a0de024d |
| raw_generations.jsonl | ace314be4f7207b5f34313133ccc0106381b514ae360e7cdd6b1db6aef057018 |
| scored_generations.jsonl | 5da88a2999e037ba234d1416700bdd5ad65b7d938006c385d489639e0cc4b589 |
| admission_plan.json | 98afa8adc74f96c35aa2fddf045f48a457e14168586f2807114a417749d85afa |
| normalized_records.jsonl | d5581cf50e29f63b63df884407dfe139e2ecf9a84ec771e5920e5d322972439d |
| report.json | 054d54673e74b4b7c96906f3b80a5ccaf31b998a87906b4bd642c232187916f4 |
| independent_verification.json | 0d7db8f9cee91c1ea816d66d0d125a661283e1bedb42f8d3da3faf10427a8dc1 |
| closure.json | 4df2986a0f0ce97607a029cd08f4fd7a1643cac5a7cfeeb6c1992ad63c7e526d |
| derived_manifest.json | 29b260b833b48204cfe417c6c21d0f81e540d5eff45324122143405f618a050d |

六个同级launch/console/launcher hash及失败工件完整索引见[readiness](../HF_DEV_ACCEPTANCE_READINESS_20261030.json)。

## 解释与下一步

系统主链已打通：有来源的工程恢复、准入、实际调度、双判分和统一60格报告在固定模型/输入范围内通过集成验收。保护仍未验证；单模型/同12DEV/短原段落、公开数据可能预训练见过，不能作为独立科学确认、算法创新、安全或性能结论。v1工程误报如实保留，v2不改变科学判据。旧QA gate=false及既有输出/失败不改，封存未访问。

停止重复当前12DEV与14工程回归。下一步离线收敛系统验收矩阵与独立实证协议，明确任务/来源覆盖、Full支持、预算可行性和第二模型所缺证据，再决定新的有界GPU协议；BoolQ403来源和跨任务最终划分仍待解决，不直接扩封存/预算/提示搜索。

新增2run（1failed/1complete）、36主/0工程，累计112run2888主；当前索引 `results/20261030-run-index-hf-DEV-acceptance.json` SHA `743ee5444d9e41414d017dae54c978f73e63f6ce246adb9948112a685ada8de1`，旧110/111run索引保持。STATUS/WORKLOG/HANDOFF/PLAN与系统readiness已更新同步，源码配置文档两端逐SHA核对，GitHub未配置未push，依赖/环境无变化，当前无运行任务。


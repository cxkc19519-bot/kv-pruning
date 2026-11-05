# Mistral当前QA Full-only：工程通过，支持门槛失败

## 实验身份

2026-10-30，Asia/Singapore；用户“继续”，沿已明确授权的实验会话按[执行前协议](../MISTRAL_SQUAD_FULL_PROTOCOL_20261030.md)执行。服务器绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-mistral-squad-full-v1`。问题是已有Mistral固定权重能否在当前span-QA/JSON任务上通过真实Full KV工程与任务支持；不是新算法、压缩/保护/安全或独立上下文确认。

状态：**run完成exit0，工程门槛true，Full支持false**。6工程+12DEV主回答，共239新token；零错误/截断，未启动压缩、保护或封存。能力门槛失败不是运行异常，也不证明模型一般不会QA或整个研究方向无效。

## 可复现条件

固定[proposal](../../configs/mistral-squad-full-v1.json) SHA `217d320431dd9a21441d27b37d773ab2e2a303de0dfbe981c1e28bb9c849f688`，runner `cdec42ae81cb7f6d8aa5cd9771c37a1d524a21069392badc728110422677700e`，独立verifier `77cf7cd24302f895103d8ca47f080786801ece21558159ab8eedb213e4dfd235`。源码以逐SHA快照标识，未配置Git远端；不复制nano-vllm，也未把Qwen28/4常量当Mistral布局。

沿既有Mistral-7B-Instruct-v0.3 revision c170c708c41dac9275d15a8fff4eca08d52bab71和原13文件官方清单，模型路径models/Mistral-7B-Instruct-v0.3/c170c708c41dac9275d15a8fff4eca08d52bab71。加载前完整校验3个权重SHA、10metadata官方git-blob/LFS与前端SHA；独立回读再次流式核全部13文件。模型/数据/环境/原始日志只服务器，无下载/升级/remote code。

现有Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1/safetensors0.6.2/sentencepiece0.2.1/protobuf6.33.0不变。真实32 Full Attention层、32query-head/8KV-head/head128、BF16/SDPA、无滑窗；实际每层K/V形状(1,8,n,128)，总131072bytes/slot。新入口独立实现Full prefill/clone/native/custom，未将其称为已接入通用压缩后端。

原两工程case 56f991b19b226e1400dd15b8、57280cfc3acd2414000df323及原12DEV，Mistral原生INST折叠system/user、prompt/gold/完整ids/prefix沿CPU预检逐项相等。其余2工程和48封存不入模。所有题保留，不改提示、长度、gold、seed、输出格式或样本。

fresh GenerationConfig：greedy/max_new_tokens128/rep1/num_beams1/use_cache=true，EOS2/pad2/bos1；torchseed20261030，TF32和BF16 reduced precision reduction关闭。GPU物理1 UUID4ce22e12-b5c0-e423-06c5-e858bb71daaa/RTX4090/驱动580.178.04，进程内cuda:0；初查/加载前核≤128MiB/util0，独立收尾15MiB/0%，未操作他人任务。

实际命令由固定离线env、UUID及KV_MISTRAL_FULL_WATCHDOG=registered_660_seconds的外层launcher运行：

```bash
.venv/bin/python -u scripts/run_mistral_squad_full.py --execute --proposal-sha256 217d320431dd9a21441d27b37d773ab2e2a303de0dfbe981c1e28bb9c849f688
```

内部600秒/外层660秒/TERM后20秒仅自有进程组、12主+6工程/2304token、64文件64MiB上限。实际UTC 2026-10-30T13:24:03.286581+00:00—2026-10-30T13:25:30.029089+00:00，worker999238内86.049380秒、launcher999235共86.742325秒exit0；时间含完整权重hash/load/审计，不当推理性能。watchdog未触发，两个自有PID退出，无服务/端口或后台队列。原始token先append再核KV/判分，异常不会丢掉已生成回答；单次v1，无失败重试。

## 结果与证据

工程两题各native整段、native缓存分段、custom缓存分段共6次，逐token与termination相同；6条均完成。原reference内容hash在所有分支不变，clone独立地址/逐tensor相等；实际prefix与最终live K/V字节按元素观测匹配，custom trace保存Full物理=逻辑递推。native整段没有保留内部cache，prefix/final字节null，不把估算记实测。参考hash只用于验证，未改变prefix或选择任何KV；本轮没有选择map/scoring hook或压缩。

| 预先固定项 | 观察 | 门槛 | 判断 |
| --- | --- | --- | --- |
| 两题三生成路径 | 6回答逐token/终止一致 | 全相同 | 通过 |
| DEV任务EM | 7/12 | ≥6/12 | 达标 |
| DEV格式合规 | 8/12 | ≥9/12 | **未达标** |
| DEV截断/运行错误 | 0/0 | 截断≤1、错误0 | 达标 |
| joint完整交付 | 6/12 | 单独报告，无新阈值 | 描述性结果 |
| Full支持关卡 | false | 所有支持条件同时满足 | **停止本适配裁剪** |

全部12DEV未截断、任务候选均可评估，无N/A；EM/F1与格式分别计分，不能把未合规输出重解释为合法对象。4条格式失败都是json_string，即模型输出一个JSON字符串，而不是单key answer对象。其中1条候选任务EM正确，另3条任务错误；这再次区分格式与内容，但本轮没有因压缩导致该变化。后验分类仅汇总已保存reason，不重新评分/改门槛或修正输出。

工程三路径长度分别12/12/12及11/11/11；12DEV生成长度6–32（含EOS）。共同runtime digest `9f045ed0e5680200da3841a3bd8eede8633eaf5d3d610ad29ce9f9769608af64`绑定实际模型/config/版本/完整generation defaults。所有主记录和scalar report包含真实输入/gold/runtime identity；当前Full-only报告12cell，task/F1/format适用分母及unknown成本保留，inference_performed/task_text_rescored=true。

## 独立复核与归档

纯标准库独立verifier不导入模型/runner或项目scorer，复用另一份已固定独立JSON候选提取与EM/F1定义；18文本重新判分，raw与eng/DEV保存记录逐项对应，12scalar指标/均值/分母、Full阈值和输出计数独立重算。193个custom位置trace步和所有split实际prefix/final字节递推通过；两工程case三路径相等，reference与输入/运行指纹一致。12固定输入/4运行source保持，3权重完整SHA及10metadata另行再核，独立结果passed。

peak allocated/reserved、额外buffer和同步推理时延未benchmark，报告unknown，不能以131072bytes/slot或总wall声称性能/显存优势。实际正常任务成绩如上，安全能力和压缩效应本轮不测。console的torch_dtype弃用提示保留，未在固定run中改参数/依赖。

原manifest21项，后验verification、格式分类、closure、derived分别追加不覆盖原；最终26文件166502bytes，另同级launch/console/launcher。重要SHA：

| 工件 | SHA256 |
| --- | --- |
| manifest.json | c1a377ba7f9ad7f9f40ef6f2f17622fee3c23ab5eda0fc59f1dfd094f509af21 |
| summary.json | f53c13909ae0266f010ab0351664f5fce615979a0c7864229bbb29ef4a6a62b5 |
| actual_runtime.json | 5ac79b7866654f491e94fad6e9d124243c436b6201375f7af1ec7b63df2e201c |
| execution_snapshot.json | 3a7beea93dc774e2c33812d82548387b8eea7ff1ae98d6f2f0a9abaf746c26db |
| model_file_verification.json | 633b6173ab7385ac78e70003734d2957eb9484e54b652f0595482fab5cdb0df4 |
| input_bindings.json | 2475a7294fcd6100d6a7880d9113a4b13728a4e0fc53919a9cdd94082e846eae |
| raw_generations.jsonl | 81c4febf5b6f62f67ab208001a50d84e40e2187d5de7513586b1e91fc2d3be37 |
| engineering.jsonl | a458675c174f00287a21cde59d684946278188e71d12c6a8f6585a20678caad3 |
| generations.jsonl | 00a9adfed40bc25e33989c67d96379cad2406b41b48eeaf51091410feb5aaf4d |
| engineering_checks.json | 3ae1c2d40dd13edf323c13d44cc96b38528994b3c840e856edf21eb7f1fef98a |
| Full_support.json | cc6ef38a2f7c0619a33a55b365dbbd539bc8565e22f7c1f18b97116ed59cccdd |
| normalized_records.jsonl | 2aa494a5105fbf655f9ad21dcc9ffa341e6b6217474a0ba2440cc0c55a4f4bba |
| report.json | cdf3c3f28162ec6a0b83e3967348063a85fb2f1c7e06a419267a7b8b748c20fb |
| independent_verification.json | e3f9620f3c2e2cea80ad08e3ac052fbad1bd60085ecaa11db9f291e0c28c26c1 |
| format_failure_categories.json | a5b5621de6ac27d599de0dfc944a3985236783ea97186581a9c7dd752408c664 |
| closure.json | b0712a0a277140c58f3596340dbb44e6d46f7d8d38e8cc06e2459beb4f0847da |
| derived_manifest.json | a89887e69f52281245ed9e22b473982032c4a4e73be0539a5fadb33ce0c69d96 |

同级外层工件hash见[readiness](../MISTRAL_SQUAD_FULL_READINESS_20261030.json)。完整原始数据/回答/模型元数据与日志仅服务器，源码配置文档同步服务器核SHA，GitHub未配置未push。

## 解释、停止决定与下一步

直接观察：当前固定原生QA适配上，Mistral真实Full布局与三路径可复现，但格式支持8/12低于冻结9/12门槛。**该适配的压缩/保护/封存队列停止**。不把json_string放宽成格式正确、不换提示/模型/题目或重生成4条错误来救回，不以“只差1条”取消关卡。旧权限Mistral门槛与旧QA false也不改。

本次12DEV与Qwen共享同文章组，模型native wrapper/tokenizer不同；只能称开发适配支持边界，不能归因为模型权重的单独因果影响，也不增加独立context证据。当前仍不能宣称第二模型压缩验证完成，3/4预算数学可行不等保护路径通过；BoolQ403/替代分发缺title及48封存保持。系统链范围内验收仍有效，科学证据缺口需如实保留。

下一步转为离线收敛：把两模型任务支持/预算覆盖和仍缺的独立证据整理成最小可行研究范围，决定如何缩小主张与后续证据优先级；不继续模型/提示搜索，也不自动开启Qwen新预算/封存以追正结果。任何新独立实证需新的有界协议，当前无GPU队列。

新增1run、12主/6工程、239token；累计115run2900主（非独立样本量），索引`results/20261030-run-index-mistral-squad-full.json` SHA `d2673f944eddab9c4a43568fe327705e0f63bb0786234d0eed6544d2f94d2c0a`，旧114索引保留。STATUS/WORKLOG/HANDOFF/PLAN及系统矩阵/readiness更新，环境/依赖无变化，当前无运行任务。


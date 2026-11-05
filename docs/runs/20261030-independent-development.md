# 新来源DEV与系统可交付性：失败来源、数据验证和真实KV小试

## 实验身份

2026-10-30，Asia/Singapore，用户再次要求“开始做系统设计与实证”，沿已有实验会话授权推进。服务器绝对根`/home/user/jhk/project/Directional Exploration/kv-pruning/results/`，本轮七个目录如下。原始数据/答案/日志只服务器，本地仅代码、配置与文档。

| run后缀（共同前缀20261030-） | 状态 | 秒 | 主/工程回答 | PID |
| --- | --- | --- | --- | --- |
| independent-source-discovery-v1 | failed：官方GCS元数据HTTP403 | .781412 | 0/0 | 912453 |
| independent-source-public-head-v2 | failed：同官方对象公开HEAD HTTP403 | .937753 | 0/0 | 912871 |
| independent-task-preflight-v1 | complete | 8.428507 | 0/0 | 913805 |
| independent-squad-tokenizer-v1 | complete | 1.326967 | 0/0 | 914828 |
| independent-squad-full-v1 | complete，Full支持过 | 27.361655 | 12/6 | 915363 |
| independent-squad-compression-v1 | complete，含不可行cell | 53.794911 | 28/8 | 916500 |
| independent-development-analysis-v1 | complete | .029474 | 0/0 | 917466 |

新增7run，保留2个失败；实际40主+14工程=54回答/1767tokens（主1162、工程605）。另有20主/4工程条件预算不可行，未生成回答，不能计入实际输出数。累计107run2852历史主输出，统计单位仍是本轮12开发文章组，不是累计run或回答数。

## 来源检查与计划修订

BoolQ作者固定README指向`boolq/dev.jsonl`。先在独立v1中对官方GCS JSON metadata API发1次GET，403后停止该run并保留失败；随后另冻v2对同作者bucket/object的公开media端点发1次HEAD，同样403。未改认证、未取数据正文、未尝试镜像或自动重试，不据此断言数据永久私有或普遍不可用。BoolQ源对象版本/正文SHA与跨任务分组仍未就绪。

继续已规划的另一来源SQuADtrain，先通过CPU预检，再在**新模型输出前**冻结[开发阶段修订](../../configs/independent-squad-development-amendment-v1.json) SHA `e19913a62ec016d5e6478f6c2336dcfbe0fe61c7e1469f8425f4b857a44c51ee`。仅允许新SQuADtrain12DEV及前2工程题；这不重写数据准备run的`model_inference_allowed=false`，而是另立开发适配执行协议。原计划BoolQ优先改为SQuAD开发优先的原因是来源阻塞，不是模型结果；仍不称跨任务最终划分或独立科学确认。旧QA false关卡、旧封存16全部保持，新封存48也无推理。

SQuADtrain从固定作者commit e0c66cfec263165fb3c15cb76a22175e371b71d7下载，30288272bytes、Git blob77f1d9a7daee11f7bc293832020f7709f63410ad匹配，SHA256 **`3527663986b8295af4f7fcdff1ba1ff3f72d07d61a20f487cb238a6ef92fd955`**。原始442文章、18896段、87599唯一问题/答案；每条参考答案offset与原文逐字一致。单次固定GET，无重试/redirect，90秒/40MB下载/80MiB归档上限，软件BoolQ20用例先执行，再下载与全量检查；无模型/GPU/依赖安装。

新BoolQ gold-blind软件适配器只接受完整bool字面或预定yes/no/true/false映射，格式必须恰好单key JSON boolean；false不是缺失、numeric1不是true。重复键/NaN/结构歧义/额外解释不扫描gold补分。20个输出前固定的正负用例全部通过，**不代表官方BoolQ数据或模型能力已验证**。

## 抽样、原生前端与预算

沿固定标题/规范段落连通分组，排除历史整个SQuADdev48文章的标题/段落重叠。独立两两图+DFS复核442组件均合格，无历史精确重叠。按新seed`kv-reliability/new-source/v1\0`排序组件，每组从所有原问题中按id hash选1题，**不取最长段落**；预留工程4、开发12、封存48。未来BoolQ必须排除这64组的连接重叠后再锁定跨任务划分，不能利用DEV输出挑BoolQ题。近义改写和预训练污染未排除。

`selected_provisional.jsonl` SHA `20f45408aa11db0848f65b0ca2fb4c096af0d4bc05840ab917dac8f208b846d1`，仅前2工程+12DEV进入原生前端/模型；另外2工程与48封存不推理。新CPU前端36次编码、14case，原生问题边界无跨token，替代工程问题prefix hash不变。完整system含模板边界56token，sink4/recent64并集120槽位；prefix146–312、半预算73–156。

**工程2题与DEV10题的半预算均小于120，完整保护不可行。** 这一结果在模型输出前已知；修订协议规定记infeasible_budget，禁止提高保留率、减锚点、只保护部分规则、填充或换题。DEV其余2题prefix312/311、预算156/155可容纳。不可行不是推理错误，也不是语义回答错误。

## 模型条件与工程验证范围

既有Qwen2.5-7B-Instruct a09a35458c702b33eeacc393d103063234e8bc28，原`.venv` Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1/safetensors0.6.2；两GPU run分别逐SHA核验4权重shard，无新模型/依赖下载。实际28 Full Attention、GQA4、head_dim128、BF16、SDPA、57344KV bytes/token。UUID固定GPU1，加载前18MiB/0%，没有操作其他GPU任务。

本小试沿固定项目原语默认random seed20261028，key为context_group_id；正式草案的三seed矩阵未执行。fresh GenerationConfig覆盖模型采样默认，greedy、max_new_tokens128、beam1、repetition_penalty1、EOS[151643,151645]，TF32关闭。新Qwen专用driver从旧项目脚本独立版本适配到参数化token上限/12题及不可行状态，旧脚本未改；不是nano-vllm代码，也不称跨模型通用运行壳已完成。

Full两工程题三路径共6答逐token一致，hook off/on prefix K/V逐值相同；12DEV答案EM9、格式11、joint8、无截断，固定支持量≥6任务/≥9格式/≥6joint/≥11候选通过。

压缩工程只有无保护Snap/random的2题×2路径共8答可执行，native/custom token与trace一致；两个保护条件×2工程题的4格均不可行。runner中的总`engineering_gate=true`只表示**已执行的适用路径通过**，不代表保护方法的工程路径已测；分析明确写`protected_engineering_paths_verified=false`。因此保护DEV中仅2题的输出是开发诊断，不能据此宣布保护路径独立验证完成或方法总体可靠。

## 主结果与全部计划格

| 条件 | 实际执行 | 预算不可行 | 任务EM正确/严格可评估 | 格式通过/严格可评估 | 联合交付成功/计划12 |
| --- | --- | --- | --- | --- | --- |
| Full | 12 | 0 | 9/12 | 11/12 | 8/12 |
| 适配SnapKV | 12 | 0 | 0/11 | 0/11 | 0/12 |
| random | 12 | 0 | 3/11 | 2/12 | 0/12 |
| Snap+system保护 | 2 | 10 | 0/2 | 2/2 | 0/12 |
| random+system保护 | 2 | 10 | 1/2 | 2/2 | 1/12 |

Snap有1条128token截断，raw候选仍保留但严格指标不可评估；random有1条结构输出没有字符串answer、未截断，因此任务N/A而格式可判。均不按语义错或安全成功补值。每保护条件的10条不可行是无输出，任务/格式均N/A；不能把剩下2/2格式通过报成总体100%成功。

联合交付定义为固定预算内产生未截断且任务/格式都通过的输出，分母始终12；不可行无交付，但语义分仍未知而不是false。三类分母（全计划、实际完成、指标适用）均在报告分别保存。60计划格全部保留，实际40答与20不可行相加，没有挑成功子集。

这不是与旧最长段落DEV的随机对照，来源与样本同时变化，不能把效应变化归因于单一抽样规则。不过，本轮明确说明固定完整保护与锚点占用会在较短输入下直接限制可运行覆盖；系统应在加载模型前给出此准入结果，并在策略比较中保留覆盖成本。

## 独立核验与工件

外层不导入新准备/报告模块，以独立图+DFS重新构造442文章组件、rank/选题/role、原文/gold/提示和全部87599 source slice，通过。模型阶段逐层gather与原KV指定位置逐值一致、reference版本不变；后验另核3584个head map的唯一/排序/预算/保护与适配Snap排序，14组Full/压缩score gzip逐hash一致，40主答prefix/最终KV字节及逻辑/物理trace一致。统一核心输出60唯一cell的bool/连续分、四转移/Full分母/未知覆盖范围独立Counter重算通过。

| 工件 | SHA256 |
| --- | --- |
| 数据准备原manifest | 67f53261e8cf318f5bd9b6b7a2ee8caae29b21efa45165203487614dd663a945 |
| tokenizer原manifest | 3adb1917dc4cd0f673fbaa93b81c72872f56ef7396ee987e1353ec489a22d832 |
| Full原manifest | 769c196352e418b946e3927c4be5042cbfaf3ff426332d5b178b580537a07177 |
| 压缩原manifest | 68d3d0750bc0cb00553510a34168b572d50d61416922af5543e235a6c3d7a1e1 |
| 分析原manifest | ab10c85a63fa540bba4a3ec24454386b5d9376d83586d0d304857ca28dd034c1 |
| 分析report | d6852baf3f0a6f7720d65ffcd0c9cd0813bd53d8988f278e195112bbd63db2f8 |
| 分析独立verification | 191f736564348c51706edb5e1018e485b786a1451b2455d02a1d0818f04ed656 |
| 分析closure | c8c3e97b09a7fa41849c67d8f1fe03d987c494e113fdb21cf79c9b0e33189677 |
| 分析derived manifest | 0bba1cac90f0f76ec00f9a117785c6a00952ffc2a1e1b0c33380d711cdd00984 |

原manifest不追写后验，derived另覆盖后验文件。七run合计约33MB，外加同级launch/console；全部原始只服务器。新索引`results/20261030-run-index-independent-development.json` SHA **`a1e120d953c73f159af4a1c07b678c8b599ba0406365a31d9e215d8d65db9969`**，旧100run索引不变。所有旧归档输入/复用源SHA保持。

实际历史命令（已执行，不是重跑待办；既有run拒绝覆盖）：

```bash
.venv/bin/python -u scripts/discover_independent_source.py --execute
.venv/bin/python -u scripts/head_independent_source.py --execute
.venv/bin/python -u scripts/preflight_independent_task.py --execute
.venv/bin/python -u scripts/preflight_independent_tokenizer.py --execute
.venv/bin/python -u scripts/run_independent_squad_model.py --proposal configs/independent-squad-full-proposal-v1.json --execute
.venv/bin/python -u scripts/run_independent_squad_model.py --proposal configs/independent-squad-compression-proposal-v1.json --execute
.venv/bin/python -u scripts/analyze_independent_development.py --proposal configs/independent-development-analysis-v1.json --execute
```

四来源/CPU stage内部墙钟30/30/90/90秒；Full600/compact900秒及回答上限均未超，分析outer60秒。launcher与源码/配置snapshot/输入hash保留。运行wall含权重hash/加载/审计IO，未测生产式峰值、纯推理时延或吞吐，不将半prefix字节当整进程显存减半。

## 收尾与下一步

七个自有PID全部退出，GPU1收尾18MiB/0%，其他任务未操作，无新依赖或持续后台服务。系统设计/实证已经落到新的来源与真实模型DEV，不是只写计划，但仍限开发与工程诊断：跨任务分组、BoolQ实际来源、保护条件工程路径、第二模型和科学确认尚未完成。

下一步先把**每条件预算准入与工程证据范围**接入统一执行接口，不能让一个总pass掩盖未测的保护路径；以现有不可行样本做只读验收。BoolQ来源保持暂停，先核有明确作者/基准来源的替代正式发布版本再注册，不能偷偷使用镜像。后续独立/第二模型/新预算实验须新协议，旧48/16封存不自动运行。当前没有运行任务。STATUS/HANDOFF/WORKLOG/readiness及根环境同步服务器，GitHub未配置未推送。

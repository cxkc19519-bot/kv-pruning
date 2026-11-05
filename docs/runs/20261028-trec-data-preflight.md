# LongBench TREC数据CPU预检与32题上下文能力关卡准备

## 实验身份

- 2026-10-28，Asia/Singapore；用户“开始下一步”，执行上轮交接的官方TREC数据CPU预检。未加载模型权重、未推理、未裁剪，未复制nano-vllm。本地仅代码、配置与文档。
- 服务器绝对根：`/home/user/jhk/project/Directional Exploration/kv-pruning`。本轮结果：`results/20261028-trec-data-preflight-v1`（服务器网络失败）、`results/20261028-trec-data-preflight-v2`（CPU审计完成）、`results/20261028-trec-context-gate-data-v1`（32题准备完成）。
- 目的：固定真实长上下文数据、原生前端和可判分能力控制，不证明安全特异性或新算法。数据通过后，另存一份**尚未执行**的64输出有/无示例校准提案。

## 可复现条件与来源

- 官方数据仓库旧`THUDM/LongBench`重定向`zai-org/LongBench`，固定[提交5e628be450b7e67fb7ae6e201bd6d8f7056f7672](https://huggingface.co/datasets/zai-org/LongBench/tree/5e628be450b7e67fb7ae6e201bd6d8f7056f7672)。这是HF数据提交，与上轮GitHub源码`2e00731f8d0bff23dc4325161044d0ed8af94c1e`分开记录。
- 固定`data.zip`为113,932,529bytes，SHA256 `cb45b11a4133c6bc1d6a44b0f8e701335ff1e543195db1103472e575857f7f64`，与HF metadata的LFS摘要/大小一致。归档保留，只解出`data/trec.jsonl`，不混入trec_e；TREC 6,360,293bytes/200行，SHA256 `20a88e14f7442f58a39082cdd7396f1093ea8162da0a4ea7ead7d6757514c8f4`。逐行原始SHA、原_id和0起始源行均保存。
- metadata、README和LongBench.py亦固定存档，后两者Git blob与metadata匹配；只对loader做AST，不运行远程dataset脚本。保留上轮固定的LongBench prompt/metrics/eval/pred/README/LICENSE及摘要。
- GitHub代码MIT、HF loader Apache头保留；HF卡片没有统一dataset license字段，不把代码许可冒充全部衍生数据的许可。官方卡片说明TREC为原始训练集few-shot示例＋验证/测试问题，并引用[原TREC论文](https://aclanthology.org/C02-1150/)。本轮未发布数据、不声称完成全部原始数据语义/许可审计。
- 服务器直接curl官方HF API失败（curl28连接超时），v1 manifest/headers/stderr/实际命令和bootstrap保存。改用本机可达的同一官方固定地址：Windows curl stdout经二进制内存管道直送SSH stdin，在服务器写part后验大小/SHA再rename；本地无数据/压缩包文件，未用第三方镜像。114MB ZIP传送约26.58秒，仅为下载记录，不是模型性能。
- 复用现有Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28` tokenizer，五个config/tokenizer文件SHA冻结。Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1不变，未安装依赖，CUDA未初始化。28层Qwen2 Full Attention/GQA配置沿已有审计，BF16每prefix token 57,344 KV bytes是按配置计算，不是本轮实测。

实际传输命令（Windows项目根；每文件直写服务器v2）：

```powershell
./scripts/stream_hf_to_server.ps1 -Name hf-metadata.json
./scripts/stream_hf_to_server.ps1 -Name README.md
./scripts/stream_hf_to_server.ps1 -Name LongBench.py
./scripts/stream_hf_to_server.ps1 -Name data.zip
```

实际CPU命令（服务器方向目录）：

```bash
.venv/bin/python scripts/audit_trec_data.py --run results/20261028-trec-data-preflight-v2 --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --upstream results/20261028-systemcheck-source-audit-v2/semantics/upstream/longbench/LongBench
.venv/bin/python scripts/prepare_trec_context_gate.py --data-run results/20261028-trec-data-preflight-v2 --out results/20261028-trec-context-gate-data-v1 --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
```

源码SHA256：传输`56336ea0c0ce9c0b29191cafabf5d15bc43e839ac727996e48a123df87e83042`；数据审计`1917d2444b11177c052f99759766b9a3cab0b96e6d8eb035fdc83eebdbd11e00`；队列准备`e4213155ca28edf22aee61be4091fd689f39f9e5804997f103d68ba65099f3c2`。各保存同版本快照。已完成目录不可覆盖；复核须新建out/run、固定相同官方字节。

## 结果与证据

第一步前端仅将原任务header＋原context放system，原input放user，是相对user query的query-blind角色改编；不称官方flat completion原前端，不做中间截断或padding。

| 全部200题CPU结果 | 数值 |
| --- | --- |
| 原_id / 问题唯一数 | 200 / 200 |
| system prefix token最小/中位/P90/最大 | 1886 / 6911 / 10650 / 11474 |
| user＋assistant suffix token最小/中位/最大 | 16 / 20 / 28 |
| 原始flat prompt token最小/中位/最大 | 1893 / 6918 / 11482 |
| 每题示例数最小/中位/最大 | 100 / 361 / 596 |
| prefix1024–4096 / 1024–8192 | 44 / 127题 |
| schema/gold在标签表/示例边界/原生拼接检查 | 全部200通过 |
| 标签表 / 实际gold覆盖类别 | 50 / 35；分布不平衡 |

- 71,409个示例出现位置来自5381个不同问题；所有示例问题在多个context重复，不能把所有示例或所有模型输出当独立样本。200个context无全文重复。
- 同一示例问题“What is the chromosome number of an elephant ?”对应Number of something与Other number两个标签；全数据28个context含该问题，其中2个context内部同时有两标签。原始记录保留，不就地改标注。
- 1题目标问题在自己的context示例里出现；4个测试问题可在其他题context出现。后一种跨context出现不等于该次输入含答案，逐题情况单列，不把两者混计。query彼此无冲突标签。
- 这是结构/一致性审计，不保证全部自然语言gold在语义上正确，更未证明模型必须依赖示例才能答题。官方英文length为词数，不能代替本轮token计数。

### 32题准备与判分CPU检查

- 在无任何模型答案时制定新短规模选择：源角色改编prefix1024–4096、不含本context冲突标签或全局歧义示例问题、目标问题不出现在自己的示例中；按SHA256(`20261028:trec:`＋原_id)排序取前32。44个长度合格中最终42个可用，选32；全部排除理由及未选候选保留，不按模型表现挑题。长度选择服务单4090小控制，不能代表全部TREC长度。
- 另立显式前端：相同50标签列表＋“仅返回一个标签”的输出指令，两条件均固定；with_demos保留原context，without_demos仅移去context，user query/gold逐字保留。这是新的能力前端，不是上一步header或原论文原版。
- 32个source key、两条件完整messages/ids与SHA、原行/原context摘要、gold在服务器`cases.jsonl`冻结，SHA256 `e709d4bd298cd61a272f42835a180c7ac032b450b0aa1c40892814c7f6c8caf7`。with_demos prefix2069–4182、without_demos prefix205；32对suffix ids完全一致，附加输出预算64后均小于8192。覆盖18个gold类别，不能给稳定的50类排名。
- 两条件输入长度和query逻辑位置不同，这是移除示例的联合干预，不是等长度内容因果实验、等预算压缩对照或内部机制定位。相同标签表避免把“无示例时未告知标签名称”当作全部上下文收益；仍可能靠常识识别自然类别。
- 对固定官方`classification_score`纯函数AST节点做隔离执行，不import整个metrics模块；保留原函数体，配合原eval首行预处理作为兼容指标。另用完整`response.strip()`检查标签格式与gold精确一致，不取首行/去引号/大小写折叠。8个人工可判正负/边界fixture通过：例如首行Individual＋第二行多余内容，官方兼容分1但完整精确失败；两类并列可得兼容0.5；City可格式合规但gold错误。未执行其他上游代码或模型。

## 独立提案与执行边界

[trec-context-gate-proposal-v1](../../configs/trec-context-gate-proposal-v1.json) SHA256 `6e9c61d13d8a926ed0ce3d338d33642f95ff4aa48e2a014a8804896f65e2f91c`，与服务器队列proposal逐字一致。`execution_enabled=false`，status为CPU已准备、待runner与缓存检查；不能把数据准备称已做能力验证。

- 下一步实现一个有明确输入/源码摘要检查的runner，沿冻结32题，仅做with_demos Full KV与without_demos Full KV各32，共最多64主要输出，BF16/SDPA/greedy/penalty1/max_new64。首3题两输入条件逐一做native整段/native cached/custom cached逐token一致，额外检查输出单列；工程失败须保存并停止，不直接进入主要队列。
- 按完整输出exact统计全部32对C→C/C→W/W→C/W→W，并报官方兼容分、标签格式、截断/error/N/A。这里的“前→后”为有示例→无示例，**不是**Full→压缩。
- 预先固定的描述性最低支持：with_demos至少16/32 exact正确，截断最多3，且至少8对有示例正确/无示例错误；否则保留全部64输出，停止此设置的压缩推进。不替换题、不修提示/换模型/增预算直到过关。这些是小规模可行性条件，不是功效/显著性证明，不代表示例内容的唯一因果机制。
- 这份提案没有压缩方法或安全泄漏支路；未来压缩须另立设计并做等字节/锚点/hook/100%选择等检查。旧IFEval禁用、AccessDenied失败不变；TREC及这类联合评测已有近邻，不作新贡献承诺。

## 收尾

- 本轮3个manifest run（1网络失败、2 CPU准备完成）、0新模型答案；累计53run2460主输出，索引`results/20261028-run-index-trec-preflight.json`。8 fixture与CPU案例不是模型输出。
- 原始metadata/114MB归档/6.36MB TREC、逐题审计、重复冲突、label inventory、prepared cases、判分fixture、manifest/source/console/transfer proof/closure全部服务器；本地仅三个脚本、提案配置和文档。主要输入/source/artifact与tokenizer SHA通过，原IFEval配置未改。
- 本轮无遗留进程/后台/服务/端口，两卡最后各15MiB/0%、compute-app空；无依赖或权重变化，无其他会话进程改动。未测准确率、安全性、实际KV分配或性能。已更新并同步STATUS、HANDOFF、WORKLOG、PLAN、README与本记录。

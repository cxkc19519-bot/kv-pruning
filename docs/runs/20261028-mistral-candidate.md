# 独立Mistral模型族候选与原生前端核查

## 执行前范围

- 2026-10-28，Asia/Singapore；用户“开始下一步吧”，沿用本会话授权，按上轮交接先完成独立模型族的固定候选核查。服务器`/home/user/jhk/project/Directional Exploration/kv-pruning`，本地仅代码/配置/文档，不复制nano-vllm或采用Qwen3.5 Hybrid。
- 仅一个候选`mistralai/Mistral-7B-Instruct-v0.3` revision `c170c708c41dac9275d15a8fff4eca08d52bab71`，官方API当次gated=false/private=false，README声明Apache-2.0。选择理由为独立Mistral架构族、该固定config无sliding window、公开且适合单4090的权重规模、已有Transformers原生实现；**不以模型成绩选择，不假设能力/安全性强于Qwen**。官方README说明无专门moderation机制，此声明不等于实际政策遵从成绩。
- [固定配置](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/blob/c170c708c41dac9275d15a8fff4eca08d52bab71/config.json)：32层/32query/8KV、hidden4096/head_dim128、max_position32768、sliding_window=null、BF16声明。旧Mistral版本/论文的滑窗不能替代此固定config；需要在当前Transformers meta实例逐层检查。
- [固定README](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/blob/c170c708c41dac9275d15a8fff4eca08d52bab71/README.md)同时提供原生mistral-inference和HF system+user例子；本方向选择现有Transformers，不安装新推理引擎或替换模板。两套权重格式不重复下载。
- 本步只获取10个metadata/tokenizer文件约3.3MB并校验官方git blob/LFS摘要，权重3分片约14.50GB只冻结清单，**不下载完整权重、不GPU加载/生成、不进行压缩**。构造meta模型仅检查形状/结构，不证明实际权重dtype/完整性或推理正确性。
- 服务器两张4090起始各15MiB/0%，磁盘约9.64TB空闲；没有现存Mistral权重缓存。本方向venv/Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1沿用，不安装依赖。资源适配仅估算，不称实测峰值或OOM通过。
- 原生template把可选system内容与user问题合在`[INST]`段，不能宣称拥有Qwen式独立角色token边界。保留原system/user内容与顺序，实际完整token串由模型自带模板生成；这种跨模型前端差异必须记录。
- 按原版冻结development/confirmation各24条，仅做最终渲染/oracle/tokenizer检查；message字典须与旧Qwen3逐字节一致。检查`system-only`模板是否可直接当prefix；若不可则在完整原生token串中按query字符offset定位不含query的前缀，验证完整ids无损重组及两个替代query的prefix完全相同。**只验证token化，不声称cached generation已通过**。
- 本轮输出为候选可用性/前端审计与准备好的输入，不产生模型答案，不使用未推理确认集来选择候选。将来模型基线需先完整权重摘要/运行时层检查，再首三分支native整段/native cached/custom cached逐token检查；同一512预算/greedy/penalty1/BF16 SDPA，保留各条件>=95%与同事raw零披露门槛。发展失败不改提示/模式、不开确认；发展通过才运行已冻结确认队列。

## 执行与结果

状态：候选结构与前端审计完成，Mistral固定版本可进入完整权重获取阶段；**权重尚未下载、模型生成能力未知、缓存生成正确性未验证**。本轮仅metadata/tokenizer下载、meta结构和token化检查。

## 实际命令与失败修复

服务器方向根执行，stdout/stderr保存到对应console。先v1失败，补原生依赖后v2复用已校验metadata（再验完整摘要），没有重取数据或改变tokenizer参数：

```bash
.venv/bin/python -m py_compile scripts/audit_mistral_candidate.py
.venv/bin/python scripts/audit_mistral_candidate.py --spec configs/mistral-7b-v03-c170-artifacts.json --out results/20261028-mistral-candidate-v1 --development-data results/20261028-access-data-v1 --confirmation-data results/20261028-access-confirm-data-v1 --qwen3-reference results/20261028-qwen3-access-dev-v1 --preregistration docs/runs/20261028-mistral-candidate.md
.venv/bin/python -m pip install --no-deps sentencepiece==0.2.1
.venv/bin/python scripts/audit_mistral_candidate.py --spec configs/mistral-7b-v03-c170-artifacts.json --out results/20261028-mistral-candidate-v2 --development-data results/20261028-access-data-v1 --confirmation-data results/20261028-access-confirm-data-v1 --qwen3-reference results/20261028-qwen3-access-dev-v1 --preregistration docs/runs/20261028-mistral-candidate.md --metadata-from results/20261028-mistral-candidate-v1/metadata
.venv/bin/python scripts/check_mistral_candidate.py --run results/20261028-mistral-candidate-v2
.venv/bin/python scripts/index_runs.py results --out results/20261028-run-index-mistral-candidate.json
```

- v1获取10文件共3,310,406bytes，hf-mirror固定revision传输、官方HF git blob/LFS size+摘要全通过，0次网络/摘要失败。结构meta检查完成后，原生AutoTokenizer初始化报`Cannot instantiate this tokenizer from a slow version`。保留failed manifest/原日志/旧source，不标为能力失败。
- 静态核对Transformers4.57.1的LlamaTokenizerFast：官方tokenizer_config含`add_prefix_space=true`，该原生类因此启用from_slow；本环境缺sentencepiece，protobuf6.33.0已存在。没有用from_slow/legacy/add_prefix_space覆盖绕过官方设置。
- 仅本方向venv安装sentencepiece0.2.1 --no-deps，wheel1.4MB；实际模块`/home/user/jhk/project/Directional Exploration/kv-pruning/.venv/lib/python3.11/site-packages/sentencepiece/__init__.py`，安装日志`results/20261028-mistral-sentencepiece-install.log`。基环境和旧nano-vllm未变，未升级Transformers/Torch/protobuf。执行前“不安装依赖”范围因原生缺包作此有记录修复，没有新模型性能筛选或参数搜索。
- v2重新校验v1全部metadata摘要后复用，完成前端检查；随后48条全部HF slow/fast tokenizer的原生渲染、完整ids逐项相同。CUDA未初始化，无GPU推理。两个审计run均rows=0，不能把预编码的48条当作模型回答。

## 架构、模板和资源结果

- meta实例32层均config.sliding_window=None，Mistral模型state名称与固定checkpoint index一致；形状推得7,248,023,552参数元素，BF16参数估算14,496,047,104bytes。**这是meta形状/索引一致，不是实际权重tensor dtype或加载验证。** 保存当前原生modeling_mistral.py及SHA `3fbb6202376a1fdf57166d199dd4d43f81226b1e0634ec8b61dcb1ade7de153e`。
- 原生输入实际为`<s>[INST] ` + 原system内容 + 两换行 + 原user问题 + `[/INST]`；system/user字典内容与旧Qwen3逐项一致，没有改政策或解释要求。API可接受system，但token串没有Qwen式单独system边界，跨模型能力结果会包含各自原生前端差异。
- `apply_chat_template([system])`仅返回`<s>`，不包含system资料，因此禁止把该返回当资料缓存。改从完整原生ids按query字符offset取不含query的prefix；ids无损拼回，全48条各2个替代query的前缀ids与原问题完全相同。没有在prefix引入未来query词语；这只是token化检查，尚不声称cached generate等价。
- development24输入3173–3312tokens、prefix3161–3300；confirmation24输入3158–3315、prefix3145–3300，均留足512预算且低于32768。两队列source ID/目标不重叠、所有渲染oracle通过，没有新抽样或模型输出。
- 新模型BF16 KV应按131072bytes/prefix token计算，不能沿用Qwen3的147456或Qwen2的57344。最大prefix3300估算KV432,537,600bytes；参数+该prefix KV约14.93GB，含再512decode KV约15.00GB，尚不含activations/workspace等额外成本，**不是实测显存峰值/OOM通过**。
- 官方HF清单已锁13文件（10metadata+3个HF safetensors分片）；3权重分片合计14,496,080,928bytes。排除另一个consolidated.safetensors，避免重复下载相同模型的另一格式。现只3.31MB metadata在服务器run/metadata，不存在完整Mistral模型目录。

## 证据、计数与收尾

- 配置`configs/mistral-7b-v03-c170-artifacts.json` SHA `9df15f9d17e9258284cf474a6927f438a520863d424726ea5e735429b68bee58`；v1脚本SHA `a9ce71931685a8d5f1796118de56e85608841d72cf8586cacb404a254a07bea1`，v2新增metadata复用/依赖版本记录后SHA `67b1af23a5756cefaa550a3a077e5b97cccdb4105c430ba7506721c84077cd0c`；独立收尾脚本`c744904269bba83e3c44ad9e5489ad0afc64fc36c528503e1222ff1af30eae5f`。预注册初版SHA `32dd91cecf5fc4f54478d0cbfff0f7fc259ad5a1f05ec0fc92dc808a7c02da4c`在两run内保存，不替换成收尾文档。
- `results/20261028-mistral-candidate-v1/`保留失败与10个metadata；`results/20261028-mistral-candidate-v2/`保存official_spec/metadata_checks/architecture_checks/frontend_checks/development_cases/confirmation_cases/summary/manifest/fetch_attempts/runtime源码及source快照；`tokenizer_crosschecks.json`和`closure_audit.json`保存48条slow/fast检查与源码/来源/metadata/初版预注册输入SHA。全部原始输入/日志只在服务器。
- v1 11.59秒（含下载与缺包失败），v2 5.95秒、收尾约3.21秒，均非推理性能。增加2个manifest run、0主要输出，累计43run2436输出（含重复开发控制，非独立样本）；索引`results/20261028-run-index-mistral-candidate.json`，索引时结果约642MB，旧Qwen3权重16.4GB另计。
- 最后本轮审计/检查PID为空，CUDA未初始化、两卡15MiB/0%；没有服务、端口、后台作业或其他会话进程改动。环境只新增sentencepiece0.2.1，根ENVIRONMENT同步记录，STATUS/HANDOFF/WORKLOG/README/PLAN/协议/文献按远端旧摘要比较同步。

## 下一步固定操作

1. 按已冻结Mistral清单实现/适配下载器，复用已校验metadata，服务器下载3个权重分片；现有`fetch_pinned_model.py`硬编码仅接受Qwen3 revision，**不能不经适配就用来下载Mistral或伪造其repo**。所有文件须官方固定摘要通过，检查实际safetensors头/dtype和层配置后才加载。
2. 固定原版任务消息与本轮准备的native ids，不用上轮精简/输出编辑条件；原生HF BF16 SDPA/greedy/penalty1/512，不传Qwen thinking参数。首三分支native整段/native cached/custom cached逐token、实际131072bytes/token通过后，完成原24条发展评测。前缀使用本轮native完整串切分，不能调用system-only模板当资料prefix。
3. 各本人/同事/缺失仍>=95%严格正确/格式、同事raw零禁用薪资；失败即停止该组合，不改提示/换采样到过线，未推理确认队列继续保留。通过才运行预先锁定新24条确认；确认失败不开裁剪。此处命令设计未执行，不把结构/分词通过当模型能力通过。

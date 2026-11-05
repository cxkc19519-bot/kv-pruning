# 有限UTF-8输入域与无schema工厂正确性检查

## 实验身份

2026-11-01，Asia/Singapore；用户专用实验会话“开始下一步”。自建适配正确性预检，服务器绝对路径：

`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-utf8-domain-factory-v1`

状态：单次执行完成，worker/独立validator/launcher均exit0。新增1CPUrun，非语义接受、性能或资源回收实验。

## 可复现条件

- [有限字符合同](../../configs/utf8-scalar-domain-v1.json) SHA256 `a2e8333fb05ec998c190d3ef31c67a3f41084e775ce20ec8314ae8b4b86c0707`；[执行登记](../../configs/utf8-domain-factory-v1.json) SHA256 `e3eecf0b9d2bd7ba32516e3df612ec586cb8b36ae2da32100761ca19444d26d3`。源码/input/runtime在运行前冻结并检查；每个登记/目录只运行一次。
- 新代码utf8_domain、utf8_domain_factory及verify_utf8_domain_factory。独立validator只用标准库，不导入适配器或作者库；重建字符编号、字节、负例拒绝理由、45条可表达文本与事件时钟。原边界/归档器未改，不重做8项phase、23guard或12observer。
- 有限字母表为U+0000..U+007F，加U+00A2/U+00E9/U+20AC/U+4E2D/U+1F600，按该顺序映射普通id0..132；EOS133，词表134。每个普通token是一个完整UTF-8标量编码，串接133项共142bytes。此域不覆盖全部Unicode、非法字节或BPE的半个UTF-8字符token，不代表真实模型词表。
- 原始257词表/FF冲突保留为失败；本次是全新的有限域合同，不是删除FF后追改旧gate。旧cold5/FF身份/有限语义gate仍false。
- 编码接受str或严格UTF-8 bytes，不做规范化、替换、静默fallback或特殊标记解析。字面文本“<|eos|>”编码为普通ASCII编号，不注入EOS133。EOS显示字节不参与普通文本语言；本次仅核元数据，未测试matcher终止行为。
- XGrammar用RAW TokenizerInfo与stop_token_ids=[133]，再构造一次GrammarCompiler(max_threads=1,cache_enabled=False,cache_limit_bytes=8388608)。llguidance用合成TokenizerWrapper→LLTokenizer(n_vocab=134,eos_token=133,slices=[])；它没有对称的独立通用compiler构造步骤，grammar_from_json_schema/LLMatcher/first-mask全部留在后续请求内。
- 同fresh worker导入Torch/XGrammar/llguidance，设置单native线程、2CPU亲和性，CUDA隐藏且后验未初始化。Python3.11.13、Torch2.13.0、XGrammar0.2.8、llguidance1.7.6及runtime101+dill2不变；无模型/模型tokenizer/权重/GPU查询、安装、服务或相邻项目操作。
- 从父Popen前spawn计30秒覆盖导入与全部适配/构造；适配从import-ready起共用5秒，含合同解析、校验、词表构造、往返检查、可表达性和X工厂。每个调用不重置deadline；这不是每请求语义SLO。launcher/复核/清理总45秒；worker单文件硬上限1MiB、stacks外部上限512KiB、core0，各归档64文件8MiB。只启fatal抓栈，不启周期抓栈或GDB；原SIGSEGV根因仍未知。
- 425个计数调用不含导入（导入另记startup）。全部逐调用事件保留，失败时元数据和单项观测也先落盘。输入快照按序号加basename并保存路径映射，避免同名manifest/verification被覆盖。

服务器项目根内实际执行，仅作记录，不自动重跑：

```sh
.venv/bin/python -I -S -B scripts/utf8_domain_factory.py --execute --registration configs/utf8-domain-factory-v1.json --registration-sha256 e3eecf0b9d2bd7ba32516e3df612ec586cb8b36ae2da32100761ca19444d26d3
```

## 来源和数据

仅文本/AST读取已安装5份wrapper/stub/接口源，均固定摘要。XGrammar的[TokenizerInfo接口](https://github.com/mlc-ai/xgrammar/blob/v0.2.8/python/xgrammar/tokenizer_info.py)及[GrammarCompiler接口](https://github.com/mlc-ai/xgrammar/blob/v0.2.8/python/xgrammar/compiler.py)与此前安装来源审阅一致；llguidance沿已固定v1.7.6/0384f3f6…来源核对其wrapper和stub。Web对一处固定LL wrapper链接cache miss不作为源码不存在的证据，实际采用既有归档和安装文本。

来源档`literature/20261101-utf8-domain-source-v1`为9文件71226bytes，manifest SHA256 `c130edab6a4c977d5ae212a76aeedd82306cac34106c0ac4df11444908ca863f`，全回读，未新增下载数据/环境。

原公共选择仍是8个schema、45个带官方标签的实例，selection SHA256 `41a774b5ae2bc5f43cc0b7ec754ea786491307c562b616b9f36374cb7856d085`。只按原ensure_ascii=true/sort_keys/紧凑分隔符生成文本并检查可表达性，未读取标签来选择子集、改schema或执行接受性测试。

## 结果与证据

| 检查 | 观测 |
| --- | --- |
| 133个普通token | X RAW解码、LL逐项编码/解码及整串133项一致 |
| EOS元数据 | X stop_ids=[133]/special_ids=[]；LL eos_ids=[133]/is_special(133)=true |
| 8个组合正例 | 全通过，含空串、控制符、多字节字符与字面EOS文本 |
| 7个负例 | 原始FF、不完整/过长UTF-8、编码代理项、域外Ω、组合重音、孤立代理项均由适配器拒绝，未新增native调用 |
| 425计数调用 | 所有begin/end、同PID/starttime/TID及不重置deadline通过独立验收 |
| factory | X编译器构造成功；LL仅词表构造成功，schema factory未执行 |
| 原45文本 | 全部可表达，接受/拒绝语义执行数为0 |
| CUDA/最终guard | CUDA false，file/process/forbidden_import/network拒绝均0 |

X与LL的EOS分类差别是接口差别，不是语义不一致证据；本次不比较EOS显示串的文本语言身份，也不以元数据证明EOS实际终止。

从父spawn至import-ready **2.978171168秒**，适配阶段 **0.013625908秒**，launcher总 **3.383386563秒**。这是单次工程观测，不用于速度对比/延迟分位数或真实模型词表性能外推。143次编码回调包括wrapper探针；普通往返和8组合结果均留原始字节/编号。worker关闭后live_ready=false，无可跨PID复用的对象。

唯一只读query PID2271102/starttime428506921，exit0，stdout103903bytes/stderr0，stdout SHA256 `1a3b04fe196649d01c9bd1c03e8cc09fbf8152a638a590c58d989f781fb8dd03`，0.004504827秒。精确/dev/null允许10次，guard和旧库发现边界未拓宽。

- launcher2271059/starttime428506843；worker2271062/428506852；validator2271124/428507180。连同query共4个自有PID事后均不存在，无后台/端口/服务/队列。
- 归档35文件657348bytes，manifest `71ded6bf03b1d6ec4498cf527614fb5a2549f0a43a9aad1a8c0cf08a60633248`；独立verification `50a6e7f35373504918901b867cf4e76bd5d57a385e1394b7e687a7657de2426b`，所有文件回读，source/input/runtime101+dill2不变。
- 服务器closure `results/20261101-utf8-domain-closure.json` SHA256 `5e46673a39d69fb5557d14d772bc150cff48a23800464ed9682dd3079c17d207`。
- 新索引`results/20261101-run-index-utf8-domain.json` SHA256 `cc7cfee887118d1197b60eedc3f0afc7a682d9d6dc15a31b6d36f7cb1d8a4f2a`，累计145runs3038历史主回答；本轮1CPUrun、0新回答，旧失败/索引不变。

## 解释与下一步

新有限域的适配与无schema对象构造预检通过；整体backend_factory_ready/request admission仍false，语法接受性及资源回收效果尚无测量。N1科学可行性/新颖性未建立，H3停止/泛KV暂停保持。

下一步独立冻结并登记原8schema/45标签在这个新域上的正确性验证，保持schema/标签/序列化/顺序不变，记录全样本、错误/unsupported/超时与显式EOS。按134词项重新计算mask存储，不能照搬旧257词表的尺寸/字节断言。LL的schema转换和matcher构造不能提前藏进startup；真实请求5秒的端到端合同与正确性检查预算分别说明，不能将逐调用5秒称为整请求5秒。通过之前不启动资源干扰/取消/性能实验或模型。

已更新README/STATUS/WORKLOG/HANDOFF/PLAN和readiness，代码配置文档同步服务器，原始仅服务器；GitHub未配置未push。

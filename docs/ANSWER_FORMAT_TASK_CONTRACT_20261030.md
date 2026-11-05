# 新任务契约：有答案阅读理解与JSON输出

2026-10-30｜状态：离线设计完成，数据未下载、适配器未实现、软件检查与Full门槛均未运行。后续仅先准备服务器CPU预检，不启动模型。

## 研究用途

采用SQuAD v1.1公开dev资料，保留原段落、问题与全部参考答案，加上固定JSON输出要求。任务正确性与格式遵守分别判分，观察相同实际KV预算下两类损伤、改善与不可评估情况。同预算完整指令保护是否值得其内容预算成本，由未来配对结果回答，不预设有效。

这是项目适配任务，不是官方SQuAD评测、新基准、新算法或安全策略测试。它补足旧TREC严格答案与格式逻辑重合的限制。公开老数据可能进入预训练；文章分组只能避免本项目不同队列共享文章/相同段落，不能证明未见过、没有记忆或语义完全独立。原始单段文本通常不长，本设计只检查初步适配，不代替长上下文验证。

## 来源与版本

- [SQuAD官方入口](https://rajpurkar.github.io/SQuAD-explorer/)及[原论文v3摘要](https://arxiv.org/abs/1606.05250v3)：v1为从段落取答案的阅读理解。使用v1.1，不混入v2不可回答题；论文只读摘要，未声称复现论文实验。
- 官方作者仓库`rajpurkar/SQuAD-explorer`的`gh-pages`固定commit `e0c66cfec263165fb3c15cb76a22175e371b71d7`。`dataset/dev-v1.1.json`的Git blob `e9a3f913ad1468ebe105b891334ca7b0bc0e2510`、4854279 bytes已从树元数据核对；全文尚未读取，SHA256、文章/问题数及长度分布待服务器CPU取回后记录，不能把元数据审查写成数据校验通过。
- 答案分数采用[AllenAI BiDAF作者仓库所附v1.1评估脚本](https://github.com/allenai/bi-att-flow/blob/49004549e9a88b78c359b31481afa7792dbb3f4a/squad/evaluate-v1.1.py)的标量函数定义，commit `49004549e9a88b78c359b31481afa7792dbb3f4a`，blob `0137fbca04cf93b3dbb5744832d25723420a4861`，SHA256 `f5a673dbbd173e29e9ea38f1b2091d883583b77b3a4c17144b223fb0f2f9bd09`。全文已静态读，未运行。它自称official，但本轮未取到原CodaLab bundle，不宣称已验证与该原件逐字节一致；后续报告称“固定BiDAF副本的SQuAD v1.1 EM/F1语义”。
- 作者网站`javascripts/evaluate.js`也已静态读并固定blob；含空答案分支且空白切分等细节与Python版本不同，不能混用或当Python等价性证明。原仓库猜测的四个Python路径404、CodaLab web访问超时，均在来源索引保留。没有执行任何作者代码。
- 官方页标注数据为[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)；未来服务器数据卡保留作者、来源、版本、许可证及“新增提示/选择划分”说明。BiDAF仓库LICENSE为Apache-2.0，与数据许可证分开记录；本轮不将作者代码复制进项目源码，不发布派生数据。详细阅读范围见[来源索引](ANSWER_FORMAT_TASK_SOURCES_20261030.json)。

## 输入与压缩边界

固定system字符串（UTF-8、LF，无示例）：

```text
You answer questions using only the supplied passage. Return exactly one JSON object with exactly one key, "answer", whose value is a non-empty string containing the shortest answer span copied from the passage. Do not include explanations, Markdown, or any other text.
```

user消息由`Passage:\n`、原始context、`\n\nQuestion:\n`、原始question依次拼接。不得重写、摘要、拼入gold、重复规则、拼其他段落或加填充长度。保留全部原始答案及字符offset作为判分资料，模型输入不含答案字段。段落放user而非system；不将可信输出规则与整段证据视为同一保护区。

未来沿Qwen2.5-7B固定原生模板，完整渲染后在问题内容开始前分为prefix与suffix。prefix含system、原段落与Question标记，suffix含问题及原生结束/生成标记。选择器只见prefix，标`query_blind_prefix`；先看问题再选位须另命名协议。CPU本步仅存字符边界，不能声称token切分正确。加载模型前须核对两替代问题的prefix token ids不变及模板/tokenizer版本；分词边界若不成立，停止，不靠分别tokenize后拼接修补。

保护条件只保护完整system指令及其模板边界；sink4/recent64与保护并集全部计入相同实际prefix K/V字节，重叠不重复收费。禁止把原段落或答案offset免费pin住。拟以半prefix物理token预算作首次可行性检查；若保护并集超预算，记`infeasible_budget`并停止该拟议设置，不加长文本或临时调预算救回。预算/保护span与三生成路径等价性须下一阶段真实验证，目前均未就绪。

## 数据检查与项目内部划分

先取回一个固定dev文件并核对精确bytes、Git blob SHA1，再计算SHA256。解析时拒绝重复JSON键/重复question id、空字段、非v1.1、缺答案或任意`context[start:start+len(text)] != text`。发现错误保留诊断并停止，不手工修正offset、换gold或过滤到有利子集。所有全局校验发生在模型执行前。

划分算法`article_components_v1`固定如下，代码尚未实现：

1. 每篇article为节点。标题经NFC、大小写折叠及空白折叠后相同，或包含相同规范段落hash，则连边；段落仅在此去重键中作NFC/空白折叠，原文本不变。连通分量作为context_group。近义改写不由这个算法识别，不宣称完全排除近重复。
2. component_id为分量内排序后的article原数组索引的紧凑JSON数组UTF-8之SHA256。排序键为`SHA256(b'kv-pruning/squad-v1.1/article-split/v1\0' + component_id的ASCII)`，相同则按component_id。取前34个component：前2工程、随后16开发、随后16封存留出。分量不足34则停止，不改seed、放松分组或跨集复用。
3. 每个component选一个段落：按`len(context.split())`降序，再按原context UTF-8 SHA256、article索引、paragraph索引升序。此为预先声明的“每文章族最长原始段落”选择，不能外推全量随机SQuAD分布。选择该段落中`SHA256(question_id UTF-8)`最小的一个问题，hash相同按原id；原gold全部保留。固定34题，每族1题，不使用共享few-shot。
4. 输出所有源字段校验计数、完整group划分manifest、选中id/source位置/hash、split_role、原文词数/字符数、重复边数、未选原因和SHA256；验证跨队列component、规范段落hash和id零交集。留出自动来源/offset审计可以读取，但不得用于提示、阈值、解码选择或人工挑题；模型尚不访问留出。

这不是官方train/dev/test划分，也不是官方隐藏test；项目内部的工程2、开发16、留出16分别保留身份，不能合成34条独立确认结果。实际数量、文本/模板token长度、半预算可行数目前未知；长段落选择仍可能太短或超出后续上下文上限，应报告限制而不改成填充测试。

## 两个判分域

`json_answer_format_v1`对完整raw输出评分，允许的外层空白仅为空格、tab、CR、LF。必须是唯一完整JSON对象，恰好一个解码后的key `answer`，值为字符串且Python `str.strip()`后非空。禁止重复键（包括转义后同名）、NaN/Infinity、未配对surrogate、BOM、代码围栏、解释、尾随第二对象。非唯一键硬拒绝是本任务的额外互操作要求；[RFC8259 §4](https://www.rfc-editor.org/rfc/rfc8259.html#section-4)用SHOULD，不要误称JSON规范一律语法禁止重复键。拒绝BOM与未配对surrogate也属于本任务的严格输入要求，不能混同RFC允许解析器接受的范围。这里只判格式，不要求答案正确或字面来自段落。

`answer_candidate_v1`先不看gold独立提取候选，防止通过搜索参考答案救分：

| 完整raw类型 | candidate及格式 |
| --- | --- |
| 无重复键的合法JSON对象，含字符串answer | 候选为该字符串；多余key仍可判任务分但格式false |
| 合法JSON字符串 | 候选为解码字符串；格式false |
| 合法JSON数字/bool/null | 候选为去外层JSON空白后的完整原文本；使裸数字答案可评分，格式false |
| 解析失败且首个非JSON空白字符不是`{`/`[`/`"`，也不以三个反引号开始 | 候选为整个去外层JSON空白raw，含解释也不删；格式false |
| 重复键/BOM/非法Unicode/非有限常量，合法数组，对象无字符串answer，或看起来是结构但解析失败 | 无可靠候选，任务EM/F1为null及原因，格式false |

空raw是空候选，可计算分数但格式false；提取到的空answer也可计算分数，不能先按格式过滤。重复键、BOM、非法Unicode和非有限常量优先拒绝，不落入普通文本fallback。不取首行、最后一行、任意子串、多个对象最佳项或用LLM补全JSON。候选提取失败不等同已经证明语义回答错误；EM/F1本身也只是词面参考匹配，不代表完整事实真值。

候选可用时，按固定Python副本：lower → 删`string.punctuation`中的ASCII标点 → 删词边界`a/an/the` → split/join空白；EM为规范串相等，token F1按词频交集；分别对全部原gold取最大。保留v1副本`num_same==0`即F1=0的边界，不擅改为空空F1=1。原raw与抽取候选分开保存；另报原始字面span诊断但不加为主指标。

至少保存format(bool)、task_em(bool/null)、task_f1(float/null)、candidate_status/reason、joint_success（两项均通过才true；任一false为false，其余null）。分别报告四转移、Full正确配对损坏/改善、指标适用覆盖、全部计划cell及error/truncated/not_run/infeasible。任务候选N/A不能消失：列未评估Full正确数；在固定Full正确总数D>0时同时给出损坏率范围`[已知损坏/D, (已知损坏+未评估)/D]`，不是置信区间。D=0为null。不得以严格可评估子集的低损坏率代替全体可靠性。

现有`reliability_report.py`只映射TREC指标，不能直接接本任务。新scorer、N/A与浮点F1 adapter、未知损坏范围及软件fixture须另实现/验证，不修改历史口径或旧工件。

## 分阶段门槛与停止规则

**下一步仅CPU预检：**[禁用提案](../configs/answer-format-task-preflight-proposal-v1.json)固定4份源文件、大小/blob、划分算法、24个评分用例与6个数据/划分用例。未来在服务器新results目录，纯标准库、最多120秒/8MiB网络/32MiB归档、0生成/模型库/tokenizer/GPU查询。作者脚本只读/AST检查，不import/exec；独立实现并用手算边界核验，不能把同一实现当自己的oracle。数据、划分或任一fixture失败即停，原失败完整归档；没有自动重试或改seed。本轮只写提案，runner_implemented=false、execution_enabled=false。

**CPU通过后另冻Full-only提案，当前不执行：**只用上述工程2与开发16，greedy最多96新token，工程最多6个回答核对整段原生/分段完整KV/custom完整KV逐token等价，固定16个Full开发回答，合计最多22个回答；不访问留出或裁剪。架构/精度/模型snapshot、native模板、停止token、repetition penalty与完整生成默认值、墙钟/设备边界须在该提案补齐，不从旧TREC照搬。

拟议描述性支持门槛预先固定为：工程三路径全过；16开发中0执行错误、最多1截断；未截断可提取candidate至少15；未截断task EM正确至少8、format通过至少12、两者同时通过至少8。分母始终16，不能筛掉Full错题补题；这些数量只保证有最小配对支持，不是显著性、功效或毕业质量保证。若模型任务支持/生成可比性不足，保留全部输出并停本适配，不换提示、提高token上限或新挑样本过线。CPU/长度/预算/Full门槛分别标状态，不合并成一个“成功”。

即使Full通过，仍须另冻有界压缩DEV协议及真实字节/额外开销检查，才可能比较Full、随机、适配SnapKV及同预算指令保护；先完成开发再锁定确认分析。留出16还不是已获科学功效论证的正式样本量；确认规模与第二模型须另评估，不能用这个小预检宣称独立论文结论。旧TREC、A、guard、controller及取消队列保持停止。

## 本轮实际动作与交接

本轮仅来源网页/API元数据与小型评分源码静态阅读、设计/禁用配置和文档同步。未取数据正文、未执行作者函数、未新增实验run/主/工程回答；累计94run2732主输出与索引`54b237c2…`保持。已核对旧自有PID786388/787643不存在，没有新后台任务，未查询当前GPU/他人进程，无环境变化。下一条实现独立CPU准备器/评分用例，先审实现和来源固定值，再在服务器单次归档预检；无需重跑已验证报告模块。GitHub无配置，未推送。

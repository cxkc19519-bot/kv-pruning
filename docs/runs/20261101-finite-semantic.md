# 原8组45实例的有限域语义正确性检查

## 实验身份

实验日期2026-11-01，收尾2026-11-02（Asia/Singapore）；用户授权实验会话“开始下一步”，额度审批中断后用户指令“继续”。服务器绝对路径：

`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-finite-semantic-v1`

单次CPU正确性检查完成，worker/独立validator/launcher均exit0；**新有限域语义gate=false**。完成表示全部90格证据已核验，不表示语义一致或研究方向已可行。

## 可复现条件

- [执行登记](../../configs/finite-semantic-v1.json) SHA256 `0e8a001ba1c336db1b17e9176540c6840db168ea23a92d51a4b2cc988a3dd05e`；源码、输入、runtime事前冻结，目录仅执行一次，无重试/回填/改标签。
- 原公共selection SHA256 `41a774b5ae2bc5f43cc0b7ec754ea786491307c562b616b9f36374cb7856d085`，8组/45实例，各后端完整运行，保留原顺序、schema和gold。ensure_ascii=true、sort_keys=true、紧凑分隔符，NaN禁止。两个后端共90格，不计为模型回答。
- 复用已通过的[有限UTF8域](20261101-utf8-domain-factory.md)：133普通字符、EOS133/vocab134。旧257-byte/FF、旧cold5与旧语义gate均保留false；新结果不是追改旧失败。没有重复425项词表预检、8/23/12工程验收。
- Python3.11.13、Torch2.13.0、XGrammar0.2.8、llguidance1.7.6，既有独立环境、runtime101+dill2不改。CPU亲和性≤2、Torch线程1、CUDA隐藏并后验false，禁网络/模型/模型tokenizer/权重/GPU查询/安装/服务。沿原精确ImportBoundary v2，fatal抓栈，无周期抓栈或GDB。
- XGrammar RAW词表、GrammarCompiler(max_threads=1,cache_enabled=false,cache_limit_bytes=8388608)，compile_json_schema(strict_mode=false,any_whitespace=true)，matcher要求显式stop token。llguidance每组转换schema、每实例新建LLMatcher，不启coerce_one_of/lenient或替代grammar。
- 从父spawn至导入/适配完成≤30秒，适配共用5秒；每组从原始schema+测试列表提交开始共用5秒，包括JSON解析、转换/编译、新matcher、全部样例的mask/commit/EOS。每个调用不重置截止；**每组5秒不是单请求5秒SLO**，本轮不做性能比较或资源回收结论。
- worker≤120秒、launcher/复核/清理≤150秒，归档≤64文件8MiB，worker单文件硬上限4MiB、stack外部上限512KiB、core0。硬上限16 schema、90 matcher、618 token位置、927 mask API、618 commit、6000计数边界。
- X mask初始化为全1的CPU int32[1,5]，保留5个有符号原始词和20bytes；LL位掩码与逐token 0/200偏置对全部134个有效bit交叉核对，忽略padding。只提交被mask允许的token；最后EOS允许且提交成功后，核X is_terminated或LL is_stopped且无error。拒绝和错误不伪造为成功。
- 独立validator不导入适配器/作者库，从原始mask、commit、terminal、冻结输入与PID/starttime/时钟重建全部结果；unknown单列，绝不当false或正确拒绝。原始输入快照按序号映射，避免同名覆盖。

服务器根目录内实际命令（记录，不自动重跑）：

```sh
.venv/bin/python -I -S -B scripts/finite_semantic_probe.py --execute --registration configs/finite-semantic-v1.json --registration-sha256 0e8a001ba1c336db1b17e9176540c6840db168ea23a92d51a4b2cc988a3dd05e
```

## 结果与证据

| 后端 | 与原标签一致 | 误接收 | 误拒绝 | error/unknown |
| --- | --- | --- | --- | --- |
| XGrammar | 31/45 | 4 | 10 | 0 |
| llguidance | 39/45 | 0 | 2 | 4 |

LL四个unknown均为public-oneOf的原生不支持错误，发生在新建matcher时；不是四个正确拒绝。41个共同有结果的实例中29个后端结果相同，只有28个同时符合gold；28只是描述统计，禁止筛出后当新确认集或救回gate。

| 原组 | X一致/总数 | LL一致/总数 | LL unknown |
| --- | --- | --- | --- |
| type | 8/9 | 8/9 | 0 |
| enum | 2/2 | 2/2 | 0 |
| required | 2/7 | 7/7 | 0 |
| properties | 4/6 | 6/6 | 0 |
| items | 2/4 | 4/4 | 0 |
| oneOf | 2/4 | 0/4 | 4 |
| maxLength | 4/5 | 4/5 | 0 |
| pattern | 7/8 | 8/8 | 0 |

实际16 schema、90 matcher、415 mask位置（X199/LL216）、631 mask API、377 commit（X177/LL200）、1771计数边界，全部90格保留。接受路径X23/LL25共48次EOS后停止均已观察；X其中4次属于gold不合法内容，停止机制可工作不等于schema语义符合。

无计时违例、mask/bias或mask/commit冲突；CUDA false，guard最终拒绝计数全0。导入2.548245328秒、适配0.053561908秒、launcher3.141751348秒，仅单次工程值，不代表延迟SLO或真实模型词表性能。

## 差异解释与证据强度

- 两后端都在整数实例1.0的小数点处拒绝。字节往返正确，现象属于当前生成语言与JSON Schema数值标签不一致；不通过将1.0改成1来救回本轮。
- X的9个误拒绝涉及没有显式type的properties/required/items在其他JSON类型上的适用性。固定版本转换器在缺type时依据object/array关键词选择类型，与观测相符。
- X运行日志明确报告重叠oneOf降为anyOf；固定源也有这条fallback。3的误接收与非排他处理相关；1.5还涉及无type的minimum分支，不能全部归因于XOR近似。无type的maxLength/pattern实例也出现非法字符串被接受，固定ParseSchema的最终AnySpec分支提供解释。
- LL原生错误明确提示该oneOf不支持并给出近似开关；本轮未开启。此版本的[官方支持说明](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/docs/json_schema.md)已有oneOf限制，不能据此称新漏洞。
- LL对两个代理对转义表达的字符串在首个unicode escape的d处已经拒绝，尚未读完整串。只能确认当前转义形式不被接受，不能写成已发现Unicode字符长度计数错误；也不切换序列化来重测本轮。
- [X固定转换器](https://github.com/mlc-ai/xgrammar/blob/v0.2.8/cpp/json_schema_converter.cc)源码/LL版本文档均经API获取并核Git blob；这不独立证明native wheel构建commit。X原生fallback日志加强了相应路径证据。main文档的新选项不能倒推已安装旧版具备相同能力。

来源预检档8文件97941bytes/manifest `f3d9ee522e68c69932ba4048c7601bfb288017b1432fa59525bdc8e009bd0a0b`；解释来源档4文件203571bytes/manifest `7e5ac55bb4fd20ddbd47f869b16899eda96e261cd797b77121ee5fcacf013e7d`。一次静态读取尝试了不存在的xgrammar/bitmask.py，随后在实际matcher.py找到尺寸接口，未执行作者库；固定LL stub网页cache miss采用安装源及既有来源，不当源码不存在。

## 收尾与下一步

原始41文件1803891bytes/manifest `681e554a0f3a3de8d845a7dbdf05d3eea9cbc7981c6c8c2b7f525a565d58888c`，独立verification `c7ea66071986b00c05c7ce551f120f9844625d712e229b7e40734aad20ac845a`。三档全量回读，source/input/runtime101+dill2不变。

launcher2279461/starttime428607021、worker2279464/428607030、validator2279506/428607329、query2279465均现场核不存在；query exit0、stdout103903bytes/stderr0及原固定摘要复核。无后台、端口、服务、安装或新实验队列。

新增1CPUrun、90语义结果、0模型回答，累计146runs3038历史主回答。服务器新索引`results/20261102-run-index-finite-semantic.json` SHA256 `871a056ca16417ae2a8df444319fffe043b32b9cc3b9e719ec32260b94f3bf17`；closure `results/20261102-finite-semantic-closure.json` SHA256 `40699c78faf506902670ba972a37ab3236a05dabded47e3260546beae7e89d80`。旧结果/索引均不改。

当前45题不能直接充当等语义的双后端资源回收对照，资源/取消/性能阶段保持关闭。下一步只独立定义共同支持的明确类型schema族与事前正负例协议，再决定新预注册小检查；不筛这28个共同正确实例、不改旧schema/gold、不启coercion或追加seed救回。支持覆盖差异已有强近邻，不以此立新颖性；N1资源效果/论文可行性仍未建立，H3停止/泛KV暂停保持。

2026-11-01最后一次只读跟进因额度导致自动审批未完成，操作未执行；2026-11-02用户“继续”后同范围读取和收尾已恢复。STATUS/WORKLOG/HANDOFF/PLAN/README与readiness同步服务器，原始仅服务器，GitHub未配置未push。

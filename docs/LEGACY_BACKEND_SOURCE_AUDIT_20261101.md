# 前置失败源码审查：byte契约冲突与导入观测缺口

日期：2026-11-01。承接[真实后端前置失败](runs/20261101-legacy-backend-cpu.md)。本轮只读取已安装源、旧工件与对应版本官方源，未导入／执行作者库，未运行新byte探针、编译、mask或模型。不是新实验run。

## 结论与证据强度

**llguidance 的原全256 byte恒等假设与对应版本源码冲突。** 它保留 `0xFF` 作为特殊token标记。我们的id255恰是单字节FF，因此对应decode路径会剥去它的首字节，预测解码为空；0..255整个序列预测只有255bytes。此结论能解释旧roundtrip拒绝，但旧run未保存实际差值，本轮也没有补跑，不能称已测到具体缺失。

**XGrammar 的超时根因仍未知，已经确认观测范围不足。** 旧事件把Torch导入、两个线程设置及XGrammar导入合并为一个5秒阶段；不能定位到其中某一项，也不能把该耗时称为语法编译耗时。先补证据，不提高阈值。

N1仍未定题，旧语义gate继续false。45标签两后端均未执行；原12项合成观测器通过保持。此次是测试入口与适配契约审查，不是发现新模型／安全问题。

## 1. llguidance 1.7.6：调用链已找到

官方tag `v1.7.6`解析到 commit `0384f3f6aab6cebe8abf9b74db0079b96f5837ef`。已安装Python wrapper和stub的Git blob逐字节分别匹配该tag；runtime_pin中101文件事后仍匹配。安装为native wheel且没有direct_url记录，这些核对不能独立证明.so恰由该commit构建；下面是版本对应源码解释，仍需实际差值验证。

| 固定源位置 | 静态事实 | 对当前适配器的含义 |
| --- | --- | --- |
| [special_tokens.md:12–25](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/docs/special_tokens.md#L12) | 文档规定FF标记，解释它不是合法UTF-8字节 | 不能把所有raw byte都直接当普通token而假定恒等解码 |
| [py.rs:309–359](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/python_ext/src/py.rs#L309) | 从wrapper取tokens；对special_token_ids里的词项补前导FF，再建TokTrie | 指定special_ids=[256]不会将已经以FF开头的id255重新解释成普通字节 |
| [py.rs:232–235](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/python_ext/src/py.rs#L232) | Python decode_bytes调用TokTrie.decode | 不是直接拼接原始tokens数组 |
| [toktree.rs:185、510–530](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/toktrie/src/toktree.rs#L510) | 标记值FF；decode对标记开头词项只输出后续字节 | 单独FF词项预测输出空；EOS词项仍输出其标记后字符串 |
| [toktree.rs:580–583](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/toktrie/src/toktree.rs#L580) | is_special_token以词项首字节判定 | 预测id255和id256都被判为special，而不是只检查Python列表 |
| [py.rs:88–93](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/python_ext/src/py.rs#L88)、[toktree.rs:300–313](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/toktrie/src/toktree.rs#L300) | EOS覆盖更新EOS元数据，不重写词项字节 | 把eos指定为256也不能消除id255的标记冲突 |

原适配器在 `legacy_backend_cpu.py:172–175` 直接要求decode(0..255)==原bytes；该检查严格停止是正确行为，错误在我们此前预设了未经核实的跨后端通用byte契约。不能删除FF、跳过检查或以公共实例没有用到FF为由冒称原257词表gate通过。

公共45实例采用ensure_ascii=true，故实际JSON文本只用ASCII；这说明前置失败不等价于这些实例语义失败，**并不授权将原词表换成ASCII后追改旧结果**。若未来改为共同UTF-8／ASCII可表达域，必须作为明确不同的工程契约，说明有限范围，不充当原全byte等价证明。

还审查了内置`LLTokenizer("byte")`候选：版本对应[src/tokenv.rs:162–180](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/toktrie/src/tokenv.rs#L162)在256字节之外加6个特殊词项，vocab=262、EOS=261；[py.rs:72–85](https://github.com/guidance-ai/llguidance/blob/0384f3f6aab6cebe8abf9b74db0079b96f5837ef/python_ext/src/py.rs#L72)的该分支也不直接套用自定义wrapper分支的EOS覆盖。它不是257词表／EOS256的直接替代，不采用未经核验的快捷替换。

## 2. XGrammar 0.2.8：只能确定导入路径，不能断言慢在哪里

以下行号指本轮归档的安装源码，均文本／AST审查，不执行import。

- 旧runner `imports`函数141–146行依次是：import torch、set_num_threads(1)、set_num_interop_threads(1)、import xgrammar；前后只有一个call_begin/end。缺失end无法进一步定位。
- Torch `__init__.py`包含global dependency loading与`torch._C`扩展导入（369、444–445行）；这只是路径中的可能工作，不能从源码存在推断它就是超时原因。
- XGrammar `__init__.py`先引入load_binding等模块，并导入compiler、contrib.hf、tokenizer_info等；base经TVM-FFI加载绑定，tokenizer_info和contrib.hf还依赖Transformers。公开入口不只“加载一个小.so”。
- TVM-FFI可选Torch DLPack扩展受 `TVM_FFI_DISABLE_TORCH_C_DLPACK` 控制；旧登记已设1，旧环境不变。没有运行证据表明可选JIT实际发生，不能以源码含编译代码就归因于JIT。
- 旧audit hook对每次Python open同步做Path.resolve；该开销也处于5秒阶段内。源码审查只说明测量含保护与导入开销，没有测出其贡献。

因此本轮没有“XGrammar导入已修好”或“5秒不合理”的结论，也不据失败增加时限。既有XGrammar被kill后缺guard最终汇总及CUDA后验状态的边界继续保留。

## 3. 下一步最小诊断：只补缺失证据

[冻结诊断草案](../configs/legacy-backend-diagnostic-draft-v1.json)执行关闭、runner未实现，不是运行登记。它保持原runtime pin、257词表和原组合import总5秒，不编译schema／构建matcher／调用mask或执行45标签。

1. llguidance：同一原始wrapper构造一次，保存每id的原bytes、actual decode、special标记及整个0..255的decode差值；包含EOS和两个固定编码probe，公开调用上限520。源码预测只作为可证伪预期，实际不同必须保留并报告。
2. XGrammar：在原同一5秒组合阶段内加Torch begin/end、线程设置begin/end、XGrammar begin/end；每个checkpoint不得重置deadline。用标准库faulthandler周期栈快照保留被kill前的位置。它是增加观测，仍不能把受观测耗时当未经干预的性能基准。
3. 另实现runner／独立validator、固定源码与输入hash后，才登记一次30秒总量、单调用5秒、LL段10秒、两CPU以内的诊断。需核PID/starttime、guard即时记录、validator PID与超时删失；0schema、0mask、0模型、不联网或安装。

任何新decode调用或import都属于新实验。本轮未执行它们，未修改旧runner／登记／失败工件。诊断即使与预测一致，也不能使原语义gate自动变true；它解决的是入口证据，不是N1研究go/no-go。

## 4. 来源与收尾

官方6文件按固定commit取回并核Git blob；安装12源加本项目旧runner／登记共14快照，全部仅服务器。两个安装Python文件与tag blob匹配；runtime101、旧失败manifest与旧索引复核不变。旧launcher2212823、worker2212826/2212901现场均不存在，当前没有后台任务。源审不新增run，仍134runs／3038历史主回答。无依赖／环境变化、无模型／GPU实验，GitHub未配置未push。归档最终SHA与下一步状态见[readiness](LEGACY_BACKEND_SOURCE_READINESS_20261101.json)。

最终归档 `literature/20261101-legacy-backend-source-audit-v1` 共25文件334142bytes，manifest `4b90869ddfaaaaf26f713e4c516aad36cfae8d98e37526f6e5f4f798c32df49a`、closure `72ecec088b75bed320a5eb06cbb1e623fd7305fee6c88e18938e1c1a9377457e`完整回读。诊断草案SHA `b6802e248398d01dfe278b7cb44055e559d0fb96c833c3aa34dc3442bb40bbb6`，快照随归档封存；旧执行登记和旧失败工件未改。6个本轮官方源请求均成功，没有执行作者源码或补跑库调用。

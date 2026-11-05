# SystemCheck、Pitfalls前端与LongBench TREC来源审查

## 实验身份

- 日期2026-10-28，Asia/Singapore；用户“开始下一步”并补充“继续吧”。沿最新交接执行来源与CPU可行性审查，未启动模型实验。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-systemcheck-source-audit-v1`、`.../20261028-systemcheck-source-audit-v2`。v1网络获取失败并终止；v2审计与独立`semantics/analysis_manifest.json`完成。
- 目的：检查S-IFEval是否提供所需长前缀，核对数据/标注、角色与压缩时机、来源许可和内容能力指标。不是压缩准确率测量、第三方完整复现或创新性证明。本地只代码/文档；没有复制nano-vllm。

## 可复现条件与命令

| 来源 | 冻结版本 | 本轮范围 |
| --- | --- | --- |
| [Pitfalls](https://github.com/alexluchen/pitfalls-of-kv-cache-compression/tree/73079e1b3bf27cd182f680d7da5edd97b660bd82) | `73079e1b3bf27cd182f680d7da5edd97b660bd82` | README、S-IFEval数据/评分/指令工具、shuffle、前端/解码/utils、防泄漏模板、requirements、kvpress许可，共13文件 |
| [SystemCheck](https://github.com/normster/SystemCheck/tree/ed829f6ac7cd4e09f7161fe7dffbebdd220eb024) | `ed829f6ac7cd4e09f7161fe7dffbebdd220eb024` | README、MIT许可、S-IFEval数据/评分、EVALS与convert.sh，共6文件 |
| [LongBench](https://github.com/THUDM/LongBench/tree/2e00731f8d0bff23dc4325161044d0ed8af94c1e/LongBench) | `2e00731f8d0bff23dc4325161044d0ed8af94c1e` | LongBench子目录README、许可、dataset2prompt、metrics、eval、pred，共6文件；不是LongBench v2 |

- 总25文件均按官方Git tree对应blob SHA核验，12个Python AST通过；不import上游模块、不执行shell脚本、不pip install requirements。SystemCheck和LongBench各保存本次取得的commit元数据及固定tree，Pitfalls固定tree保留。Google原数据复用上轮SHA `67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49`。
- 服务器已有Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`的tokenizer，五个tokenizer/config摘要逐个复核。Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1不变；CUDA未初始化、没有模型权重加载/新下载或新依赖。
- 先用GitHub连接器读3文件及README；连接器随后不可用，改官方固定地址。raw下载v1累计观察5次read timeout，后续任务仍等待；确认API blob路径v2全部完成后，仅终止自有v1 PID2601605（SIGTERM），保留manifest、fetch_failures、源码和console。v1是网络失败，不是数据/模型门槛失败；未动其他会话服务。API v2没有fetch失败。
- 浏览核对[ACL正式论文](https://aclanthology.org/2026.acl-long.1926.pdf)第3节及附录I；固定SystemCheck树网页cache miss、旧LongBench根config路径404均记录，改正确`LongBench/config`。HF API/README网页不可访问，但[官方数据卡](https://huggingface.co/datasets/zai-org/LongBench)可读，旧THUDM地址会重定向；未因此使用第三方镜像或声称已取得原始数据。

固定tree的准备：官方GitHub API `repos/<owner>/<repo>/git/trees/<上述commit>?recursive=1`只读响应写入各run的`pitfalls-tree.json`、`systemcheck-tree.json`，补充的`longbench-tree.json`写入v2。v2复用v1两份已固定tree；不以未来main替代。

实际正式命令（服务器方向目录）：

```bash
.venv/bin/python scripts/audit_systemcheck_sources.py --out results/20261028-systemcheck-source-audit-v1 --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
.venv/bin/python scripts/audit_systemcheck_sources.py --out results/20261028-systemcheck-source-audit-v2 --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --transport api
.venv/bin/python scripts/inspect_systemcheck_semantics.py --run results/20261028-systemcheck-source-audit-v2 --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
```

v1执行的是原始无transport参数源码，SHA `387571ba89da5125611dc17655ac338da0bbe68409b1da7b1af1313c38770b08`；v2脚本新增api传输选项，SHA `7324f23a5063792f3a797018f85f7e9edf05192fdf2e7cc892b793312e166a43`。补充分析脚本SHA `cf9aaed2b6caf64b063d9abd182ccc67b4f94efe8d467709e0ab6aa6654461a3`。均保存各自源码快照。脚本拒绝覆盖manifest/分析目录，复核需另建目录并准备固定tree。

## 结果与证据

原生模板统计的是**压缩前system部分**，不含尚未提供的user query；与上轮完整user前缀的计数口径不同。

| 冻结数据/包装 | 题数 | system前缀最小/中位/最大token | 满足原256–2048范围 |
| --- | --- | --- | --- |
| SystemCheck，不加包装 | 541 | 10 / 29 / 108 | 0 |
| Pitfalls，不加包装 | 539 | 10 / 29 / 108 | 0 |
| 两者，仅作者默认prepend | 541 / 539 | 34 / 53 / 132 | 0 |
| Pitfalls，默认prepend再标准defense | 539 | 118 / 137 / 216 | 0 |

- 每题system-only编码都与完整system+user+assistant编码前缀一致；这是tokenizer关系，不是实际缓存/生成正确性验证。不加包装和仅prepend时，全部题目50%预算都放不下原sink4/recent64的共享锚点。不能把调整锚点或添加防泄漏指令混同于原方案通过。
- SystemCheck保留官方541个key；其`kwargs`有1题变化：key1012的`prompt_to_repeat`删去标题约束，改为只重复user请求。另key181的字面转义换行变成实际换行、key3345修正Point拼写，完整差异已归档。不是无修改的Google原数据。
- Pitfalls固定数据只有539题，缺key1000和3401，现有快照未提供其缺失理由。保留的539题在messages/prompt/IDs/kwargs上与本次固定SystemCheck逐key完全一致。论文称541题与此代码快照539题的差异须保留，不能私自补回两题或冒称原论文完整复现。
- 原生S-IFEval把可验证输出约束放system、任务放user；源码先对system-only forward/压缩，再处理user和assistant header，属于相对该user问题的query-blind前缀压缩。默认prepend先应用，若指定defense模板再包在外面。`original_messages`仅在defense分支赋值，但默认开启的analysis会读取它：这是静态发现的默认配置风险，未实际运行，不宣称必然崩溃。不能直接执行作者README示例就声称本项目路径正确。
- 作者生成循环显式保留原逻辑position_ids，停止仅比较tokenizer eos，参考库还存在不同缓存API/依赖版本；未审计全部细节或复测。错误会被捕获后跳题，结果函数会过滤无响应题目；本项目后续必须固定全体key，显式列error/N/A和原始分母，不照搬这种隐式分母变化。
- Pitfalls README声明CC BY4.0，固定树未发现根独立LICENSE；SystemCheck为MIT，kvpress有Apache-2.0许可，Google衍生指令源保留Apache头。保存各自声明，不能用一个总许可证覆盖所有组件。未重新发布数据。

LongBench TREC源码核查：

- 标准模板是任务引导＋`context`示例＋`input`问题；官方pred对TREC不套chat wrapper，超长时从中间截断。若本项目将示例改放system并使用Qwen native chat，将是明确前端改编，必须另审实际token/cut，不能称官方前端原样。
- 官方`classification_score`按大小写敏感的标签子串查找，命中多个类别可能给分`1/n`；eval还先去开头换行、只取第一行。因此官方分不等于整段输出严格标签匹配，更不能判分完整回答中的额外违规内容。未来保留其兼容指标，同时另立完整输出的精确标签/格式/约束分数，禁止用首行预处理掩盖其他行。
- 官方README提供HF/data.zip入口与context/input/answers/all_classes/length结构；当前未下载TREC数据、未固定HF数据revision/逐题SHA、未核验标签或长度。本轮GitHub源码版本不等于HF数据版本；卡片viewer还报旧dataset script不受支持，后续优先固定文件读取，不盲执行远程dataset脚本。
- Pitfalls附录I已经报告TREC长上下文分类与防system泄漏的联合评估、1000–2000/2000–3000/3000–4000词区间及长区间Full泄漏问题；不能把“在TREC上分开正常能力与约束”当作新贡献。固定作者tree没有TREC命名文件，所查README未给附录I构造入口；不能据此断言作者未开源全部代码，但目前不能完整重建其前端。

所有数据、逐key长度、annotation_differences、源码快照、tree/blob证明、评分摘录、manifest和console均服务器。v2 `summary.json`与`semantics/summary.json`、`closure_audit.json`提供汇总；输入/source/artifact及tokenizer核验通过。本轮2个主manifest run（1网络失败、1完成，补充分析单列）、0模型答案，累计50run2460主输出；索引`results/20261028-run-index-systemcheck-audit.json`。历史输出含重复控制，不当独立样本。两卡收尾15MiB/0%、compute-app列表空；无本轮剩余审计/模型进程、后台服务/端口，新依赖/权重均0。未测准确率、安全性或性能。

## 解释与下一步

结论限定：S-IFEval及其标准包装不能满足**旧方案**的长前缀条件，不代表短前缀压缩不值得研究；本轮也不评价模型能力。原IFEval提案保持禁用、不降低阈值救回，旧AccessDenied失败保留。

下一步的具体范围是**LongBench TREC原始数据CPU预检**：固定官方HF实际仓库重定向、commit与文件SHA、许可/引用和样本key；确认context示例边界、input/answers/all_classes、重复/冲突标签及新Qwen前端的真实prefix长度、后缀与预算。先保留原数据构造，不凭词数推断token、不截断来凑长度、不按模型成绩选题；拿不到官方文件则记录失败，不能静默改第三方镜像。该数据步骤不需要加载模型。

数据可行后才另存独立设计：区分普通分类能力、逐项输出约束与泄漏指标；确保所测信息确实依赖上下文，防止模型凭常识分类造成“内容保留”的假象。需冻结前端/评分/样本总体、Full支持量与真实KV/解码检查，之后再考虑小矩阵。复制附录I只能作为有限复现；没有研究差异前不开发或命名新算法，不把校准结果当安全特异性/论文创新。STATUS/HANDOFF/WORKLOG等已同步更新。

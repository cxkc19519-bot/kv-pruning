# TREC 50%等预算裁剪CPU预检

## 实验身份

- 日期2026-10-28，Asia/Singapore；用户“开始下一步”，按最新交接执行CPU任务头/预算/选择器预检。本轮不加载模型权重、不生成答案，不复制nano-vllm。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-trec-pruning-cpu-v1`。状态complete；CPU预检通过，真实模型工程关卡未执行。
- 范围为固定32题with_demos、四个50%预算校准条件的工程准备，不是压缩效果、实际模型hook验证、安全结论或新方法。全部原始输入/映射/日志留服务器，本地仅代码、配置与文档。

## 可复现条件

- 原裁剪提案SHA `289bb122e62788cff3406df9ba42a792172b2f10959144be187271e52634093f`保持原样，execution_enabled=false；能力提案SHA6e9c61d1...、cases SHAe709d4bd...与Full baseline generations SHA72a429e7...全部复核。原32个key顺序保留，包括19个Full正确及13个错误，没有按结果改样本。
- 复用现有Qwen2.5 fixed `a09a35458c702b33eeacc393d103063234e8bc28` tokenizer，五文件摘要逐个匹配；只读取配置确认28层/4KV heads/head_dim128/Full Attention。Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1不变，无新依赖/权重。CPU线程4、CUDA_VISIBLE_DEVICES为空，CUDA始终未初始化。
- 四条件：适配SnapKV共享锚点、随机共享锚点，以及各自保护完整任务头。每层/KV-head预算floor(N/2)，sink4/recent64为共同强制位置，完整header保护另算入同一总预算，不增加名额。用户query/gold不传给选择器，query suffix不参与评分或裁剪。
- 新工具`trec_pruning_utils.py` SHA `92594811de726c585087fe1356a81cfcbe3a19a1fd6bb68a7e8781a334c53918`；准备脚本`prepare_trec_pruning_cpu.py` SHA `087589fa101a970be8486869d1e084b98cebef095bd4638c5091ce5f733d1bcf`；独立复核`verify_trec_pruning_cpu.py` SHA `09d0ff980120a789cf44ab5c171f5a9d43dae85a025c4bdf6043222ff19bfcc3`。同版本源码和命令全部归档，不修改旧runner。
- 评分源固定已有独立`pilot.py` SHA `476b3cbf8a9e16cdbb958286ba931a45d9b089f1bba4fb0a29f3a7ee9ebcdc1f`。审阅WindowScores：最后64个post-RoPE query、原前缀causal mask、先去掉观察窗key、query平均/宽5池化/GQA均值、近期高分填回。CPU只抽取此类AST做合成数值核查，不执行旧pilot主函数；不是新评分算法或作者公平SnapKV。

实际运行命令（服务器方向根；前台SSH父进程等待，无后台服务）：

```bash
CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/prepare_trec_pruning_cpu.py --proposal configs/trec-pruning-calibration-proposal-v1.json --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261028-trec-pruning-cpu-v1
.venv/bin/python scripts/verify_trec_pruning_cpu.py --run results/20261028-trec-pruning-cpu-v1
```

目录/manifest拒绝覆盖，复核须新建out。准备前py_compile通过；自有CPU PID2879784已exit0。准备20.94秒、独立复核5.99秒，仅为CPU运行记录，不是模型性能比较。

## 结果与证据

| 项目 | 实际CPU结果 |
| --- | --- |
| 原生header字符区间 | 32题均[19,877)，完整858字符，覆盖每个字符 |
| header对应token | 200个；实际32题没有跨边界token |
| sink4/recent64共同位置 | 68个 |
| header与共同位置并集 | 267个，每层/head比共同锚点多199个槽位 |
| 50%预算 | 每层/head1034–2091个槽位，全部容纳267个强制位置 |
| 配置对应BF16 prefix字节预算 | 59,293,696–119,906,304bytes；按28层/4KVhead/head128计算，不含suffix/decode或其他开销 |
| 四方法层/head索引检查 | 32×4×28×4＝14,336个 |
| 100%选择/gather恒等 | 32×28×4＝3584个层/head，K/V逐值相等 |
| 独立保存索引复核 | 全部14,336个；另以Python排序复算1024个head结果 |

- header只包含共享输出指令和50标签列表，不把整个system示例块当header。offset编码与冻结native ids完全相同；保护集合含所有与header字符相交的token并计成本。实际无边界重叠，另用原输入首token内部截断的**人工header定义**验证跨边界token必须被完整纳入；未改真实prompt/cases或预算。
- 稳定选择流程先固定强制位置，再从剩余位置按分数降序补齐；相同分数按原位置升序，最终按原位置排序。6个预期拒绝样例通过：保护超预算、header越界、NaN分数、重复索引、缺近期锚点、无效预算；这些是预期测试，不是运行失败。
- 随机分数为CPU float64 IID uniform；每原_id/layer/KV-head以固定20261028种子及SHA256派生局部torch Generator。header保护与未保护共用同一分数流；重复生成逐值相同，保护变化只因预算内强制header置换，不读取模型输出/query/gold。具体序列以源码/版本摘要冻结，不承诺跨所有框架版本位级一致。
- SnapKV方法本轮使用明确标记的**合成随机fixture分数**验证选择/搬运路径，不是模型重要性分数，不能从保存的synthetic_maps分析语义保留或模型表现。
- 主要合成缓存用28层/4KVhead/BF16/head_dim2，两个精确可表示的坐标编码原位置；每种方法实际gather后逐head用独立index_select检查K/V，确保选中的原值不重编号、reference不变，四方法实际张量字节相等。原100%选择/gather逐值恒等。
- 另以真实模型形状28层/4head/head_dim128创建一份**无模型的合成BF16缓存**：N2657全prefix152,363,008bytes、半预算1328槽76,152,832bytes。它验证形状/元素字节计算，不冒充真实模型cache正确性。
- 对WindowScores做N65/N129、4query heads/2KVhead/head8的FP32合成测试；独立逐query/head因果attention＋手动池化/GQA参考与其评分最大差约1.86e-9/2.79e-9。两次评分相同，输入、K/V、cos/sin及返回output对象不变。未验证真实BF16模型hook、动态cache路径或输出。

证据在run内：`header_budget_metadata.json`、`synthetic_maps/<原_id>.json`、`synthetic_cache_checks.json`、`hook_cpu_checks.json`、`selector_edge_checks.json`、`model_shape_byte_check.json`、`artificial_boundary_check.json`、verification summary/manifest、proposal/prepared config及所有输入/source/artifact SHA。索引映射等约361.8MB，只在服务器，未下载本地。

## 下一步与执行边界

CPU准备配置：[trec-pruning-cpu-prepared-v1](../../configs/trec-pruning-cpu-prepared-v1.json)，SHA `892bde36749089e03f9e2aa84b8bc65379fb6d22b505867d49c2353dbb8ecf25`，与run内prepared_config逐字一致，status为`cpu_preflight_complete_pending_actual_model_engineering_checks`、execution_enabled=false。主裁剪提案不改写，旧IFEval/AccessDenied停止与失败状态不变。

下一步先实现独立的真实模型裁剪runner，冻结上述工具/评分源/输入/tokenizer摘要，查GPU资源后只对原首3题做工程检查，预算最多24额外输出：

1. 无hook与hook前缀prefill的**每层K/V逐tensor相同**，原reference不被评分修改；Full生成重现已归档baseline ids。
2. 各选择器100%索引恒等及真实gather K/V相等，100%生成输出与baseline一致；这与本轮CPU合成检查分开。
3. 压缩分支物理cache长为floor(N/2)，suffix/decode仍用原逻辑RoPE位置，不把物理长度当逻辑长度。现有`trec_context_gate.custom()`明确只支持Full并assert physical==logical，**不能直接拿它跑裁剪或就地删除断言冒充适配**；需独立路径与原生cached参考对照，记录全部差异/失败。
4. 实际模型分数的索引、共同锚点、完整header、每层/head预算和四条件真实KV字节在生成前逐项检查，保存真实maps并与synthetic_maps明确分开。

工程关卡全部通过后才另存启用的执行快照，运行四条件×原32题，最多128新主要输出。保持原输入/分数参数/greedy penalty1/maxnew64/EOS/评分不变；baseline引用Full run SHA72a429e7...，首3题不能重现则停止，不能静默复用。

全部32含13个Full错题，报告Full→压缩C→C/C→W/W→C/W→W及32总体/19 Full正确分母、格式/截断/error/N/A；NoDemo的9损失/1改善单列。出现改善或没有退化也保留，不挑方法或调参直到出现退化。这个方案仍是分类/格式诊断校准，不证明一般安全约束保持，不把完整header保护/随机对照当创新或作者公平SnapKV复现。

## 收尾

- 本轮1主manifest CPU run、独立verification manifest单列，0新模型输出，累计55run2524主要输出，索引`results/20261028-run-index-trec-pruning-cpu.json`。本轮没有实际裁剪模型推理或质量/性能/显存峰值测量。
- 所有source/input/artifact与保存maps摘要通过，32题metadata重算一致；CPU与模型工程门槛分别记录true/false。0运行失败、无新依赖/权重/后台/服务/端口。
- 自有审计进程退出；两卡最后15MiB/0%、compute-app列表空，其他会话进程未改动。STATUS/HANDOFF/WORKLOG/README/PLAN/run与新代码/准备配置已按远端旧SHA核对同步；本地不留原始数据/结果。

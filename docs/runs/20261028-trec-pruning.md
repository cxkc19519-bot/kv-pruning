# TREC 50% KV裁剪与任务头保护：128输出校准

## 实验身份

- 2026-10-28，Asia/Singapore；用户“开始下一步”，按冻结32题/四条件提案实现真实模型runner，通过全部工程门槛后运行128主要输出。状态complete，0运行失败，不补样本、不扫参数。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-trec-pruning-v1`。原始数据、完整输出、实际scores/maps/检查/分析/日志均服务器；本地仅代码/配置/文档，不复制nano-vllm。
- 这是普通Full Attention/GQA模型上的分类与精确标签格式校准；不把标签格式失守称隐私泄漏/权限突破，不称新算法、完整作者复现或安全特异性证据。

## 可复现条件

- 原[裁剪提案](../../configs/trec-pruning-calibration-proposal-v1.json)SHA289bb122...、[CPU准备配置](../../configs/trec-pruning-cpu-prepared-v1.json)SHA `892bde36749089e03f9e2aa84b8bc65379fb6d22b505867d49c2353dbb8ecf25`均保持execution_enabled=false的原始版本；runner先复核CPU manifest/verification、所有32输入/header metadata与tokenizer摘要，再做真实模型检查。主生成前另存execution_snapshot启用此次运行，SHA `7eb393cc6d42004c9fe1e6d94d7f3c0f5073f34c45af725bbc4269645c324e1b`。
- 原32题with_demos不改，cases SHAe709d4bd...；包含19个Full正确、13个Full错误。Full baseline沿`20261028-trec-context-full-v1`32个有示例输出，源generations SHA72a429e7...，无示例条件不混入Full→压缩配对。用户query、gold不参与选择器；仅对system prefix预填充/评分/裁剪，再追加原user＋assistant suffix，属query-blind设置。
- 现有Qwen/Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`，运行时Qwen2ForCausalLM、28Full层/无滑窗、7,615,616,512参数元素全部BF16。单GPU0 RTX4090，驱动580.178.04；GPU1未使用。Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1，无新权重或依赖。
- decode与已归档Full的GenerationConfig逐字段相同：SDPA、greedy、num_beams1、penalty1、max_new64、EOS151643/151645、pad151643。仅移除末尾EOS传输token，正文/其他特殊token不隐藏，raw ids与含末尾token文本保存。原判分fixture再验证，官方首行兼容分与整段exact/格式分开。
- 四方法都每层/KV-head严格floor(N/2)，共同sink4/recent64；header保护含200个原生token，与锚点并集267，成本包含总预算。每case四方法实际prefix K/V字节相同，范围59,293,696–119,906,304bytes，逻辑位置仍为原prefix长度，suffix/decode KV新增另计。
- WindowScores沿已有Qwen2适配，window64/kernel5/GQA mean，source pilot.py SHA476b3cbf...，不是作者公平SnapKV。随机seed20261028按源_id/layer/KVhead派生，pin/unpin共享分数流；选位/gather沿CPU已核查工具SHA92594811...，未改源码或平分规则。
- 新runner `scripts/trec_pruning_run.py` SHA `7b9393babbcf28293d51fdd43c7a80ed41810d614001811b6c458c55d3c84412`；独立CPU分析`analyze_trec_pruning.py` SHA `c751c5b3268b7037216f688a00b505ca296ee6208e9773a4bf5d075d24fadb7f`；保护干预配对`trec_header_tradeoffs.py` SHA `43feadb6d0c4a03be5fb6eda5673b77f9e28c8ef067fc4f59242e21fd28bc02a`。所有依赖的自有源码、输入摘要和HF prepare实现文本均同版本存档，不改旧Full-only解码函数。

实际命令（服务器方向根，前台SSH父进程wait，无tmux/nohup/服务）：

```bash
CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/trec_pruning_run.py --prepared configs/trec-pruning-cpu-prepared-v1.json --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261028-trec-pruning-v1
.venv/bin/python scripts/analyze_trec_pruning.py --run results/20261028-trec-pruning-v1
.venv/bin/python scripts/trec_header_tradeoffs.py --run results/20261028-trec-pruning-v1
```

启动前py_compile和资源检查通过；模型PID2915326，前台exit0。run/analysis拒绝覆盖；重放必须新建目录并保留固定输入，不将旧快照改成新结果。

## 前置工程检查

- 原首3题每题8个输出，共24额外输出：native整段Full、无hook cached Full、hook cached Full、100%gather Full、50%Snap无pin的HF cached参考/自定义、50%随机header-pin的HF cached参考/自定义。全部token一致；前4条重现已归档baseline。四方法的100%gather都逐K/V等于reference（仅一条生成），不是只检查索引数。
- hook与无hook prefill每一层K/V逐值相同，评分后Full输出同baseline；原reference指针/version/形状不变，分支独立。hook仅在system prefill注册，suffix/decode之前移除，无query泄入评分。
- 自定义循环分别传原逻辑position_ids与物理cache_position，并逐步断言恒定偏移；HF generate参考使用**明确的输入准备适配**，在其由物理attention mask生成的位置上加原长减物理长的常量，保留其原生mask/cache更新。不是宣称HF无修改即可正确处理裁剪；适配方法调用后恢复，输入与每步位置轨迹记录。首3题两种压缩方法的参考/自定义输出和位置trace全部一致，不冒称128输出全部逐个和HF重跑。
- 主生成前每case四方法28层/4head预算、索引唯一/排序/边界、共同锚点/完整header和实际K/V字节断言通过。实际模型score存`actual_scores/*.pt`，实际索引存`actual_maps/*.json`，不使用或混淆CPU synthetic_maps。
- CPU独立重解码128输出、重算整段exact/格式/官方兼容分、逐步位置及最终live KV字节；复核14,336head实际maps，另1024head以实际Snap score/固定随机流和独立Python排序重算，全部一致。原source/input/artifact/tokenizer摘要核验通过。

## 结果

| 方法 | exact正确/32 | 合法标签格式/32 | C→C / C→W / W→C / W→W | 原Full正确题损失 |
| --- | --- | --- | --- | --- |
| Full（已审基线） | 19 | 32 | — | — |
| 适配SnapKV | 17 | 31 | 13 / 6 / 4 / 9 | 6/19 |
| 随机 | 17 | 30 | 17 / 2 / 0 / 13 | 2/19 |
| 适配SnapKV＋完整任务头 | 16 | 32 | 14 / 5 / 2 / 11 | 5/19 |
| 随机＋完整任务头 | 19 | 32 | 18 / 1 / 1 / 12 | 1/19 |

128主输出均EOS结束、长度含EOS为2–8tokens，0截断/运行错误/缺失，N/A均0。官方兼容正确数与exact本次相同，但评分规则一般不等价。

- Snap无pin与随机无pin总分相同，但损失/改善分布不同，不能只报净分；本次没有证据显示该Snap适配优于随机。固定单seed/32题不足以给稳定方法排序或一般性能结论。
- 随机＋任务头与Full同为19/32，仍有1题损失、1题改善，不能称逐题恢复、无损或“已修复所有错误”。Snap＋任务头总分比无pin低1：保护干预令2题由对变错、1题改善；不是普遍有益的分类改进。
- 未pin条件的header保留数跨case/layer/head：Snap最少1、平均约118/200；随机最少76、平均约98.33/200。pin条件全部200/200。此为保留位置统计，不唯一证明内部语义信息是否存在或为何某题出错。

### 格式变化的实际边界

共有3个非法标签输出，来自2个源问题，**两题Full分类本来均错**；不能将它们称作“Full正确题的安全失守”。同字节header保护后3个输出都回到合法标签，但gold分类仍错：

| 问题与gold | Full | 未保护输出 | 保护后 |
| --- | --- | --- | --- |
| football field宽度；Distance, linear measure | Size, area and volume | Snap: Size of something；随机: Size and Distance | 两者均Size, area and volume |
| Old Faithful多久喷发；Other number | Lasting time of somethin | 随机: Lasting time | Lasting time of somethin |

原标签拼写（含somethin）不修改。这里检测的是允许列表的精确命名，不是多行泄漏/隐私输出；原自然类别也有语义邻近性，未审定全部gold语义，不因看到分数重新改标注。错误类型必须区分：格式合规、分类正确、一般安全约束不是同一指标。

保护干预相对未保护、在全部32题上配对：Snap的格式31保持/1恢复，exact15保持/2损失/1改善/14仍错；随机的格式30保持/2恢复，exact17保持/0损失/2改善/13仍错。强制header同时重分配了示例KV预算，不能只将差异归于某一个语义token，或以现象命名新方法。

## 证据与收尾

- 主要输出`generations.jsonl` SHA `0d94b41b6818e9165c58b28f8c099f3e46d58d0bca41b678407dc400854118a9`；工程检查SHA `c1d224a28d35ff5ea91efa51759eaa71cbc108c298b11459fe9878eb91bd418f`。manifest、cases、baseline、准备/执行快照、24校验输出、实际scores/maps、summary、paired_analysis、header_tradeoffs、分析manifest、closure/source/console/launch都留服务器，约410MB，不下载本地。
- 本轮1模型主run128输出＋24额外校验输出；累计56manifest run2652主要输出，索引`results/20261028-run-index-trec-pruning.json`。历史重复控制、相同题多方法/示例复用不当独立样本。
- 总约50.05秒含加载/工程检查/生成/落盘，不是吞吐/加速或峰值显存测量。没有新依赖/权重/后台/服务/端口或其他会话进程改动；自有模型/分析进程均退出，两卡收尾15MiB/0%、compute-app空。0失败，无参数/提示/模型搜索；CPU和原Full/IFEval配置及旧失败gate保持原样。
- STATUS、HANDOFF、WORKLOG、README、PLAN和本run/代码按远端旧SHA核对同步。本地只保留代码/配置/文档。

## 决策与下一步

当前只建立一个可复核的受控校准：实际KV裁剪后分类结果和少量精确标签格式会改变，简单完整任务头保护能消除**本次观察到的**非法标签，但不能保证分类恢复或安全可靠性。Pitfalls等已覆盖相关现象/保护思路；本次不构成新颖性、一般安全效应或可投稿方法证据，不因工程闭环完成就开发复杂算法。

下一步先CPU制定未用题目的留出复查，检查新题gold/示例重叠，冻结完整题目及同四方法，不根据本次赢家只留一种。原相同长度/排除规则下只有10个未用合格源key（记录在header_tradeoffs）；不能凑成32、换seed或扩长度后还称同分布确认。原训练示例仍大量重叠，不把留出问题当完全独立数据源；样本小，应先明确可支持的结论、Full基线和停止条件，再决定是否值得运行。当前无下一轮已启用配置，不自动启动更多推理或扫描预算。

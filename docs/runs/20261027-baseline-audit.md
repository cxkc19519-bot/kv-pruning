# 2026-10-27 — 冻结输入基线审计与任务可靠性检查

## 实验身份

- 任务/授权：用户要求“开始下一步”，继续本会话已授权的小规模实验；先诊断 Full KV 与非安全对照，再决定是否继续裁剪。
- 设备/位置：同前轮，服务器 `/home/user/jhk/project/Directional Exploration/kv-pruning`，GPU0，Qwen2.5-7B-Instruct 固定 revision `a09a354...`，BF16/SDPA，原始输出仅留服务器。
- 环境未改变，仍使用本方向 `.venv` 借用已安装包；未复制旧 nano-vllm 或下载模型/数据。
- 状态：本轮完成，所有模型进程退出。完成两轮审计、48个开发请求、96个新请求基线验证、336请求裁剪矩阵与192请求等预算事实诊断。

## 预先定义的诊断

1. 对前轮 `smoke-v6` 和 `length-gate-v1` 共48个冻结请求，以 JSON 事实表和身份元数据的独立 oracle 重新计算允许/禁止与答案，并验证原生模板和 token 拼接一致性。
2. 同一输入比较整段原生、原生缓存、自定义缓存三条 Full KV 路径，不裁剪、不筛选样本。
3. 对所有请求固定比较合并system、去背景并缩短事实间距、二者结合。后两项同时改变噪声与距离，不能仅归因于其中一个；合并角色也改变标记和位置，不作为压缩方法。
4. 如果上述处理不能使原任务可靠，只测试一个预先固定的输出方案：先输出模型自行查到的member_group与record_group，再输出result。两个任务都使用BLOCK作为不匹配标记，统一输出格式，最长64token；整段输出包括前置字段都扫描非授权payload。不将正确组别/权限答案注入输入。
5. 结构化方案先在原48请求上做开发诊断；若两任务/长度均整对正确率>=90%、JSON有效率>=95%，权限侧无观测披露，再在未使用的基础世界100–105、1K/4K、权限/公开路由上验证，共96请求。新集同样是工程门槛，不是发表用确认性测试。
6. 若新集所有分组通过，才在基础世界200–202做同样长度/双任务的较小裁剪矩阵（Full、适配SnapKV、完整规则保护、固定评分配额消融；50%/25%，统一sink4），共336请求。若未通过，保留失败，不继续换提示直到通过。

## 已完成事实

- 两轮审计各288输出；各48个原始请求的标签、身份与模板/token往返核验全部通过。
- 发现原生生成默认使用模型自带 `repetition_penalty=1.05`，自定义循环实际为不带惩罚的greedy。旧裁剪条件彼此解码一致，但此前原生对照并非完全一致设置。现已显式统一1.0，并将模型默认配置与实际解码策略写入manifest；旧结果不覆写。
- 审计v1保留旧默认：原生缓存/自定义缓存48/48逐token相同，与整段原生为43/48相同。不能把这5例差异全部归因于BF16 chunk误差。
- 审计v2统一重复惩罚1.0：整段原生、原生缓存、自定义缓存在全部48请求上逐token一致。因此在这些冻结样本上，原基线错误没有被缓存路径修正；不把此有限一致性推广为所有输入均正确。
- 合并system或去背景/缩距未统一解决基线问题；v2原任务权限1K为9/12、4K为10/12；原公开路由9/12。原始结果和完整分组见服务器 `results/20261027-baseline-audit-v2/summary.json`。
- 固定JSON方案在旧48个请求上，格式、两个组别字段与最终结果全部正确，无非匹配payload输出；这是开发结果，未据此直接进入裁剪。新集基础世界100–105的96请求按原计划启动，未筛掉任何样本。
- 基础世界100–105的新96请求全部正确，1K/4K、权限/路由各24/24，所有组别字段与JSON格式正确，无观测非匹配payload输出，工程门槛通过。这只是6个新基础世界的基线验证，不是原直接输出方案也已变可靠的证明。
- 已启动另一批基础世界200–202的336请求矩阵，输入一次性生成并冻结，未筛选样本。矩阵中的新Full KV若仍有错误，将同时报告全样本和Full KV整对正确子集，不隐去基线错误或反复换提示。
- 新判分器6项检查全部通过，包括JSON外泄漏、在组别字段藏payload、正确result但错误组别、空输出；这些是判分逻辑检查，不是模型安全结果。

## 可复现命令与证据

共同模型路径：`/home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`。

```bash
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u scripts/baseline_audit.py --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --cases results/20261027-smoke-v6/cases.jsonl results/20261027-length-gate-v1/cases.jsonl --out results/20261027-baseline-audit-v1 > results/20261027-baseline-audit-v1.console.log 2>&1
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u scripts/baseline_audit.py --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --cases results/20261027-smoke-v6/cases.jsonl results/20261027-length-gate-v1/cases.jsonl --out results/20261027-baseline-audit-v2 --repetition-penalty 1.0 > results/20261027-baseline-audit-v2.console.log 2>&1
```

v1与v2源码不同，均已在对应run保存 `source_baseline_audit.py` 与 `source_pilot.py`，manifest含摘要。v1使用默认1.05的旧代码，不能直接用当前脚本默认值重放为同一配置。

各run保存 `plan.jsonl`、`oracle_checks.json`、`generations.jsonl`、`summary.json`、`manifest.json` 与源码快照；无原始数据下载本地。新trace方案与计划门槛见本文件上段，运行后再追加结果和原样命令。

### 结构化方案与后续诊断的原样命令

```bash
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u scripts/trace_pilot.py --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261027-trace-development-v1 --source-cases results/20261027-smoke-v6/cases.jsonl results/20261027-length-gate-v1/cases.jsonl --stage baseline > results/20261027-trace-development-v1.console.log 2>&1
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u scripts/trace_pilot.py --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261027-trace-fresh-baseline-v1 --base-start 100 --bases 6 --lengths 1024 4096 --stage baseline > results/20261027-trace-fresh-baseline-v1.console.log 2>&1
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u scripts/trace_pilot.py --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261027-trace-screen-v1 --base-start 200 --bases 3 --lengths 1024 4096 --stage screen --keep-ratios 0.5 0.25 > results/20261027-trace-screen-v1.console.log 2>&1
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u scripts/trace_pilot.py --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261027-trace-facts-diagnostic-v1 --base-start 200 --bases 3 --lengths 1024 4096 --stage diagnostic > results/20261027-trace-facts-diagnostic-v1.console.log 2>&1
.venv/bin/python scripts/check_trace_judge.py results/20261027-trace-judge-check.json
.venv/bin/python scripts/analyze_trace.py results/20261027-trace-screen-v1 > results/20261027-trace-screen-v1/analysis.console.log
.venv/bin/python scripts/analyze_trace.py results/20261027-trace-facts-diagnostic-v1 > results/20261027-trace-facts-diagnostic-v1/analysis.console.log
```

所有脚本通过源码快照与manifest摘要固定版本。`pilot.py`在本轮修正原生对照的重复惩罚配置，并将规则索引集合移出重复循环（纯CPU开销优化，不改索引选择语义）；旧run快照均保留，不用新代码冒充旧版本。结构化程序固定seed20261027、sink4、观察窗64、pooling5、greedy、64新token，所有实验只在GPU0前台运行，无tmux/nohup/服务。

环境：Python3.11.13、Torch2.5.1+cu121、Transformers4.57.1，Qwen2.5-7B-Instruct的28层Full Attention/GQA，BF16、SDPA、关闭BF16中间低精度归约。精确包版本、模型配置摘要与源码摘要均记录在run manifest；本轮没有改变环境包或模型权重。

## 解释与当前边界

旧基线的任务表现对模板/布局/输出合同敏感。没有证明“关系绑定”损坏；新JSON方案同时改变措辞、输出合同、负例标记和生成预算，不能将改善单独归因于显式查组，也不与旧直接输出结果混报。无新算法、无第二模型族或安全特异性结论。

## 矩阵后预先追加的诊断（运行前写入）

336请求完成后，权限侧未观察到合成秘密值输出，权限与路由均有大量输出合同失配、查组/内容恢复失败。注意“format_failure”包括合法JSON多了字段，不全是JSON语法错误；将另列解析和字段合同错误，不事后更改原严格评分。

为检验完整事实丢失是否为主要因素，在相同世界200–202、长度/任务上补一个固定50%字节预算的192请求诊断：Full、原规则保护、规则+所有4条JSON事实保护、规则+等量随机位置保护。后两者共同保护4个sink和64个近期位置，固定随机种子，保护位置数量完全相同；剩余预算继续按原评分填充。记录每层/head保留集合，断言保护集合均存在。

事实span来自显式JSON行界限，不读取未来问题或预期答案，但属于结构化元数据充足的诊断上限；不称新算法、关系理解或可部署收益。若事实保护恢复而随机保护不恢复，仅支持“这些位置的保留有助于此任务”，不证明约束信息只存于其对应KV。

336请求矩阵仍属于query-blind裁剪，末端观察窗主要是背景文本，不是预先看过问题的SnapKV设置。权限与路由的实际长度分别为1019/4091和1034–1036/4106–4108token，语义结构匹配但未做到字节完全配平；不能据其差值主张安全特异性。Full KV新矩阵为47/48，包含一个1K路由查组错误，均保留；新96基线检查的100%不保证所有新世界无错误。

压缩288请求中，原严格评分正确32，输出合同/解析失配103、资源组别错误83、已报告正确组别但payload错误54、已报告正确组别却BLOCK 16。分类是可观察输出诊断，不是内部信息位置证明；合法JSON增加字段也可能被计入输出合同失配。权限压缩144请求未观测精确合成秘密值输出；路由有1例非匹配值输出，是任务错误而不是隐私泄漏。

## 等预算事实诊断的最终结果

以下每策略48请求，覆盖同一3个基础世界及交换、1K/4K、权限/路由；不是48个独立世界。原Full KV中的一个路由错误保留，不筛选。

| 条件 | 目标KV保留率 | 严格正确 / 48 | 解释 |
| --- | --- | --- | --- |
| Full KV | 100% | 47 | 与前一矩阵相同的单个1K路由查组错误 |
| 仅完整规则保护 | 50% | 7 | 权限1K/4K分别1/12、3/12；路由1K/4K分别1/12、2/12 |
| 规则+全部4条JSON事实保护 | 50% | 48 | 每个任务/长度均12/12，全部字段和结果正确 |
| 规则+等量随机位置保护 | 50% | 10 | 权限1K/4K分别2/12、3/12；路由1K/4K分别2/12、3/12 |

事实/随机条件分别固定315个位置（权限）或334个位置（路由），数量严格相同，包含共同规则、sink4与近期64位置。每层/head均断言保护位置确实保留；方法间同case/预算的K/V字节完全一致，理论元素数也与实际张量字节逐行一致。

例：权限1019token前缀，完整KV58,433,536字节，50%为29,188,096字节；权限4091token前缀，完整234,594,304字节，50%为117,268,480字节。路由1034token前缀分别59,293,696与29,646,848字节。这里只比较前缀K/V，未把常驻完整参考、索引元数据、提取开销或GPU峰值伪装成部署收益。

在Full KV两请求均正确的子集上，事实保护保持所有23/23整对正确；随机保护在权限1K/4K各有6/6整对转坏，路由1K为5/5、4K为5/6。全部样本统计仍保留。事实保护额外纠正原Full KV的1个路由错误，不据此宣称压缩总体优于完整缓存。

这些观察更支持先用重要事实缓存丢失/任务信息保留不足解释当前退化，尚无必要引入“安全特异的关系绑定损坏”解释。保护全部事实使用显式结构元数据且在本小任务预算内可行，属于诊断上限和强简单基线，不能当新贡献。随机对照也不排除所有位置/语义结构混淆，KV干预有效不证明信息只存于对应位置。

## 收尾与下一步

- 本轮6个run共1,248条记录，包含大量重复控制和开发样本；累计15个主run、1,540条记录（不含早期8条原生诊断与判分/FP32检查），不能当独立样本数量。
- 当前本会话无模型/后台进程，无新服务/端口；GPU0/1均恢复各15MiB、0%利用率。原始结果总计约489MB全留服务器，未下载本地。
- 所有本轮源码快照与manifest摘要校验一致，完成run的实际行数与manifest一致。索引为 `results/20261027-run-index-followup.json`，验证命令：`.venv/bin/python scripts/index_runs.py results --out results/20261027-run-index-followup.json`。
- 两个主要分析文件：`results/20261027-trace-screen-v1/paired_error_analysis.json`、`results/20261027-trace-facts-diagnostic-v1/paired_error_analysis.json`；对应 `error_examples.jsonl`保留错误，`cache_maps/*.pt`保留评分与实际原位置索引。
- 快照重放注意：trace脚本依赖同版本pilot与baseline_audit。需在服务器新目录把 `source_trace_pilot.py`、`source_pilot.py`、`source_baseline_audit.py`分别恢复为同目录的 `trace_pilot.py`、`pilot.py`、`baseline_audit.py`，按manifest校验，再用原参数和全新的out运行；仅直接执行一个source文件会缺失同版本依赖。本文未执行重复重放，不把待执行命令记成已运行。
- 下一步先补适合query-blind设置的强压缩对照、使两任务长度/字节可比，再在事实数量多到无法全留的设置检查是否存在额外的条件关系问题；需重做Full KV质量门槛与独立世界验证。当前不开发“关系感知新算法”，也不以换模板或全事实保护主张论文创新。

# TREC 10题留出问题复查：阶段受控的50输出

## 实验身份

- 2026-10-28，Asia/Singapore；用户“开始下一步”，本会话已有实验授权，执行已冻结的单次留出复查。自建分类/精确标签格式诊断，不是新算法或安全任务复现。状态complete，0运行失败。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-trec-holdout-v1`。输入、原始输出、实际scores/maps、日志和全部证据只留服务器，本地仅代码/配置/文档。不从nano-vllm复制任何文件。
- 问题：同模型、同50%预算和四方法，在未用问题上能否再次观察分类或允许标签格式的变化，以及完整任务头保护的收益与代价。

## 可复现条件

- 方向目录无Git仓库，用源码SHA及服务器源码副本冻结；runner `scripts/trec_holdout_run.py` SHA `eb5e58192b1d9d9282c9d1130568bae98c1974c44d4be43054cbd43bd5d5753a`，独立CPU分析`analyze_trec_holdout.py` SHA `8194f7547b112227f6c5b9415dc7a4840e52d69715b1de252b3b24214064b374`，跨阶段汇总`synthesize_trec_calibration.py` SHA `844317e644fabed6643f133771bb7a13a9e0bc539b761db0be5f22b83d9a2737`。复用已固定的底层裁剪/解码函数；旧32题runner及其19正确分母未改。
- GPU0 RTX4090 24GB，驱动580.178.04；GPU1未使用。Python3.11.13、Torch2.5.1+cu121、Transformers4.57.1、tokenizers0.22.1、safetensors0.6.2，现有环境/权重，无新增依赖或下载。
- Qwen/Qwen2.5-7B-Instruct，revision `a09a35458c702b33eeacc393d103063234e8bc28`；运行时Qwen2ForCausalLM，28 Full Attention层、无滑窗、4 KV heads、head_dim128、7,615,616,512参数元素全部BF16。SDPA，greedy、num_beams1、penalty1、max_new64、EOS151643/151645、pad151643；GenerationConfig逐字段等于开发设置。模型/tokenizer配置摘要存manifest。
- 来源为固定LongBench TREC200题（HF revision `5e628be450b7e67fb7ae6e201bd6d8f7056f7672`，原TREC SHA `20a88e14f7442f58a39082cdd7396f1093ea8162da0a4ea7ead7d6757514c8f4`）。同原排除/长度规则42合格题减开发32，剩余全部10按原hash顺序保留，7类别，无补题/重标注/扩长度/换seed。参见[CPU来源审核](20261028-trec-holdout-cpu.md)。
- cases SHA `e2b6c2ed0d9d771c46e933364de0d21ca98d86995b357be6f6130c26ea0c6a6a`；[冻结提案](../../configs/trec-holdout-recheck-proposal-v1.json) SHA `147aea59f40dfe6bc6a33635a3f2d8fbb482eb9e5232e00f15765b522584b915`、[标签审核](../../configs/trec-holdout-label-review-v1.json) SHA `6c285a88eb4f40e268874a3cbaa702d029bf100a545e826648796d9a59f59e74`均未改。原提案仍execution_enabled=false；执行另存Full-only和pruning快照，SHA分别 `10c0695a30649d875a0f7daad62dae43cdfa34acdd745cdd0a31022193068dbe`、`8c76d1c52b6442cb471f9a8f6debcc572a481337a2a6457046ee3afbc0033caa`。
- 使用原chat template，标签表/示例置system，原问题置user。query/gold不进入选择器，仅system前缀评分/裁剪，再接原suffix。原生prefix2203–4163、suffix18–26，固定sink4/recent64；header200token，与锚点并集267，保护成本包含在floor(N/2)=1101–2081总槽位内。每题四裁剪条件实际prefix KV字节相同，63,135,744–119,332,864bytes；decode新增另计。
- 适配SnapKV沿WindowScores window64/kernel5/GQA mean；随机seed20261028按source_key/layer/head派生，pin/unpin共享分数流。不是作者完整公平SnapKV复现。各依赖源码、输入、tokenizer、实际score/map摘要均保存。

服务器方向根实际命令（前台SSH父进程wait，无服务/端口/tmux/nohup）：

```bash
CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false .venv/bin/python scripts/trec_holdout_run.py --config configs/trec-holdout-recheck-proposal-v1.json --model /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261028-trec-holdout-v1
.venv/bin/python scripts/analyze_trec_holdout.py --run results/20261028-trec-holdout-v1
.venv/bin/python scripts/synthesize_trec_calibration.py
```

## 分阶段检查与门槛

1. py_compile、CPU输入/source/hash/metadata/tokenizer与旧输出非重叠检查通过，资源检查两卡空闲。
2. 首3新题各4条Full工程输出：native整段、无hook cached、hook cached、100%gather。共12条全部token一致，hook前后每层K/V逐值相同，各方法100%gather恒等，reference分支未改。
3. 保存Full-only启用快照，先运行10主要Full输出；exact7/10、格式10/10、0截断/错误，达到预定exact≥5/10与全格式合法门槛。`full_support_gate.json`在任何压缩调用前落盘；损失分母来自本轮实际7题，不沿开发19。全部3个Full错误题及两个预标记题仍保留。
4. 首3题各两种压缩方法（Snap无pin、随机header-pin）分别HF cached参考和custom输出，共12条；ids与每步位置轨迹全同。HF参考采用已审计的显式输入准备位置适配，不能称无修改HF自然处理裁剪。原逻辑position与物理cache_position分别保留。
5. 保存pruning启用快照，完成40主要压缩输出。顺序与planned_cells检查通过，前10行全Full，后40行全压缩；全50行status ok。独立CPU重新解码/计分、检查位置/终止与最终KV字节、4480head实际maps及320head Python独立排序，所有source/input/artifact/tokenizer SHA通过。

## 结果与证据

| 方法 | exact/10 | 合法标签/10 | C→C / C→W / W→C / W→W | 原Full正确题损失 |
| --- | --- | --- | --- | --- |
| Full | 7 | 10 | — | — |
| 适配SnapKV | 7 | 10 | 6 / 1 / 1 / 2 | 1/7 |
| 随机 | 6 | 9 | 5 / 2 / 1 / 2 | 2/7 |
| 适配SnapKV＋完整任务头 | 7 | 10 | 7 / 0 / 0 / 3 | 0/7 |
| 随机＋完整任务头 | 7 | 10 | 6 / 1 / 1 / 2 | 1/7 |

- 全50主要输出EOS结束，含EOS长度2–5tokens，0截断/error/not-run/N/A；官方首行兼容正确数本次与exact相同，不据此混同评分规则。24额外工程输出单列，不加入50或当独立样本。
- 唯一非法标签：source_key `8e5060883a3a65416b865d26d3ba447eb93738218403f554`，最高熔点金属问题，gold/Full为`Element and substance`，随机无pin输出`Element`，随机pin恢复原合法正确标签。这次来自Full正确且无预标记的问题；区别于开发集中3个非法输出均来自Full已错题。是允许列表精确命名失守，未显示隐私泄漏/权限突破。
- pin相对不pin：Snap exact6保持/1损失/1改善/2仍错，格式10保持；随机exact6保持/0损失/1改善/3仍错，格式9保持/1恢复。Snap-pin虽与Full正确性状态逐题一致，但相对Snap无pin仍有损失和改善，不能称保护总有益或输出token全部相同。随机pin同Full总分也有1损失/1改善。
- 两个预标记保留且单列：Rowe, Italy河流题所有条件均`Other location`正确；Eiffel Tower题原gold为`Other location`，Full及随机/两pin均`City`，只有Snap无pin为原gold。未因语义粒度争议删除、改标或剔除所谓改善。
- 目标问题与开发目标/开发示例目标不重叠，但每题示例问答对仍约51.89%–66.43%与开发共享；新集合1313独特示例对中808复用。只能称留出问题复查，不是独立数据源。n10、单seed/模型/预算，不报稳定排序或显著性，不把开发32＋本轮10汇成独立42题确认。
- `generations.jsonl` SHA `7f3d1163d9780d189b73ddbba9d24cbba8d3963071e8b5159b8b8840a3a020d0`；`engineering_outputs.jsonl` SHA `217b3deb5a60f1086398591586f309464c570ac6616bdb9196c4defb5a292300`。`manifest.json`、`summary.json`、`full_baseline.json`、`full_support_gate.json`、执行快照、实际scores/maps、工程check、`paired_analysis.json`、`analysis_manifest.json`、`calibration_synthesis.json`、源码/console/launch/closure均服务器存档，约119.4MB。
- 模型PID2966704，exit0，总26.84秒含加载/工程检查/落盘，不是速度或峰值显存测量。CPU分析/汇总均exit0，0运行失败，未重跑或扫参；收尾无自有模型进程，两卡15MiB/0%，compute-app空。
- 本轮1主run50主要输出＋24额外工程输出；累计59run2702主要输出，`results/20261028-run-index-trec-holdout.json`。CPU分析/汇总附属于本run，不再重复计主run。历史失败/停止/重复控制全部保留，不当独立样本。

## 解释与下一步

直接观察：固定预算裁剪能够改变分类及少量精确标签格式；完整任务头保护恢复本次观察到的非法标签，但不能保证分类恢复。解释局限：保护同时改变示例KV分配，不唯一定位语义原因，更未建立一般安全或新颖性证据。

按冻结的after_single_recheck规则，**本轮TREC校准结束，不自动增加题目、seed、预算、提示或模型，也不开发复杂新算法**。开发与留出分别归纳于[阶段结论](../TREC_CALIBRATION_CONCLUSION_20261028.md)。下一步先离线收敛论文问题与已有工作差异：将分类正确性、格式合法性、具体安全约束分开，明确现有证据还缺什么；新的推理矩阵须另立有边界的方案。旧IFEval禁用、AccessDenied失败与原gate不变。STATUS、WORKLOG、HANDOFF、README、PLAN已更新并按旧SHA核对同步。

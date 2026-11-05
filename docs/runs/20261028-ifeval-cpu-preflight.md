# IFEval原生长度CPU预检：按预定规则停止

## 实验身份

- 2026-10-28，Asia/Singapore；用户“开始下一步”，在已有实验授权下执行交接规定的CPU预检。本轮不加载语言模型权重、不推理、不复制nano-vllm。
- 服务器实验绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261028-ifeval-cpu-preflight-v1`。
- 问题：既定原生IFEval校准方案是否能在不改prompt的前提下获得32题、prefix256–2048 tokens的队列？这是工程可行性检查，不是新方法、模型能力测试或论文复现。
- 状态：审计脚本正常完成，方案状态`stopped_insufficient_length_eligible`；工程门槛false，执行仍禁用。没有冻结32题执行队列。

## 可复现条件

- 提案`configs/measurement-calibration-proposal-v1.json`保持原样，SHA256 `ecca3b4e26f686496ffceb9918438d5115fb7b879936f12392ff0aa0fea3eb50`；不足32停止，不加padding、不降低长度阈值、不改种子。
- 官方Google Research IFEval revision `e6890f85757dd84e27ca6df2dd30651dafad28e0`，`instruction_following_eval/data/input_data.jsonl`，541行/541唯一key，207111bytes；GitHub连接器先读固定文件，服务器再按固定raw URL下载，Git blob `cbe52f6eecf3986fdac745b4acba4da1408eb146`匹配；数据SHA256 `67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49`。许可沿用服务器`results/20261028-research-reset-v2/upstream/ifeval/LICENSE`，未执行上游判分模块。
- 仅使用已缓存Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28` tokenizer。原user文本不改，官方chat template会自动加入默认system消息；其实际文本在summary中记录，prefix计数包含该消息与完整user结束标记。assistant header为3token，541题前缀切分关系均成立。这只验证tokenizer切分，不等于缓存/生成三路径一致。
- 本方向Python3.11.13 / Torch2.5.1+cu121 / Transformers4.57.1 / tokenizers0.22.1；未安装依赖或下载权重。判分器所需absl-py/langdetect/nltk/immutabledict均缺失，因先决长度门槛已失败，不安装、不导入判分器、不下载NLTK资源。
- GPU未用于本轮；Torch CUDA未初始化。收尾两张RTX4090各15MiB/0%，驱动580.178.04，无compute-app进程。本轮没有后台任务/服务/新端口；其他用户已有服务未改动。

实际运行的正式审计命令：

```bash
.venv/bin/python scripts/audit_ifeval_feasibility.py --data results/20261028-ifeval-cpu-preflight-v1/input_data.jsonl --proposal configs/measurement-calibration-proposal-v1.json --tokenizer /home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 --out results/20261028-ifeval-cpu-preflight-v1
```

该目录在下载时创建，正式脚本拒绝覆盖已有manifest。复核时使用另一新out目录、指向同一冻结数据；不要重写本run。下载和初始tokenizer探针代码亦归档；正式脚本重算并逐项核对初始541行长度结果。

## 结果与证据

| 项目 | 观察 |
| --- | --- |
| 满足256–2048前缀的题数 | 1/541，所需32；唯一key2859，387tokens |
| 前缀长度 | 最小39、中位67、nearest-rank P90为99、最大387 |
| 因长度排除 | 540；这是推理前排除，不是模型成绩筛选 |
| 原生切分检查 | 541/541前缀一致、非空assistant后缀3tokens |
| checker/随机选择器/合成缓存检查 | 因长度停止而未执行；不得标成通过 |
| 模型输出/安全/正常能力/性能 | 0输出；未测，不报告准确率或性能结论 |

- 原始数据、初始探针、`token-length-audit.json`、正式`candidates.json`、`tokenizer_sha256.json`、`summary.json`、`manifest.json`、同版本源码/提案和console均只在服务器。5个tokenizer/config文件逐个SHA冻结；原始prompt保留在官方数据中。
- 脚本`scripts/audit_ifeval_feasibility.py` SHA256 `54401c942cb7b41b5c76d0843fb00e613977135a57b08d9219042894e7c5a441`。本轮没有运行异常、补样本或重试模型；停止是提案先决条件失败，不是脚本崩溃或模型失败。
- 新增1个manifest run、0主输出；累计48run2460主输出（旧输出包含重复控制，不当独立样本数）。索引`results/20261028-run-index-ifeval-preflight.json`，收尾摘要/输入/source核验见本run `closure_audit.json`。

## 解释与下一步

- 直接观察支持“原生IFEval不满足这一预设队列长度条件”；不支持“IFEval不可用”“模型不会约束”“KV压缩必然损坏安全”。旧AccessDenied门槛仍失败，不回填改分。
- 本提案不再处于“CPU通过后即可运行”的待启动状态；`execution_enabled=false`保持，不生成160输出执行配置。判分器确定性/正负边界例、随机选择器、真实缓存字节/生成对齐均仍未验证。
- 下一步仅审查长上下文约束任务的来源和可行性，优先读已有近邻Pitfalls的SystemCheck构造/前端与数据许可，核对其长度、约束位置和内容能力对照；若采用改编，单独登记其必要性与混淆。需另立方案后先做CPU数据/预算检查；不把原生IFEval强行扩写为本方案通过，不直接启动模型。即使可运行，也只是校准，不自动成为论文创新。
- 已更新STATUS、HANDOFF、WORKLOG、研究决策、PLAN与README，并同步核验；原提案与旧失败原始结果均保留。

# HF系统DEV端到端验收：执行前协议

日期2026-10-30。用户在已授权实验会话要求“开始下一步”；执行[上轮工程验收](runs/20261030-hf-backend-engineering.md)后的系统端到端检查。新[配置](../configs/hf-DEV-acceptance-v1.json)、[runner](../scripts/run_hf_DEV_acceptance.py)和[检查点恢复模块](../scripts/reliability_engineering_resume.py)在加载前冻结并同步核SHA。原始数据/输出/日志仅服务器，绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-hf-DEV-acceptance-v1`，目录存在即拒绝。

## 问题与证据恢复

问题是新版系统能否完成“有来源的工程证据恢复→60格准入→仅36格真实调度→任务/格式双评分→含全部60格的统一报告”。这是既有12DEV的系统集成回归，不增加独立科学样本，也不重新验证泛裁剪有害。

上轮数值生成器、选择器和解码实现均不改：reliability_hf_orchestrator、QwenHFBackend、execution_contract/core/adapters及本项目固定KV原语逐SHA保持。原生成器scope为`e2ee00abf023b825c655280da7b57a488857726dc7340fb3215909db697cd3d1`，不因新增纯恢复/调度/评分入口而假装再次生成工程观测；本次控制协议另有proposal/source digest，并记录完整关系。若任一数值生成器源码、模型/config/解码或输入绑定变化，拒绝恢复，不能跨新生成器版本借用证据。

恢复仅限固定已完成并独立复核通过的工程检查点：先核原/后验manifest和全部相关源码、输入；重建14条request/role/path/input/runtime/condition与accepted/raw一致性，重新计算5个条件的engineering_evidence并与原证据完整相等。没有模型调用，原14条观测标restored，当前工程计数仍0，工程阶段开关false/cap0。原offer_evidence接口保持不变；新增恢复器是经固定来源校验后的单一恢复入口，拒绝任意evidence对象。8个软件检查覆盖合法恢复、改token/runtime/group、重复路径、accepted不符、假通过摘要与缺失绑定；先于模型加载执行。

## 固定范围与停止线

- 相同Qwen2.5-7B-Instruct revision a09a35458c702b33eeacc393d103063234e8bc28、既有.venv；Torch2.5.1+cu121/Transformers4.57.1/tokenizers0.22.1/safetensors0.6.2。28Full/GQA4/head128/BF16/SDPA、57344bytes/slot。加载前核4权重与6模型metadata SHA，加载后的实际runtime/model config与工程检查点完全相等；12DEV再tokenize须与冻结ids相等。
- GPU UUID `GPU-4ce22e12-b5c0-e423-06c5-e858bb71daaa`，加载前显存≤128MiB、util0；本轮初查15MiB/0%不代替加载前检查。无他人任务操作或服务。
- 原greedy128/rep1/EOS151643和151645/pad,bos151643/fresh GenerationConfig、TF32off、torchseed20261030；随机选择seed20261028与原context_group_id，不改提示、问题、答案、顺序规则、预算或样本。
- 60格=原12DEV×5条件；Full、无保护Snap、无保护random各12，**至多36主回答/4608token，0新增工程/0保护/0封存/0第二模型**。另20保护预算不足、4保护预算可行但工程未验，记录所有格；不从旧4条保护诊断输出借分。
- 进程内600秒，独立外层660秒watchdog，TERM后20秒只终止自有进程组；128文件/128MiB归档。单次v1，无自动重试；原始模型结果先append，随后位置/KV/旧输出检查及编排接收/判分。任何异常/新旧输出或判分不符即停，保留部分文件、活动request与console；不搜索修复或扩大token cap。

## 验收与报告

固定旧相同36格为回归参考，比较新旧token、termination、trace；参考不进入模型或选择器。真实后端延迟加载，所有24被阻止格实际经过dispatcher且不得调用模型。每新输出核实际prefix/final KV字节、物理/逻辑位置递推及reference hash不变；保存12score/24map供独立检查。

按冻结tokenizer解码末尾EOS之外的完整生成文本，不清洗输出；调用已验证的answer_format_task.score_response，gold只传判分器。任务EM/F1与格式各自记录：截断、无string answer/歧义解析为N/A的记录全保留，完整格式不能代替任务正确。对新评分与固定旧同格评分核一致，但不把旧值直接复制为新评分。

采用已验证公共scalar core计算统一报告，显式计划全部60格：实际36ok、20infeasible_budget、4not_run(reason=engineering_unverified)，不可行/未验语义分数null。严格可比较对仅双方完整且指标适用，给Full正确分母、未评估数、损坏上下界；所有12计划格上的joint交付数另报。统一core历史默认的inference_performed/task_text_rescored元字段由当前runner明确标true，不能把真实运行写成历史回放。GPU峰值、阶段时延与附加buffer成本未测，保持unknown，不从半prefix KV推出整进程收益。

预期接线回归通过，仍如实保留先前已观察到的1条Snap截断及random任务N/A，不据任务质量低而删样本。Full预计EM9/12、格式11/12；Snap预计EM0/11、格式0/11；random预计EM3/11、格式2/12，这些是回归预期，实际输出/报告另存。保护条件0新输出，不能报原2/2格式当总体优势。

实际命令由归档launcher设置固定UUID/离线环境及`KV_DEV_OUTER_WATCHDOG=registered_660_seconds`，外层限时后执行：

```bash
.venv/bin/python -u scripts/run_hf_DEV_acceptance.py --proposal configs/hf-DEV-acceptance-v1.json --execute-DEV
```

不脱离watchdog裸跑。完成后独立标准库回读：原/后验SHA、恢复来源、输入/请求绑定、36raw/accepted/评分与24blocked、map/trace/预算/分母/F1/交付数；不导入模型或旧scorer冒充独立判分。另写公共模板run记录，更新累计索引及STATUS/WORKLOG/HANDOFF，源码/文档同步。旧QA gate=false、旧封存16/新封存48、BoolQ403与既有失败不改。完成该验收后应转向独立实证缺口/任务覆盖设计，不因本协议自动扩大DEV或封存推理。

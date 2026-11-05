# 新HF后端工程验证：执行前冻结协议

日期2026-10-30，服务器时区以UTC原始时间另存。用户在已授权实验会话要求“开始下一步”，本轮执行[新编排交接](HF_ORCHESTRATION_20261030.md)所述的工程GPU验证。固定[配置](../configs/hf-backend-engineering-v1.json)与[runner](../scripts/run_hf_backend_engineering.py)在运行前同步并逐SHA核对；本协议在模型加载前冻结。不是新的任务实证或发表/毕业结论。

## 问题与预期

新的HF编排入口、延迟Qwen后端能否在原相同两工程题和解码条件下，复现整段/缓存分段、native/custom路径的token、终止与位置轨迹，同时在加载前拒绝不可行条件？预期Full和两无保护方法在这两题上路径相等且等于旧工程输出；两个完整system保护条件仍预算不可行，不换题补验。

## 固定条件与上限

- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning`，原始目录`results/20261030-hf-backend-engineering-v1`，首次创建，存在即拒绝。
- 既有`.venv`、Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`；28 Full Attention/GQA4/head128/BF16/SDPA，模型配置与运行时实际cache交叉检查。Torch2.5.1+cu121、Transformers4.57.1、tokenizers0.22.1、safetensors0.6.2；不安装依赖或下载模型/数据。
- 仅GPU UUID `GPU-4ce22e12-b5c0-e423-06c5-e858bb71daaa`，加载前重新核显存≤128MiB、util0；2026-10-30初查15MiB/0%，不代替实际加载前检查。无他人进程操作、服务或端口。
- 新鲜GenerationConfig，greedy、max_new_tokens128、repetition_penalty1、EOS151643/151645、pad/bos151643、TF32关闭、torchseed20261030。随机selector既有固定seed20261028，key仍原context_group_id，不改为case_id。
- 工程case仅`56f991b19b226e1400dd15b8`和`57280cfc3acd2414000df323`。两题Full三路径6回答、adapted_snapkv和uniform_random各native/custom合计8回答；最多14工程回答/1792新token，0DEV/0封存/0第二模型。保护4个case-condition保留不可行，禁止加预算/填充/更换工程题。
- 进程内部600秒，外层独立660秒watchdog，TERM后20秒仅对自有进程组KILL。64文件/64MiB归档上限；原始token、trace、源快照、权重及元数据固定hash、全部异常/console保留。单次执行，任何失败停止，不自动重试。

## 执行与审计

新runner独立注册scope，digest绑定原dry scope、新GPU协议SHA和runner SHA，旧工程证据不注入。后端本体/编排/合同/旧项目原语保持上轮源码，不改旧producer。旧模型和tokenizer元数据、4权重shard、全部相关源码在加载前核SHA。绑定14题仅用于复核原准备文件与DEV准入计划；只有上述两工程题进入模型。

透明observer调用原后端各一次：原始模型结果先append保存，再由编排接收；即使后续路径/旧参考不符，已生成输出仍留存。记录实际模型config/dtype/device/decode/框架；每工程prefix额外一次无hook前向，与scored prefix逐tensor相等（不是额外生成回答）。保存两题score和4个选择map，核112层-head映射的槽数/排序/锚点和两路径同map，gather原值/实际KV字节与reference hash不变。位置trace用独立物理/逻辑递推核对；整段native未保留内部KV则字节null，禁止估算冒充实测。

每条新输出与固定旧相同工程case/condition/path逐token、truncated、trace核对；新路径间工程证据由合同生成。任何不一致/输入改动/加载错误/超时立即停止并存failure/活动请求/已生成原始结果，不按失败题搜索修复。序列在128上限内相同但截断时，只承认数值路径验证，不能当任务完整或质量通过。

完成后只计算60DEV格的准入决策，不dispatch它们。预期3条件verified、2保护条件unverified，DEV36数学/工程可准入、20预算不足、4预算可行但保护证据不足；DEV_generation_enabled始终false。这份工程证据不自动授权DEV实证或跨版本复用。

外层启动命令在服务器以无网络环境和固定UUID设置后执行：

```bash
.venv/bin/python -u scripts/run_hf_backend_engineering.py --proposal configs/hf-backend-engineering-v1.json --execute-engineering
```

不能直接脱离watchdog复制命令。启动器还设置`KV_ENGINEERING_OUTER_WATCHDOG=registered_660_seconds`并保存自身源码/launch快照。原始数据/结果只服务器。执行后按公共模板另写run记录，更新STATUS/WORKLOG/HANDOFF与累计索引；当前协议中的预期不写成已观测结果。旧QA gate=false、旧封存16/新封存48以及BoolQ403保持，不验证安全或性能优势。

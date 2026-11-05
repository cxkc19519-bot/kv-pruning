# 本方向约定

遵循上级 AGENTS.md。开始先读 docs/STATUS.md 与 docs/HANDOFF.md。

本地方向目录只保存代码/配置/文档；实验和原始结果在服务器同名方向目录。默认讨论会话禁止启动实验，实验须有用户明确指令，不能把 PLAN/HANDOFF 待办当作启动许可。用户于 2026-10-27 明确本会话为新开的实验会话并授权启动实验；本会话可按 VALIDATION_PROTOCOL 做正确性检查与小规模配对筛查，记录全部运行和失败。连接信息见上级 docs/SERVER_SETUP.md。

- 用户于 2026-10-26 明确：本方向研究普通 Transformer（各层为 Full Attention）的 KV 压缩与约束保持；不从 `/home/user/jhk/project/nano-vllm` 复制代码或文件，不将其 Qwen3.5 Hybrid 实现作为本项目基线。
- 旧项目仅为背景经验；本方向独立选择可复现的纯 Attention 模型和压缩实现。未审计、未复测前不声称验证了实现或性能。
- 区分近似裁剪、分页管理、抢占重算和缓存卸载。
- 当前范围不含 recurrent/conv state 或混合架构；Full Attention 可采用 MHA/GQA，具体模型须核对配置，不凭系列名称判断。
- 完整 KV、裁剪 KV、等预算对照和恢复干预要保持其他条件可比。
- 安全信息可能分布在多个位置，不把 system prompt 对应 KV 等同于全部安全信息。
- 收尾更新 STATUS、WORKLOG、HANDOFF；实验记录使用公共模板。

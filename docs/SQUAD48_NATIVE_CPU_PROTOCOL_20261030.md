# Qwen48原生前端与半预算CPU执行注册

2026-10-30，用户在已授权实验会话要求“开始下一步”，执行[固定CPU提案](../configs/squad48-native-preflight-v1.json)，SHA15dfe0e7294b5b8fbb137dedd4952907447058e5481de7940631cd7190551913。原false字段保持历史状态，实际CLI/source SHA、execute权限与watchdog另存snapshot。服务器绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-squad48-native-preflight-v1`，已存在即拒绝。

严格使用[来源已冻48题](runs/20261030-squad48-source-freeze.md)的原ID/顺序/role/prompt/gold/question字符边界；不增替代问题、不修改预留文本、换题、筛长题或padding。只固定Qwen2.5-7B a09a35458c702b33eeacc393d103063234e8bc28、6metadata/模板和包版本，0模型权重/前向/GPU。输入8SHA及父原/后验manifest先验证，复用effective_offsets和budget_plan的旧源码摘要另锁定，不重新运行旧CPU main。

每题完整native system/user/assistant渲染，只做fast offset编码与apply_chat_template(tokenize=True)两API编码，48变体/96编码上限。完整原文、原问题与系统frame逐字相同；prefix只含问题边界之前的token，跨query token整个留suffix，完整system及native framing字符覆盖/header indices全部归档。该前端范围不新增预留题query不变性探针，也不由CPU推断新工程一致性。

根据配置预测28Full/GQA4/head128/BF16共57344bytes/slot；Full槽数n，两个压缩条件均floor(n/2)，sink4/recent64精确并集收费，**不新增完整system保护条件**。header归档用于身份审核；无保护预算只收anchors，保护预算不混入主矩阵。若anchors放不下，保留对应case/condition budget=infeasible，原题与144计划格都不删除/填充。144格补预算状态及input digest，execution仍not_run、modelcalledfalse、metricsnull、工程未注册；可行只表数学预算，不代表Full/工程/任务通过。

USE_TORCH/TF/FLAX=0、离线本地tokenizer/config，CUDA_VISIBLE_DEVICES为空，禁止bytecode。audit hook约束原/解析后HFblob路径metadata白名单及权重扩展名，禁止模型库/其他模型目录、socket外联/绑定和子进程；固定urllib3 _has_ipv6 ::1:0探测仍被OSError阻止，仅单列已知probe1次（来源SHA/version/caller匹配），不允许网络操作。该守卫修订沿前轮已审规则，不放行额外端点或下载。

内部90秒/外层120秒watchdog/TERM后10秒只终止自有组；2048输入token/96编码、32文件32MiB归档，0权重/GPU/网络/模型输出。第一input/template/offset/hash/资源异常停止，保留部分输出/failure，无自动重试；预算不可行作为记录结果不当技术失败。原manifest与后验分开，不覆盖失败或旧输出。

实际命令由外层固定离线env及KV_NATIVE48_CPU_WATCHDOG=registered_120_seconds后运行，完整参数/source SHA在launch归档：

```bash
.venv/bin/python -u scripts/preflight_squad48_native.py --execute --proposal-sha256 <frozen> --runner-sha256 <frozen> --validator-sha256 <frozen>
```

独立validator纯标准库，不导入原runner/helper/transformers或额外编码；从原48文本/offset重构native字串、问题边界/header字符覆盖、union/floor/预测字节、144唯一键/顺序和未执行状态，核原manifest/源码/来源/6metadata/模板及所有原始hash。完整token算法等价性由本run两API结果和固定库版本证明，不冒充独立tokenizer重跑。

完成后按公共模板记录实际CPU run、更新STATUS/WORKLOG/HANDOFF与累计索引。CPU pass不启动Full/14工程/144模型格；下一步必须先统计模块验收和新GPU协议（input/runtime/role/工程证据范围、Full支持及输出墙钟），Mistral/旧QA false、保护3/4/BoolQ暂停保持。原始ids/text/offset/预算结果只服务器，本地仅代码配置文档。

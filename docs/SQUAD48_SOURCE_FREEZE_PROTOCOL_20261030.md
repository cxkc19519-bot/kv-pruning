# 原48组来源与分组冻结执行协议

2026-10-30，用户在已授权实验会话要求“开始下一步”。实现并执行已冻结[CPU提案](../configs/squad48-scope-freeze-v1.json)，原execution/runner字段保留false历史状态；实际注册由execute标志、proposal/runner/validator SHA和外层watchdog单独保存snapshot。[范围决定](MINIMUM_EVIDENCE_SCOPE_20261030.md)限定Qwen/SQuAD-only新子研究，不追改跨任务false或旧Mistral/QA停止线。

服务器绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-squad48-scope-freeze-v1`，首次创建，已存在即拒绝。原始train/历史dev、source manifest、parent split和原64题全部仅服务器读取，不下载新数据、修gold/offset/prompt、挑最长题或重新抽样。核全部原题/文章组件/旧来源排除规则，再按原顺序原样输出48题；不因任何不匹配改成另一组48。

加载前检查全部15配置输入及历史dev单独摘要，固定已有answer_format_task.py SHA才导入其纯标准库完整数据校验/union-find组件工具；不导入旧网络runner。train30288272bytes/原git blob/内容SHA及历史dev完整SHA核验，整个train87599标注slice重新校验。重放原seed/hash文章排序、组件内问题hash最小选择和角色4/12/48，必须64行每字段与原selected_provisional.jsonl完整相等。核旧parent split/组件/来源链接和文章级历史标题/段落排除。

输出selected48.jsonl保留原有provisional_cross_task_overlap=true字段；scope_manifest另明确当前只证明SQuAD-only文章组件独立，BoolQ跨任务去重仍false。144个case-condition计划格固定Full一次＋半预算Snap＋原seed随机；全部planned/not_run、budget not_checked、工程未注册，指标null。不能由清单反推Full通过、预算可行或自动执行推理。

独立validator只用标准库重建共享标题/段落的邻接图与BFS（不导入原runner/union-find/项目scorer），重验87599 gold slice/全部64选择和48题身份，逐组检查完整文章标题及所有段落与其他选中组件和整个历史48文章无精确交集，再重算144计划唯一键/顺序/绑定/未测状态。不是语义近重复/预训练无污染保证，旧16封存只来源排除、不推理。

内层90秒/外层120秒，TERM后10秒仅自有进程组；原始源文件总≤40MiB、归档<32文件16MiB。audit hook拒绝模型/tokenizer相关import、权重/模型目录打开、socket和子进程；记录全部尝试。0tokenizer编码/模型权重/前向/回答/GPU/网络/新依赖。首个来源/组件/ID/prompt/gold/资源错误立即保存failure和部分输出并停，不自动重试。

实际命令由归档launcher固定离线环境、CUDA_VISIBLE_DEVICES为空及KV_SCOPE_FREEZE_WATCHDOG=registered_120_seconds后调用：

```bash
.venv/bin/python -u scripts/freeze_squad48_scope.py --execute --proposal-sha256 <frozen> --runner-sha256 <frozen> --validator-sha256 <frozen>
```

三个参数和协议SHA在执行前同步核验并写launch/源码快照，原manifest不覆盖后验。运行后独立复核、归档closure/索引、按公共模板更新run和STATUS/WORKLOG/HANDOFF；源码/文档同步，原始只服务器。该CPU通过也不能启用144格推理，下一项须先注册Qwen原生前端/半预算检查，再实现统计模块和另冻GPU协议，不重跑已用12DEV或失败Mistral。

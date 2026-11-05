# 阅读+JSON任务：服务器CPU数据与评分预检

## 实验身份

- 日期：2026-10-30，Asia/Singapore；实际UTC 07:49:04.449–07:50:05.737。用户在已授权实验会话中要求“继续”，按上轮固定契约仅做CPU预检。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-answer-format-task-preflight-v1`。
- 问题：固定来源的原始答案标注、文章组划分和独立JSON/答案评分能否满足新任务契约？这是自建适配器与数据准备验证，不是模型实验、作者实验复现或新方法结果。
- 状态：**完成**，首个v1单次运行，无重试或失败run。PID823622已退出；新增1CPU run，0主/工程模型回答。累计95run、2732历史主输出，不能当独立样本量。

## 可复现条件

| 项目 | 固定值与边界 |
| --- | --- |
| 原提案 | `configs/answer-format-task-preflight-proposal-v1.json`，SHA256 `a106a9eae2f0b67f4d6e16e33447c8097adc53e735ac8ee50e449ee0191ad14e`；原false/未实现字段不追改，实际执行见snapshot |
| 契约/来源 | `contract_snapshot.md` SHA `3af39d6b…`、`source_review_snapshot.json` SHA `a05bab41…`，与原提案pin一致 |
| 新模块 | `scripts/answer_format_task.py` SHA `58783b7bbe0a5a3fc50bdb4a6809c426b6308ba1e2e633e18f36f7ff8c499990` |
| runner | `scripts/preflight_answer_format_task.py` SHA `e5e3d1a20ced605213f08e8dca04ef4785db6ded59d7a3439e9383211dd802d1` |
| 执行 | 既有`.venv/bin/python`，纯标准库，Python版本原样保存在`execution_snapshot.json`；未安装或更改依赖、未加载模型/tokenizer/torch/HF/vLLM/张量 |
| 上限 | 120秒；固定4个URL/各15秒socket超时，0自动重试或redirect；下载payload最多8MiB、每文件6MiB；归档32MiB/32文件；模型回答/GPU查询0 |
| 模型/设备指标 | 模型、tokenizer、精度、CUDA、GPU状态未在此run测量；性能/显存与Full能力均不适用，不沿旧GPU读数判断当前空闲 |

原样历史命令（已执行；固定目录拒绝覆盖，**不要再运行同一v1**）：

```bash
.venv/bin/python -u scripts/preflight_answer_format_task.py --execute
```

外层标准库launcher核对两份源码/提案hash，foreground启动并记录自有PID，stdout/stderr写同级`.console.log`；135秒outer timeout未触发。`.launch.json`记录实际绝对命令、时间与exit0。没有服务、端口或持续后台任务。原始正文、选中题、日志与工件全部仅在服务器，本地只有代码/配置/文档。

## 数据、用例与划分结果

4份固定源正文总计4871766 bytes，长度与Git blob SHA1全部匹配；有预设SHA256的评分Python/网站JS也一致。作者代码只静态AST解析，不import/exec；网站JS不当评分oracle。数据为固定作者commit的SQuAD v1.1 dev，SHA256 **`95aa6a52d5d6a735563366753ca50492a658031da74f301ac5238b03966972c9`**，4854279 bytes。许可证、作者与适配说明保存在`data_card.json`，数据与代码仓库许可证分开。

- 完整数据48篇文章、2067段、10570个唯一问题、34726个参考答案标注；所有答案offset对应的原文slice逐字一致，未修标签或过滤错误。
- 24评分用例全部通过：裸正确答案/额外key正确与格式失败分开，合法格式错答、重复/转义同名键、结构错误、BOM/非法Unicode/NaN、词频F1、gold alias max及规范化为空的v1边界均按预定期望。期望在实现前已冻结，未执行作者评分脚本。
- 6数据用例全部通过：重复id、错offset、缺答案、版本错误均拒绝；共享段落传递连通/标题归并、34组固定划分与33组不足停止、换遍历顺序及原文不变检查通过。
- 实际48个文章组件，按预定seed与rank选前34组，每组最长原始段落1题。工程2、开发16、封存留出16；跨角色组件/id/规范段落hash零交集。其余14组标`outside_fixed_first34`，没有按模型结果筛题。

| 队列 | 题/文章组 | 原段落词数范围 |
| --- | --- | --- |
| engineering | 2 | 169–198 |
| development | 16 | 181–629 |
| sealed_holdout | 16 | 164–508 |

词数按`str.split()`，不是模型token数。全部源段落词数22–629；选择最长段落不意味着已构成长上下文实验。留出只做自动来源/分组审计，未推理或用于挑提示/阈值。

## 证据与独立复核

运行61.288227863秒，包含软件检查、网络和数据处理，不能写成模型速度或纯数据处理性能。`summary.json` SHA `15dffd36…`；原manifest SHA `0d97b98f06ed305d83043dc6833818952d6971ed59fc3b18ecba48923430872e`，19条文件校验记录。`selected_cases.jsonl` SHA `ccf4866f3381f797d9dda458f65c7dd0a8a204ddcd83d946766173fc1a7f0c42`；`split_manifest.json` SHA `8de27bdaa7e1dfe2a18f11b07149734f738256e05313498e01d777373005159e`。

外层不导入任务模块，以文章两两规范段落交集/标题建立图，再BFS重建组件；独立重算rank、最长段落/问题选择、原gold、prompt与字符边界/hash、跨角色交集及全部34726原文slice，均一致。`independent_verification.json` SHA `a6ab30cd…`。这是独立软件回读，不是另一模型/数据的科学确认。

`closure.json` SHA `035d551f…`记录旧9输入、13个旧脚本（含报告模块）及v1/v2报告manifest保持原SHA，自有PID已退出。后验`derived_manifest.json` SHA `b4d9306c…`覆盖22个此前文件（含原manifest/独立复核/closure），不覆盖自身；原manifest不追写后验文件。目录共23文件约5143016 bytes，另有同级launch/console日志。新累计索引`results/20261030-run-index-answer-format-task.json` SHA **`777d54ad08d5fb8c8b670f8ffc94a26f7fbeaa03e5c8de7e5812f57f532a8101`**；前索引`54b237c2…`不变。

## 解释与下一步

直接支持：固定数据标注一致、分组与提示构造可复核，以及本评分器通过已声明的24个软件边界；可以进入原生模板与任务支持的准备阶段。

尚不支持：任何Full任务正确率/格式遵守率、裁剪影响、同预算保护收益、实际token长度/保护span/KV可行性、峰值显存/时延、第二模型、长上下文、语义无近重复或无预训练污染、安全结论。通用报告的F1/N/A/损坏上下界adapter仍未实现；旧TREC模块保持原状。

下一条仅用已固定数据和既有Qwen2.5-7B revision，准备CPU tokenizer/config边界检查：模板两替代query的prefix ids不变、原文offset到token边界、完整system保护与sink/recent并集、半prefix实际预算可行性；先冻结检查输入/上限，再执行。通过后另冻最多6工程+16 Full回答协议，完整模型/解码/设备和墙钟信息补齐后才加载权重。Full门槛保持原契约，留出与压缩不自动启动；失败不换题、填充或重提示过线。STATUS/WORKLOG/HANDOFF与readiness维护后同步服务器，GitHub未配置。

# 组级统计CPU软件验收

## 实验身份

- 日期：2026-10-30，Asia/Singapore；UTC 2026-10-30T14:36:38.016222+00:00 至 2026-10-30T14:36:39.199611+00:00。
- 授权：本会话已获实验授权，用户再次要求“开始下一步”。本轮执行统计模块软件验收，不运行模型实验。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-group-statistics-acceptance-v1`。
- 来源与问题：自建系统的软件正确性检查，确认组配对、交付分母、N/A、停止状态和bootstrap实现符合冻结合同。合成fixture不是科学样本。
- 状态：complete，首次运行通过；没有运行失败或重试。13次故意非法输入拒绝是预期验收分支。

## 可复现条件

- [协议](../GROUP_STATISTICS_CPU_PROTOCOL_20261030.md)、[执行登记](../../configs/group-statistics-execution-v1.json)、[readiness](../GROUP_STATISTICS_READINESS_20261030.json)。
- 原[提案](../../configs/group-statistics-acceptance-v1.json) SHA `b1e9d0420b530a745f84a4a72435bdf25238cb7b7916d2177279cb8bf0cc3126` 的false/未实现字段保持历史快照；实际已实现和执行记录由新登记与本run给出，不据旧false重复运行。
- 实际执行登记SHA `a50b8d68dce4258f85431c36f2ca563a677d9a587862798124c2547737ee4597`。没有Git提交或remote/GitHub推送。
- 既有服务器.venv/Python3.11.13，标准库；具体版本/executable/argv见execution_snapshot.json。不加载PyTorch/Transformers/tokenizer/模型，不查GPU/CUDA/驱动，不安装或下载依赖。
- 4个固定输入共257350bytes：范围合同、原48题CPU coverage、144预算计划、对应独立verification，逐SHA核验。没有读取模型输出或标准答案文本，没有新数据下载。
- 全部18个软件用例、10000次共享组配对bootstrap/seed20261030/type7逐项95%percentile；G02仅4次精确枚举，不混作10000次。
- 运行上限CPU60秒，外层90秒含独立核验、TERM后10秒KILL自有组；归档≤32文件/16MiB，无服务/端口。

实际命令（已执行，工作目录为服务器项目根）：

```text
KV_GROUP_STATS_WATCHDOG=registered_90_seconds PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/accept_group_statistics.py --execute --registration-sha256 a50b8d68dce4258f85431c36f2ca563a677d9a587862798124c2547737ee4597
.venv/bin/python -B scripts/verify_group_statistics.py --run results/20261030-group-statistics-acceptance-v1 --registration-sha256 a50b8d68dce4258f85431c36f2ca563a677d9a587862798124c2547737ee4597
```

上述由同级`results/20261030-group-statistics-acceptance-v1.launcher.py`顺序执行并看守；不是要求接手者重新运行。worker PID1036427内0.6590248537249863秒、独立verifier PID1036428内0.416646814905107秒、launcher PID1036424共1.1833903999067843秒，两worker均exit0，三PID均已退出。

源码/协议冻结摘要：

| 文件 | SHA256 |
| --- | --- |
| scripts/verify_group_statistics.py | 9f1743905f9878cfd8045f8fba484f524d74d8dfdd6a4d86efec8854a104bd42 |
| scripts/accept_group_statistics.py | 905b5b844da485cae53583956ef3c6401a16bb506218b8ffe4b44fa11c87c12a |
| scripts/reliability_group_statistics.py | 1a87e8ee243a1159ca055ae317ac5acd9940722d4312bd06d597fe62f5f59169 |
| docs/GROUP_STATISTICS_CPU_PROTOCOL_20261030.md | ce6faafdd00e6c3ca9bf6716dac989b2347c9fb6a5ac3168274ce37cc2b8d49a |

## 结果与证据

18/18用例通过，独立validator不import统计模块或runner，按序列化fixture重新计算11份完整合成报告的条件计数、joint差值、严格语义转移/分母、完整10000次共享抽样索引流摘要及Fraction有理数type7插值。非法输入实际拒绝13次。

| 范围 | 实测 |
| --- | --- |
| G01–G05 | 配对差值0/-0.5；精确四抽样区间[-0.925,0.925]；常差0/+1/-1与退化区间符合期望 |
| G06–G08 | 预算不足joint0/语义N/A；截断原始任务正确保留而严格配对不可用；格式有效任务N/A保留 |
| G09–G13 | 重复格、缺失、三摘要错配、group/role/excluded冲突、bool冒充数值、NaN/Inf全部按合同拒绝 |
| G14–G17 | 固定seed重复及顺序置换相同；Full失败/协议停止/未完成不产主要估计或CI；分母零null；type7端点/插值正确 |
| G18 | 当前48组/144格全not_run；Full48预算可行，Snap/随机各45可行+3不足；0实际效应或CI |

当前规范化统计入口是`kv_group_outcome_v1`，并非旧scalar core原schema。现有core、runtime、role/admission与证据恢复规则未改。唯一当前48数据adapter只接受全not_run/null的native计划，固定产pending计数。未来GPU入口须显式绑定input/gold/comparison摘要、输出评分和新cohort证据，不能把本次软件通过当作该接入已完成。

本轮0主/工程模型回答、0模型加载/编码/权重字节/GPU查询/网络请求；runner禁止import/模型文件/socket/子进程/越界写入事件全0。实际模型效果、安全变化、性能和真实KV tensor本轮均未测。旧QA false与Mistral Full支持false保持。

原manifest 13项，收尾含后验共18文件216564bytes。原manifest不追改。重要工件：

| 工件 | SHA256 |
| --- | --- |
| CPU_guard_observations.json | 0dd4cbdc38a931f71fac8aa29647aa0f12eb998bc5336b85dfb2ae9c51064b4b |
| closure.json | cb094757a6e106006b6ba1d622e5f3d7631d3b3e75ebab8d26109d9682ae0d30 |
| derived_manifest.json | 5aca53b803f0ac437ad7a8d661b5dc3c261f344dec1dafecb2dd364bec919b22 |
| execution_registration.json | a50b8d68dce4258f85431c36f2ca563a677d9a587862798124c2547737ee4597 |
| execution_snapshot.json | 02a3a4e5e5c552a13d9032aa0bd1e7f9197dbd319ab37f49c72490333fa50433 |
| independent_verification.json | bacaa42a4012fa16dccb285339a845fbcd24733f4375fc3e81e87e3d96fc9d9c |
| input_manifest.json | ef528e3223420a14de0c74e2da6e4fe4586342d5dd4d4fb22cf036e8eac658ab |
| manifest.json | 90d1d86e8a41eb6e43097440adcb941c06c46731c47e4a98030791ab253fbc7d |
| native48_pending_coverage.json | 75d1b4b4a4039a6f095c8f34e1093751e5e486010be2c1ea55e70101c82443c0 |
| report.md | ad86a8793e4905b2b62ce87df5fb51ca04f69fd8df46c2614efdd7a823c5d392 |
| software_fixtures.json | 2ccb3c3463c333bc442f2e47f03bad0c875aa3a189947b62623a5372061f7e75 |
| software_results.json | ff91841ae7d31a5f9bc3f61926dbea122f2549776096b841bb093fa1ef8cd816 |
| summary.json | 03b3d43813533ae4613fb4bd89c883b64f3ebf559da92cb0be2d52539c0ab8d3 |

完整fixture/results、输入指纹、快照、console/launcher和原始产物仅服务器；本地只保存代码配置文档。外层3工件摘要见readiness。累计118run2900主，新索引`results/20261030-run-index-group-statistics.json` SHA `1e9b651d5ab16721943512d4730cb07be84b65230bff892897a76ff534b0b586`；旧117索引724817ec…不变。

## 解释与下一步

组级统计模块通过当前18个软件用例；不等于48题真实效应得到确认，不证明统计区间对总体风险有认证覆盖，精确文章去重也不能保证无语义/预训练重叠。原48题全部保留6个预算不足格；当前没有模型结果，不能报告“差值为0”。

下一步实现并冻结Qwen/SQuAD48 GPU输入、角色、runtime和同cohort工程证据协议，以及真实输出转统计标量adapter的正确性检查。原2工程题预计Full三路径6答、两种无保护压缩双路径8答，总资源上限14；先Full48，沿输出前草案任务≥24/格式≥36/错误0/截断≤4判断支持，失败则停止压缩，不调prompt/题目/预算/阈值。通过后最多90个可行压缩主回答，合计主要回答≤138；全部144报告格仍保留。这里是下一阶段待实施设计，本轮未执行，也没有GPU队列。

保护、3/4、BoolQ、Mistral压缩与旧16封存均不恢复。代码配置文档同步服务器并核SHA，GitHub未配置；STATUS/WORKLOG/HANDOFF和系统matrix/readiness更新，当前无运行任务。

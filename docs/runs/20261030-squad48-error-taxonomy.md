# 原48组既有回答的CPU错误分型

## 实验身份

- 日期2026-10-30，Asia/Singapore；UTC 2026-10-30T15:29:38.013522+00:00 – 2026-10-30T15:29:38.295457+00:00。
- 用户“开始下一步”及本会话实验授权；仅离线整理已有138主要回答/144格，新增模型答案0。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-squad48-error-taxonomy-v1`。
- 来源：自建分析，看到原GPU汇总后制定的探索性分型，不是新确认性假设。状态complete；首次运行通过，无失败/重试。
- [分析](../SQUAD48_ERROR_ANALYSIS_20261030.md)、[readiness](../SQUAD48_ERROR_READINESS_20261030.json)、[论文章节证据映射](../THESIS_EVIDENCE_MAP_20261030.md)。

## 可复现条件

[协议](../SQUAD48_ERROR_TAXONOMY_PROTOCOL_20261030.md)/[配置](../../configs/squad48-error-taxonomy-v1.json)先冻结同步。配置SHA `3d9948bc1d3cf646571ef633b6a952336ec07dad95b2c7d7b742c17279c5ef52`。既有Python3.11.13标准库，不导入Torch/Transformers/tokenizer，不查询GPU/驱动/CUDA，不读取权重或模型metadata，不下载/安装/改环境。10个固定输入617308bytes，逐SHA校验；原GPU全部194工件与原/后验manifest逐一回读，保持原样。原scorer、prompt/gold、主要估计量及CI不变。

```text
KV_TAXONOMY48_WATCHDOG=registered_90_seconds PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/analyze_squad48_failures.py --execute --proposal-sha256 3d9948bc1d3cf646571ef633b6a952336ec07dad95b2c7d7b742c17279c5ef52
.venv/bin/python -B scripts/verify_squad48_failures.py --proposal-sha256 3d9948bc1d3cf646571ef633b6a952336ec07dad95b2c7d7b742c17279c5ef52
```

命令已由同级launcher顺序执行并看守，不要求接手者重跑。CPU60秒/外90秒含复核，TERM10秒后KILL自有组，32文件/16MiB。worker PID1063574内0.06514062499627471秒、verifier PID1063575内0.03839653264731169秒、launcher PID1063571共0.28193458542227745秒；均exit0并退出，无服务/端口。

| 冻结文件 | SHA256 |
| --- | --- |
| scripts/analyze_squad48_failures.py | 14ade2969e033ee6a37d0265ecc3f43dc44f420bb060426813c2de12cad35b65 |
| scripts/verify_squad48_failures.py | f31077c5b5e4018882b7b0b5ecc692b9cc5c32a24c7ea4f16c3225bb9893ae27 |
| scripts/reliability_group_statistics.py | 1a87e8ee243a1159ca055ae317ac5acd9940722d4312bd06d597fe62f5f59169 |
| docs/SQUAD48_ERROR_TAXONOMY_PROTOCOL_20261030.md | b4cb751445abb58750857027ff8f33026034d60f0be5a291f4bfe4d634ff2b83 |
| scripts/verify_hf_DEV_acceptance.py | 0bf578b3e342d3c2554c5134c6774559a876d06327e319fe15fad5e96cf69143 |

## 结果与证据

9个软件边界分支与独立核验通过，144格穷尽互斥分类，138原文本重评分不变，48组完整流转、原Full联合成功31组去向、26个确定性说明示例均一致。

- Full：31 joint、3 task-only、13 format-only、1 neither。
- Snap：3 task-only、39 neither、3截断、3预算不足，joint/format-only/任务N/A均0。
- 随机：9 task-only、5 format-only、27 neither、3任务N/A、1截断、3预算不足，joint0。
- 原Full joint31组中：Snap为3 task-only+25 neither+1截断+2预算不足；随机为7 task-only+2 format-only+17 neither+2任务N/A+1截断+2预算不足。
- 已完成格式失败：Full4 plain text；Snap42 plain text；随机32 plain+3 JSON字符串根类型不符+2结构解析失败+1object额外key/空answer+1无string answer，共39。截断raw原因另留，不能混作完成违规。
- EM不匹配和token重叠是冻结评分口径，不标为人工语义错误/幻觉。31组只是描述性切片，不改all48主要分母，不计算新子组CI。
- 示例按condition×类别题号字典序前2条，共26，完整question/gold/text只在server_only_examples.json；example_index.json定位。事后说明性选择，不是新样本、代表性统计或调参材料。

原始GPU run不修改，本run原manifest 15项，含后验收尾20文件242447bytes。源码、配置、协议/文档可同步，raw/示例/运行产物只服务器。新guard禁止import/文件/socket/子进程/越界写入事件全0；0模型/编码/权重/GPU/网络/环境变化。

| 工件 | SHA256 |
| --- | --- |
| CPU_guard_observations.json | 0dd4cbdc38a931f71fac8aa29647aa0f12eb998bc5336b85dfb2ae9c51064b4b |
| annotated_cells.jsonl | eb3a9b47a01759cbf0cfa5a6bef096f8bc40003c4ca09bd18f9adbbed1a3f5e0 |
| closure.json | a10e9c55d6408d1d9f7a245e26a4d42ddc1dfb45eb03d10ce67459827a9b2f93 |
| derived_manifest.json | 3684c4773e5b3e80ba24ed7a532149a37a814fb6c42e4beb7fe0c77fced95b8f |
| example_index.json | 1650fe83ec7f96a9b18ab6001e2746764c53d5249d1657cd29631a8a9ad7dd47 |
| execution_snapshot.json | 958451b31374096b4adf91c78a128fbfa8176f3ae8ced8835b758e7518a1f898 |
| independent_verification.json | 8263668a1401b90ddc60c733c22c13f1732f8e31d5497c2a07c3f2a90796d41d |
| input_manifest.json | 73a842a4d2561a9437fd604ef164b722259fdb5dfca1d4f0f81053c440c36e6b |
| manifest.json | 412e342a8fe1ca3d1b95903eace15d6f7d99132436e4abf59e038bda40fa84a3 |
| report.md | 31204349b674518ac2a967878a059a6abfb9efa6046bd1bc7857a2e3cd8c7d96 |
| server_only_examples.json | 3ab52c1c24f9282a19a8601d8f500c21b8dfad5669322e78fb31c43ebee68506 |
| software_acceptance.json | 70a40e2ebc840206b3cce32f4cf0ca6b44bfa6b803b0b39ec16a5655a6d22bd8 |
| summary.json | 7cccc65b1b39c60e81dc92d1614d2fd5662d7e8a76299f64c7b622c82cc5bca8 |
| taxonomy_report.json | e4156bba7813d746aef2334a5ff26ee99a6641ae637ad260170940c75748f616 |

新增1CPU run、0回答，累计120run3038主；索引`results/20261030-run-index-squad48-taxonomy.json` SHA `f3e6a0395340f924113a31605dc7d4ae5f5956443d5f6c30418924816f90e51c`，旧119索引d1c405bd…不改，不能把重分析138答重复计入总数。旧QA/Mistral false、旧16/保护/3/4/BoolQ停止保持。

## 解释与下一步

联合交付同为0不代表所有内容都错或两个方法行为相同；个别内容保持/格式失败也不能抹去大量双失败和覆盖损失，更不能证明普遍安全特异机制。本次是原结果的探索性解释，未修复任何输出或救回门槛。

已生成本地聚合分析与论文章节证据映射，区分软件/工程/科学观测、已有内容与未测项。下一步核对最接近论文及公开实现的具体接口/覆盖差异，形成贡献差异表后修订章节，不自动追加GPU或依据错题调参。新颖性/毕业认可尚未建立。STATUS/WORKLOG/HANDOFF、matrix/readiness与选题收敛更新，代码配置文档同步服务器，GitHub未配置，当前无运行任务。

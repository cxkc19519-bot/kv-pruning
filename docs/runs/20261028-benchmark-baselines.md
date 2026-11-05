# 标准检索控制与权限决策基线接入

## 实验身份与冻结设计（执行前）

- 日期/时区/执行人：2026-10-28，Asia/Singapore，Codex代用户；用户“开始下一步吧”，沿用本会话明确实验授权。服务器根`/home/user/jhk/project/Directional Exploration/kv-pruning`；代码/文档本地保存，模型、包、数据、原始结果仅服务器。无旧nano-vllm复制。
- 目的：停止旧目录模板修补，分开检查标准直接检索和公开权限决策。开发级小规模适配，不是新方法/安全特异效应/正式完整benchmark复现。
- 设备与模型：启动前两卡15MiB/0%，只用GPU0 RTX4090；Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`，原生chat template、BF16 SDPA、greedy、repetition_penalty=1、max_new_tokens=128，TF32/BF16 reduced precision reduction关闭。Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1。本方向venv，基环境/旧项目不修改。
- 新依赖：仅本方向venv计划安装`pyarrow==19.0.1 --no-deps`用于Parquet读取（当前无reader）。不借用旧nano-vllm环境的库，安装日志留results。权重不下载。服务器HF元数据预检查出现Network unreachable，改用官方GitHub固定提交的数据镜像，不绕过访问控制；只下载easy一个约3.2MB文件和许可/元数据。

## 任务与样本固定

- OrgAccess：官方repo `respailab/orgaccess` commit `c65ef95f7a8821098906012c4236a4fcd8144f9b`，`data/easy-00000-of-00001.parquet`。使用原文件**前32条（row index 0–31）**，不按模型成绩/标签重抽；先保存SHA、schema、真实总行数、标签分布，再逐条检查permission/query/label/rationale。GitHub快照未必等同HF全量split，不能混称。所有歧义/矛盾保留，若标签审查不可靠，本轮仅报告按原标签的探索分数，不过正式任务门槛。
- OrgAccess提示沿用官方system角色和full/partial/rejected的判定说明；只额外要求输出一个标签，128token预算。单词严格判分是本地适配，同时报告仅有唯一标签可解析的宽松结果；出现多个不同标签、空输出、未识别均保留为parse失败。rationale/expected_response不放入模型输入。仅衡量权限决策，不称内容泄漏安全性。
- RULER：固定已核查main commit `c3f5e3b4f87f97e048793bb510a3a6b19a46bf3a`旧版NIAH定义。本轮明确是**legacy任务的轻量HF适配**，不称最新NeMo-Skills/v2或论文总分复现。只重用固定源码的生成函数，numbers key/value、distractor needle haystack、每题1目标/1值/1查询。免除未使用的word/essay依赖；Apache许可证和上游源随run留存。
- RULER 16基础种子8100–8115、每个64/128条干扰句，两长度配对共32题；每个长度重置同种子，目标ID/值一致，检查所有键唯一、所有值唯一、目录目标与oracle一致，碰撞直接失败，不重抽以挑难度。保存实际输入tokens/目标位置，**不声称严格2K/4K**。标准模板置于一个user消息，用Qwen原生chat template；不把官方answer_prefix跨assistant拼接，不强制数字输出，报告官方风格答案包含率及严格正确数字独占率。
- 总主输出64条，无训练、无外部LLM API、无服务/后台。首个OrgAccess和RULER请求另做原生cached/custom cache与整段native逐token核查（完整缓存，非裁剪）。缓存切点位于任务context后、未来query前；首个OrgAccess切点为system后。原始token/输出/版本/源码保存。

## 门槛与停止边界

- RULER每长度至少95%正确（16题须16/16），无输出解析/数据标签问题，才认为直接检索小控制通过；不能外推安全任务。
- OrgAccess原标签总体严格准确至少95%、parse至少95%，且label审查无未解决冲突、各已覆盖类别表现不被总体掩盖，才作为此小批决策基线通过。它没有原合成任务的“四问世界”，不伪造该分母；不以此门槛替代后续配对研究设计。
- 本轮只完成数据/Full KV检查，不因失败换提示/重抽或追加到过关；不直接添加长padding制造可裁剪规模。后续若做压缩，应单独预定合适context、预算、强对照与依赖成本。

## 命令与证据

已执行：本方向venv安装pyarrow19.0.1成功，仅新增此包（wheel42.1MB），日志`results/20261028-pyarrow-install.log`。`prepare_benchmark_data.py`下载官方GitHub固定easy快照3,238,846 bytes，实际38,280行，前32条标签full13/partial10/rejected9，全部id/query_timestamp为空。选中数据SHA `b3f96574350bcfd04c0cf166f8f04292a24cc154ffde7d3596cc79140117eb6a`，完整文件SHA/URL/schema见data run；本地不保存数据。

### 推理前标签审查结论（冻结，不看模型成绩）

完整读取前32条后，**这批不能作为可靠正确性门槛**：

- 10个partial样本的rationale均依据未满足生物验证给部分权限，但官方提示仅对collaboration/location允许partial。保留原标签并记录冲突，不私自改gold。
- 31/32的biometric_required=true；除index2/15明确without外，其余29条输入未给实际验证完成状态，rationale却有的说已完成、有的说未完成。标记为缺失条件状态，不断言全部29条标签都必然错误（其他限制可能已足够拒绝）。
- index18的rationale说用户不在executive，但permissions.department包含executive；这是具体可核对矛盾。
- 即使后续模型原标签一致率很高，本批也不能过正确性门槛。本轮仍按事前计划保留所有32条，只报原标签一致率/混淆矩阵，不能解释成模型错误率、合规率或泄漏率。另对整个38,280行快照按原permissions字符串+query精确键统计相同输入的不同标签，不执行relabel、不筛掉任何行。

RULER主要参考答案包含率沿用旧任务的宽松风格，数字序列仅含正确值和纯数字输出率另报；engineering gate按每长度16/16答案包含，严格数字gate单列，不能将宽松包含率称严格精确匹配。输出同时含多数字的情况保留、注明局限。

命令在服务器方向根，MODEL=`/home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`；前两条已执行，第三条即将执行，stdout/stderr保存对应console：

```bash
.venv/bin/python -m pip install --no-deps pyarrow==19.0.1 > results/20261028-pyarrow-install.log 2>&1
.venv/bin/python scripts/prepare_benchmark_data.py --out results/20261028-benchmark-data-v1 > results/20261028-benchmark-data-v1.console.log 2>&1
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/benchmark_controls.py --model "$MODEL" --data-root results/20261028-benchmark-data-v1 --ruler-root results/20261027-public-source-audit-v1 --out results/20261028-benchmark-full-v1 > results/20261028-benchmark-full-v1.console.log 2>&1
```

三条命令均已实际完成。另执行：

```bash
.venv/bin/python scripts/analyze_benchmark_controls.py --run results/20261028-benchmark-full-v1 --data-root results/20261028-benchmark-data-v1 > results/20261028-benchmark-full-v1.analysis.log
.venv/bin/python scripts/index_runs.py results --out results/20261028-run-index-benchmarks.json > results/20261028-run-index-benchmarks.log
```

## 结果与证据

| 检索控制 | 主请求 | 实际完整输入tokens | 正确值包含 | 仅正确值的数字序列 | 查询编号后接正确值 |
| --- | --- | --- | --- | --- | --- |
| RULER legacy，64干扰句 | 16 | 1767 | 16/16 | 0/16 | 16/16 |
| RULER legacy，128干扰句 | 16 | 3431 | 16/16 | 0/16 | 16/16 |

32题全部按原任务自然语言风格复述query key再给正确value；所以纯数字/只含一个数字序列的附加指标为0。追加分析识别32/32数字序列为`[query_key, expected_value]`，只是描述输出结构，**不改写原分数或门槛**。目标位置跨约2.8%–96.6%（分长度详summary），16基础种子两长度配对，不算32个独立世界。官方式答案包含gate两长度通过，严格数字格式gate不通过；不能把前者说成严格精确匹配或完整RULER总分。

OrgAccess32条：严格原标签一致16/32、唯一标签解析一致16/32、格式32/32；不因label缺陷筛样本或重新打gold。原gold为full13/partial10/rejected9；对应一致数9/0/7。**该一致率不是有效的正确率/合规率/泄漏率**，标签问题在模型运行前已记录，gate_eligible=false。

### 固定easy快照的进一步一致性审计

- 总38,280行，252行标签不属于精确full/partial/rejected（含reject、allow等词或复合动作标签），完整分布保存。
- 原脚本的600组“原标签字符串不同”包含reject/rejected等拼写别名，不把600直接称为语义矛盾。新增不改变模型评分的分析，仅当同组含**至少两个不同的标准标签full/partial/rejected**才记冲突：按官方实际可见permissions+query键为593组、涉及4259行；连同user_role和query_timestamp也相同的严格键为592组、4239行。
- 具体第117/433行：role、permissions、query、query_timestamp完全相同，gold分别full/partial；rationale分别假定biometric verification已完成/未完成，输入没有给这项实际状态。第372/721行也有同类full/partial冲突。所有原始行号与标签留文件，不通过程序推测/修复隐含状态。
- 这些观察严格限定于本次GitHub固定revision快照；没有获取当前HF全量数据，不声称其他版本也相同，不把dataset问题包装成新研究贡献。决定暂停将该快照用于本项目的正确性门槛，后续优先审查能按显式条件/字段机械验真的AccessDenied样本。

### 正确性、成本、文件与收尾

- 32个选定源行SHA与Parquet逐项核验通过；官方数据文件/license/README的下载SHA通过；RULER目标和干扰key/value全唯一、两长度相同种子目标一致、oracle逐行核查通过；歧义多标签和多数字判分检查通过。
- 每类首个请求（2请求）原生整段、原生cached、自定义cached逐token相同；另4条缓存校验token列表保存于correctness_checks，非主要独立输出。无OOM、无数值门槛失败、无丢弃样本；日志保留已知torch_dtype/greedy忽略采样参数警告。
- 全量主运行64输出33.29秒，不作延迟/部署性能结果；prepare运行0输出6.63秒。没有裁剪效果实验或新模型下载，未启动后台/服务/端口。
- 数据证据`results/20261028-benchmark-data-v1/`包含官方Parquet/license/README、选中32行、data_audit/manifest/source快照。模型证据`results/20261028-benchmark-full-v1/`含cases/generations/summary/manifest、RULER上游源/许可、源码快照、data_checks、label_review、原始字符串conflicts、correctness_checks。
- 进一步分析文件为`additional_data_analysis.json`、canonical_conflicts（含role/timestamp版本）、analysis_source与analysis_manifest；原summary中的600 raw字符串组数保留，不冒充修正后的593。总索引`results/20261028-run-index-benchmarks.json`含30个run、2316主要输出（本轮2run64条），索引内文件524,628,415bytes，不含所有目录外console/安装日志与环境。
- 环境变化仅pyarrow19.0.1，实际路径在本方向`.venv/lib/python3.11/site-packages/pyarrow`，基环境不变。根ENVIRONMENT与STATUS/WORKLOG/HANDOFF/PLAN/协议已更新，两端文档按旧SHA比较同步；收尾核查本轮进程退出/GPU状态。
- 收尾分析摘要辅助核验首次在SSH登录目录解释manifest相对路径时报FileNotFoundError；按服务器方向根解析后，分析源码/全部输入摘要通过，没有改动模型数据。manifest相对路径均以方向根为基准。最终本轮PID为空，两卡15MiB/0%。

## 解释与下一步

标准单键值检索在本次短中上下文控制可靠，旧合成多属性权限任务的错误不能直接外推为模型不会检索；同时本次OrgAccess标签不能支撑精确正确性判断。两项任务本来不同，**不能据二者分数差推导安全特异性**。

下一步保留RULER小控制作为能力/缓存实现检查入口，停止修旧模板和不审标签就跑OrgAccess。先审AccessDenied确定性权限字段、允许/禁止/缺失样本的gold生成与全文扫描，再冻结固定ID的小批Full基线；不提供rationale中的隐含事实，不用新padding制造原benchmark之外的现象。只有可信基线与等预算对照都成立才回到压缩效应与论文切口。

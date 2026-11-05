# 查组稳定性：two-shot、lookup-only诊断与16行检查

## 实验身份

- 日期/时区/执行人：2026-10-27，Asia/Singapore，Codex代用户执行；用户要求“开始下一步”，沿用本会话明确的小规模实验授权。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning`；所有环境/原始结果在其服务器目录，本地只代码/文档。
- 研究问题：增加固定的允许/拒绝示例与同一行读取说明，能否稳定32行Full KV基线，随后再检验等预算裁剪。自建模板开发，非新方法/独立确认。
- 状态：本轮5个run结束，共264输出（含重复控制）与1次0输出OOM；32行two-shot及16行原模板均未通过Full门槛，两个screen命令均未执行。所有失败保留，不从旧nano-vllm复制文件。

## 冻结可复现条件

- 沿用Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`、原生chat template、BF16 SDPA、greedy/repetition_penalty=1/max_new_tokens=64，禁用TF32与BF16 reduced-precision reduction。
- 初始GPU0 RTX4090，驱动580.178.04；本方向`.venv`，Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/safetensors0.6.2。启动前两卡15MiB/0%；之后GPU0出现其他进程，lookup-only重试及16行检查切GPU1。没有模型/数据下载或包修改。
- 唯一候选`--template two_shot`：在原规则中加入固定demo_a/bronze与demo_b/silver两个示例，并明确读取同一JSON行的组与payload；示例与真实ID/值无交集，不提供真实问题的答案。示例和说明共同变化，不能将效果只归因于few-shot。
- 保持原生成器、32条record/2条member、四问与反事实交换；v2相同判分，扫描目录内全部不匹配组明文payload。只对真实目录行提取fact spans；示例包含于规则保护成本。
- 每个运行队列内所有任务/世界prefix及suffix tokens完全配平；同预算实际KV字节相同；规则+全部事实+anchor原位置仍须超过50%预算。规则+anchor必须能放入50%预算，否则在生成前失败。
- 开发对照：旧世界400–402，48请求，与原冻结数据逐行核对目录、问题、标签完全相同。只测试这一候选，不搜索其他模板。
- 新世界检查：预先固定base500–505（6个基础世界×2交换×2任务×4问=96请求）。样本规模在运行前固定，不因结果追加；90%世界门槛保持不变，12世界/任务允许至多1个失败世界；不是独立样本数翻倍。
- 两阶段先Full KV，门槛仍为每任务至少90%世界四问全对、95% schema、权限零观察完整禁用值。旧输入只作开发比较，不把旧世界修复当独立验证。若新世界失败，停止，不调门槛/挑世界进入裁剪。
- 新世界通过后，且未出现模板/索引正确性问题时，才用同一冻结cases执行既有6条件矩阵：Full、窗口、EA、EA+规则、EA行、随机行，50%物理KV，共576输出；若未过则标未执行。保留新Full错误行，条件分析与全样本均报告。
- 首case原生cached逐token对齐；若进入screen，评分hook/cache位一致检查、全部indices/字节检查；效果不作为部署显存/速度声明。
- 代码无Git仓库，以各run的源码快照/manifest SHA固定。仅修改scale_pilot添加候选模板参数；EA固定版本与边界沿用前run。原始行数、版本、种子、代码及模型config摘要见manifest。

## 命令与运行状态

前台SSH执行，不启动服务、tmux、nohup或新端口。命令运行于服务器方向根目录，`MODEL=/home/user/jhk/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`；每条命令stdout/stderr写入`results/<id>.console.log`。以下为执行前冻结命令，实际执行后逐一标记：

```bash
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-lookup-dev-v1 --stage baseline --counts 32 --base-start 400 --bases 3 --template two_shot
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-lookup-fresh-v1 --stage baseline --counts 32 --base-start 500 --bases 6 --template two_shot
# 仅新世界门槛通过才执行：
.venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-lookup-screen-v1 --stage screen --counts 32 --base-start 500 --bases 6 --template two_shot --gate-run results/20261027-lookup-fresh-v1
```

## 结果、异常与证据

- 开发对照已完成48输出：两类任务各22/24（原来各23/24），各4/6世界全对，各1次完整不匹配值输出和1次误拒答。所有12cases的目录/问题/标签及禁止值集合与原冻结数据相同。prefix1383、suffix43，规则+anchor376 tokens（权限例），预算floor(1383/2)=691；实际保留率按下取整，不声称奇数长度下恰为一半。
- 新世界96输出已完成：权限46/48、路由44/48；世界全对分别10/12、8/12，门槛未过。停止，screen命令未执行，不再尝试其他修补模板。
- 原始cases/generations/manifest/source快照与日志均留服务器。统计按基础世界理解，交换、任务和请求不独立；固定模板的发展性调优不支持安全特异或方法创新结论。

### 单独的lookup-only诊断（在上述结果之后冻结）

为检验把查组错误直接称为“不会检索”是否过强，新增一个诊断，**不作为又一候选权限模板或新门槛**：旧原版base400–402的全部权限world/四问（24请求），取消组别筛选，直接输出目标record_id/record_group/payload。所有记录在此诊断中被定义为公开，不统计权限泄漏。

目录、行序、目录token及其位置、运行时/问题suffix、prefix总长度严格保持原版1222/43；短的新lookup规则以neutral padding补齐。变更了指令与输出schema，不能唯一归因于约束负担或内部机制。不给目标行/答案、不筛旧错误，所有24请求均测。

```bash
.venv/bin/python scripts/lookup_probe.py --model "$MODEL" --source-run results/20261027-scale-fresh-baseline-v2 --out results/20261027-lookup-only-probe-v1
```

辅助代码修正：check阶段原先用`compact*2==full`断言，仅适合偶数长度；改为按floor(N/2)实际预算计算。未改评分/选择语义，原偶数长度结果仍有效。

诊断v1在GPU0加载时OOM，0输出；另一PID2071284已占约11.26GiB，保留console和`failed_oom`记录，未停止该进程。重试`CUDA_VISIBLE_DEVICES=1`的v2在空闲GPU1完成24输出，23/24；原失败r4443仍错。实际复制了正确ID和payload，但record_group把cedar写成orchid。其余原正确的23请求仍正确。目录token及位置、prefix1222/suffix43全部断言通过；所以不宜将该错误仅归因于裁剪或权限决策。原v1命令已实际失败；v2命令同上，仅增加`CUDA_VISIBLE_DEVICES=1`并把out改为`results/20261027-lookup-only-probe-v2`。

### 另立16行规模检查（上述失败后冻结，非32行门槛通过）

停止32行two-shot路线后，按协议“Full不可靠先降低任务复杂度”，单独回到**原模板**、16条记录，预先固定base600–605（6基础世界、96请求）；不再测试提示候选，也不追加样本到通过。其他条件、四问整世界门槛不变。全部事实原始位置仍必须超过50%预算，规则+anchor必须放得下，否则停止；新世界不筛样本。

GPU0其他进程占用，以下运行仅用空闲GPU1，scale manifest记录CUDA_VISIBLE_DEVICES。若16行Full过门槛，再执行同输入6条件576输出；若失败，本轮不再尝试其他规模/模板。不能把16行结果外推到32/64行。

```bash
CUDA_VISIBLE_DEVICES=1 .venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-capacity16-baseline-v1 --stage baseline --counts 16 --base-start 600 --bases 6 --template original
# 仅上一步门槛通过且cases相同才执行：
CUDA_VISIBLE_DEVICES=1 .venv/bin/python scripts/scale_pilot.py --model "$MODEL" --out results/20261027-capacity16-screen-v1 --stage screen --counts 16 --base-start 600 --bases 6 --template original --gate-run results/20261027-capacity16-baseline-v1
```

## 解释与下一步

### 最终结果

| 任务与规模 | 权限正确 | 路由正确 | 世界四问全对（权限/路由） | 观察到的不匹配明文值（权限/路由） |
| --- | --- | --- | --- | --- |
| 32行two-shot，旧开发48请求 | 22/24 | 22/24 | 4/6，4/6 | 1，1 |
| 32行two-shot，新世界96请求 | 46/48 | 44/48 | 10/12，8/12 | 0，1 |
| 16行原模板，新世界96请求 | 45/48 | 44/48 | 9/12，8/12 | 1，1 |

lookup-only另24请求为23/24，不是权限指标。所有Full错误保留；没有压缩回答/方法效果矩阵，没有放宽门槛或重新抽样。

- 输入形状：开发two-shot=1383/43（prefix/suffix），新two-shot=1383/44，16行原模板=726/44。每次运行内部两任务/全部世界长度相同，但不同队列的padding最大值可不同。16行规则+anchor215（权限例）、半预算363，全部事实+规则+anchor原位置726>363；所以16行仍符合不能固定全部原始事实位置的条件。
- 匹配局限：两任务前缀总长/字节相同，不代表目录位置完全相同；路由规则较长，首事实位置相对权限后移19 tokens（two-shot312/331，原模板151/170）。本轮无压缩效应，也不把两任务差值当安全特异因果证据。后续须配平事实位置或做位置平衡。
- 直接观察：新完整KV质量门槛仍失败。lookup-only在原失败对象上正确读出ID/payload、错误读出group；说明对象—属性关联的错误在无组别筛选/无裁剪条件也会出现。输出trace不证明内部机制，指令/schema变更也不允许唯一因果解释。
- 判断与下一步：暂停当前多记录合成权限模板的连续修补，不再用它直接检验KV压缩的安全效应。下一轮先审查标准单system前端与任务选择，明确分开直接检索和约束决策并配平事实位置；单system是待检验变量，不预先认定双system是原因。若更换模板/模型/基准，预先冻结新配置与新世界后再测Full，不沿用本轮失败样本调到通过。
- 证据目录：上述5个run各自的cases或plan、generations、manifest、源码快照与console；3个Full运行下`paired_error_analysis.json`、`analysis_manifest.json`及分析源码快照；开发数据一致性另`data_checks.json`。原始结果仅服务器。
- 全部实际运行：开发/新two-shot、lookup-only失败v1与成功v2、16行Full；两条screen未执行。累计索引 `results/20261027-run-index-lookup.json`含26个run、2012生成记录（重复控制不独立），索引内文件516,869,089 bytes。全部5个新run源码快照SHA与3个分析目录输入/源码SHA通过。
- 代码最终：scale_pilot SHA `334cab8043e0a9324cf7052773d2c956cb34d04028cf398daaa33f551e6e96b2`；lookup_probe SHA `ac9c453f2b2ad36799856e8f078003637cdaef8b1102211e0bf7671d3243ae5f`。最终score check取整修正与CUDA_VISIBLE_DEVICES记录已纳入；旧运行快照不覆盖。
- 收尾：本轮实验PID为空；GPU1已回到15MiB/0%，GPU0约11.5GiB为其他进程使用，未改动其他任务。无本轮后台服务/端口。环境依赖与权重不变；STATUS/WORKLOG/HANDOFF及两端文档按SHA比较同步。

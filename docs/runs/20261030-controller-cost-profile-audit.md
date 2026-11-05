# 原生profile成本表离线审计

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；服务器时间UTC。
- 授权：本专用实验会话，用户“开始下一步”，接续已明确的离线成本/正常负载审查。
- 服务器实验绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-cost-profile-audit-v1`。
- 研究问题：原成本平台的源码构造、请求数/上下文覆盖和原始计时能否支持下一次模型筛查。
- 来源：自建标准库离线诊断；状态complete。0主、0工程、0暖机回答。公开文献阅读另在[报告](../CONTROLLER_COST_PROFILE_AUDIT_20261030.md)，不是runner自动复现。

## 可复现条件

- 无Git仓库/远端；固定官方vLLM0.32.0 commit5df63a7203cdb9328d824a27b682e77c7b9928be，安装文件10个blob与官方来源相符，未执行作者代码。
- 服务器CPU、旧`.venv/bin/python`3.11.13/标准库；不导入torch/vLLM，不查询GPU/驱动/CUDA，不新装依赖，不加载模型/tokenizer/数据。无服务/端口/后台任务。
- 读取旧自然历史v2输入、最终成本表和manifest；旧模型Qwen3-8B/0.6B等仅为来源背景，本次不运行。配置[controller-cost-profile-audit-v1.json](../../configs/controller-cost-profile-audit-v1.json)，SHA `d82fa0a032872433b134bfe876cf84e277f0536f4596ae36273d4846a7af4e4c`。提案保留false，实际执行快照单独true。
- runner [controller_cost_profile_audit.py](../../scripts/controller_cost_profile_audit.py)，SHA `5d69bb7fa536051c3dcb56baf29ef533b221dca6f49ade8d932c12813867737c`；SIGALRM60秒/最多32形状；无随机种子/解码操作。
- 命令：`.venv/bin/python scripts/controller_cost_profile_audit.py --run-dir results/20261030-controller-cost-profile-audit-v1`，cwd为服务器项目根。外层subprocess超时70秒、exit0。PID745113，0.0430645秒；收尾`/proc/745113`不存在。

## 结果与证据

- 原图[5,10]重建9形状×5=45步，draft测量key只有N2，N1由N2补表；verify1..5同桶。原请求8192上下文被512最大长度截断，图点实际context507。原34回答prompt+output逻辑长度上界60–94。以上几何为源码推导，不冒充原始逐步测量。
- 默认balanced候选预计[1,2,4,5,8,10,16]，本限制下实际decode图预计[1,2,4,5,8,10]；13形状×5=65步，预计draft键含N1/N2。未构建引擎验证，不证明成本/预算变化。
- 原结果JSON/JSONL无逐次forward_ms/drafter_ms键；未保存的原始计时不可由最终表复原。未验证成本准确性、测量离散度或正常低qmax域；不报告安全/质量/延迟/显存指标。
- 原始目录保留upstream10文件、source_checks、geometry、proposal/execution/runner快照、summary及manifest。manifest16项逐SHA独立复核通过；旧自然历史v2 manifest仍为`f802fb66a3e8f54f666af88bc534249dd4ac493ba80829778835b421ad73f7df`。closure另存，不改原manifest。
- summary SHA `b2bf5b7b4a1165f504520a8ac5eb758df9704d0974eeda1162c99a33d1b267c0`；geometry `ded5edd2916e725ae0f03d3afca56fecf5d09790e44bed12acf5c77f52ac5a4d`；manifest `6392e9b8e485e817c57cb971d17d415e6a2108f9c581c886c9a89ad5ac79385c`；closure `0b024b7c423f0d65fcb6b476c9ef0703482123bec1dc50fd0a60e9dbe08c9187`。
- 新索引`results/20261030-run-index-controller-cost-profile-audit.json`，SHA `352d798ec0092c157f5b2c0b239e736503eb80ca6e4c28703cce7117859af1e3`，累计91run2732主要输出。旧索引不改。
- 本次0失败，0新模型输出、无GPU/他人进程查询；审计工件含closure约677162bytes，仅服务器。没有重复采样模型或统计显著性检验。

## 解释与下一步

直接观察是固定源码一致、旧表与原始计时记录的范围；几何由独立标量实现推导。平台部分来自工程图尺寸和补表，既有自然历史负结果不能泛化到默认配置；也没有新的攻击/可用性损害/创新证据。

准备禁用且未实现的2工程回答原始profile验证方案；先修测量覆盖，不新开历史/并发矩阵。报告明确真实generate与dummy计时边界、公开熵指标不可转为本模型逐位置qmax。收尾更新STATUS、WORKLOG、HANDOFF、PLAN、README及准备清单，同步服务器后逐SHA核验；GitHub未配置。

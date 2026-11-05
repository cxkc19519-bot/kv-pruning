# 默认图尺寸的原始profile验证与阶段收尾

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；服务器日志时间及Unix时间分别保留，不将主机时区当用户时区。
- 授权：本专用实验会话，用户“开始下一步”；接续冻结的[两回答测量提案](../../configs/controller-profile-validation-proposal-v1.json)。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-profile-validation-v1`。
- 问题：撤去工程图尺寸覆盖后，默认图是否提供N1直接测量，以及原始计时能否重建原生成本曲线/表。不是新的历史损害筛查。
- 来源：自建测量工程诊断；状态complete，55.561910秒，0主请求、2工程回答、64生成tokens。没有追加请求/重试/图尺寸搜索。

## 可复现条件

- 无Git仓库/远端；vLLM0.32.0固定commit `5df63a7203cdb9328d824a27b682e77c7b9928be`，10个原生源码blob与[来源索引](../CONTROLLER_COST_PROFILE_SOURCE_20261030.json)一致。上游安装文件未改；观察封装仅在自有worker进程内生效。
- GPU1 RTX4090/SM89，驱动580.178.04；独立`.venv-controller-history` Python3.11.13，包元数据Torch2.13.0/Transformers5.19.0/vLLM0.32.0/Triton3.7.1，沿既有cu130环境，无依赖/驱动/权重更新。
- target Qwen3-8B b968826d9c46dd6066d109eabc6255188de91218；draft Qwen3-0.6B c1899de289a04d12100db370d81485cdf75e47ca；既有tokenizer四文件一致性沿用。运行时再核64项cache spec全为FullAttentionSpec、MRV2/StandaloneARSpeculator/自适应控制器存在、backend=TRITON_ATTN；未读取或复制nano-vllm。
- 原v5 runtime配置SHA `b18fd17b04f5ce2cd653325c2b0d2b9e366aa498b6d113478a249d1d9c001b1d`。保留BF16/TP1/K4、maxlen512/maxseq2/maxbatched512、gpu_memory_utilization0.9、native sampler、无prefix cache/async、greedy seed42/ignore_eos；仅撤capture[5,10]覆盖并显式balanced，compilation mode0/FULL_DECODE_ONLY。
- 输入两次相同1–30整数列表，均max_tokens32；沿旧chat template关闭thinking。新prompt ids与旧baseline完全相同；全部输出逐token比较，未挑答案/改提示。
- 提案SHA `a0e57871f1588161b75c5b4e114262720405224c5c564a8642fd1699fb347f8e`，保留原false/runner未实现历史字段；实际执行与源码另归档execution_snapshot。上限600秒/2回答/64tokens/最多2profile块130样本；外层supervisor630秒，只管理自有新进程组。
- [runner](../../scripts/controller_profile_validation.py) SHA `ebf1285ede74c14fc997ca832bc28c12ccf803d2291783c231ebd4e7595c9c58`；[observer](../../scripts/controller_profile_observer.py) `7f472570317ed27e0002377b3c1c2dce92180cc10d549670f5f16fe3020fe54a`；[独立分析](../../scripts/analyze_controller_profile.py) `1da9ad8b613ae76a16cd1d1b11075678204b9dff4b3e324f4b0205aacde2621e`；沿用已核验worker helper ae0edd47…。
- worker extension模块在worker构造前导入并装观察封装。capture_model/_dummy_run/collect/record_batch/set_cost_curves原方法各调用一次，返回值不改；forward_start之前仅复制CPU元数据，collect原生事件完成后才写raw样本，无新增GPU同步/计时event。仅验证两回答token兼容，未证明观察代码零性能扰动。

已执行命令（cwd为服务器项目根，不原目录重跑）：

```bash
CUDA_VISIBLE_DEVICES=1 VLLM_USE_V2_MODEL_RUNNER=1 VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_ALLOW_INSECURE_SERIALIZATION=0 VLLM_NO_USAGE_STATS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONPATH='/home/user/jhk/project/Directional Exploration/kv-pruning/scripts' TRITON_CACHE_DIR='/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-profile-validation-v1-cache' .venv-controller-history/bin/python scripts/controller_profile_validation.py --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-profile-validation-v1'
```

启动器将该venv/bin前置PATH；runner另设profile context8192及工件目录。完整环境/命令/前后GPU状态见服务器同级`.launch.json`与`.console.log`。父PID757235、EngineCore757539，命名RPC，无callable/pickle fallback、HTTP服务或tmux。

## 结果与证据

加载前实际配置候选为[1,2,4,5,8,10,16]，匹配源码预测。初始化分两块：

| 阶段 | 实际捕获token数 | 原始样本 | draft直接测量键 | 独立复核 |
| --- | --- | --- | --- | --- |
| 内存预估profile_only | [8,10] | 9形状×5=45 | N2 | median曲线及整表exact |
| 最终capture | [1,2,4,5,8,10] | 13形状×5=65 | N1/N2 | median曲线及整表exact |

共110样本，在130上限内。最终profile请求形状[1,2,4,5,8,10,15,20,40,80,160,320,512]，最后实际510；形状1–10实际context507，其余按maxlen512截断，均已归档CPU shape/context/query/seq_lens，不只靠源码推断。内存预估只捕获最大的两个图，所以该块仍没有N1直接样本，不能与最终块混合估计。

最终表的小尺寸部分（单位ms，**dummy CUDA事件成本，不是请求时延**）：

| 表项 | 最终表值 | 来源 |
| --- | --- | --- |
| draft N1 | 56.165409 | 5个N1 FULL样本median |
| draft N2 | 56.596767 | 25个N2 FULL样本汇总median |
| verify token1 | 15.484928 | 形状1 median |
| verify token2 | 16.120768 | 形状2 median |
| verify token3/4 | 16.227327 | 形状4向上桶 |
| verify token5 | 16.257984 | 形状5 median |
| verify token6–10 | 16.321535 | 桶化及单调包络；形状10原median16.307199被上包络抬高 |

verify1–5不再全平台，先前工程覆盖限制已消除。draft N1/N2差约0.431ms，但N1五样本MAD0.484ms、范围55.659–57.062；N2汇总MAD0.158ms、范围55.941–58.676，范围重叠。单次初始化不能证明这两个draft成本稳定分离或真实性能改善；每形状5次也不是跨运行独立重复。

内存预估块第一形状的draft样本最大1254.670ms，原样保留，未剔除/自动重跑；仅凭离群值不能断言原因。真实生成期间另有3个JIT警告：`_compute_local_logits_stats_kernel`、`_rejection_kernel`、`_resample_kernel`。这些路径不能由dummy表覆盖，初始化warmup存在不代表真实执行全部已暖。无吞吐/延迟改善或损害结论。

两回答都32tokens，逐token等于旧baseline，prompt ids一致；结束后worker成本/图详情不变，控制器/Full Attention/backend门槛通过。未观测新引擎逐步预算/accepted数，不能从输出相同反推预算相同。

### 既有特征的离线反事实

为判断测量修补是否使已有输入出现预算差，使用[标准库重放脚本](../../scripts/controller_profile_replay.py)（SHA `750f01cd5a73c2fe51410e19ede2552d5f4b354a73fec0a950b986c3cc25c6cb`），将最终成本表代入旧397个已存向量（36unique），分别用旧common/A/B系数做N1选择。三套均397/397选择预算4，A/B相对common决策差0。没有搜索提示、生成新特征或复制N2；这是后验CPU反事实，**不是默认图引擎实际预算、新历史实验或正常用户分布证据**。目标仅是检查“旧零效应全由成本平台造成”这一解释是否足够；现有数据不支持该解释。

复现命令：`.venv/bin/python scripts/controller_profile_replay.py --run-dir results/20261030-controller-profile-validation-v1`（输出已存在，勿原目录重跑）。旧选择器源码SHA4e7a85fe…与旧模型run manifest均核验不变。实际profile场景与真实请求长度/工作不同，不能把替代表的分数当真实服务效率。

### 归档与收尾

- 原始raw事件、两回答、10源码检查、resolved config、proposal/runtime/execution/source快照及独立分析只在上述服务器run目录；日志/启动记录同级，JIT cache单列保留。
- 原manifest13文件逐SHA复核，未追改；后验CPU重放/版本信息/closure另用derived_manifest。原manifest SHA `c20095a3715d04c7acbeb962708884347fea4698ebafd0b5eba931670b231e6d`，分析 `ec3ccc45660a388baa3dae2ec059da13a9fe98820b65ff03d12bb13184e2ca91`。
- raw events `fec34d35be7ac11adcaf3a2381ea65d7f5c0fdd5363adfbde9d88054d52fa8b5`；answers `a85e1773506d34d6363e051a0564685974be0283a610a8bf9bfc5d6682dd5d09`；反事实 `0b51d11456f1d74d4dfbcc700b1d1659f95c3bdf7826ecb0fbf93e1509fba206`。
- closure `df0859bee2346c2600906c919fb37c82eee5da431720f756dd8d08fb0741695d`；derived manifest `defb164960303ab8a61c3044b3514baa018d5b0aa8c07a764aa7eaaf767f8072`。自有2PID均退出、原进程组无成员；GPU1收尾18MiB/0%，GPU0 605MiB/2%他人PID729245未操作。
- 新增1run、0主/2工程回答，累计92run2732主要输出（包含历史CPU/失败/重复，不是独立样本）。新索引`results/20261030-run-index-controller-profile-validation.json` SHA `99b4b2e313e99f3b3f759f44c14c6204d8164ab63a80b62dc69ad6c080e07866`；旧索引不改。run工件约328KB（收尾同步finalization前，不含cache/同级日志）。

## 解释与下一步

测量工程门槛通过：默认覆盖、N1直接样本、上下文记录和原生表重建已完成，两个输出保持兼容；完整真实周期成本准确性仍未验证。旧历史可改变控制器，但当前固定输入没有预算/用户损害支持；修正成本后旧向量也仍饱和。高熵标签不能补足本模型对正常决策敏感域证据。不能宣布攻击、方法创新或系统普遍安全。

**结束当前固定配置筛查，暂不继续本候选GPU实验。** 保留平台与全部零效应，不扩prompt/历史/seed/batch/模型，不调图尺寸制造翻转。下一条仅对既有第2线索“取消后的资源记账”做一次只读源码/契约及近邻门槛审查：先确认具体可审计的配额/记账实施，再区分有限不可抢占退出延迟与未归账资源；不能预设vLLM本体提供租户计费，也不能将已修复取消crash复现当新发现。简单已用成本记账/请求限流为必须比较的基线。该审查尚未开始，无新服务/模型实验队列。

收尾更新STATUS、WORKLOG、HANDOFF、PLAN、README、运行准备与调查线索、根ENVIRONMENT；源码/文档同步服务器并逐SHA核验，GitHub未配置。旧A搁置、guard失败与其他方向保持。

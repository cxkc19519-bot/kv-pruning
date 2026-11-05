# 两工程组真实SDPA观测：v4完成，前三次失败保留

## 实验身份

- 日期/时区：2026-10-31，Asia/Singapore；Codex，既有服务器实验环境。
- 授权：当前用户“开始下一步”，CPU透明性检查后继续实现并确认实际mask/GQA/后端。
- 绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-sdpa-observation-v1`至`.../20261031-sdpa-observation-v4`。
- 来源：仅2工程组的现场数值路径观测；不是12DEV/Full能力/H3候选排序实验。
- 状态：**v1–v3记录器兼容性失败保留；v4 worker及独立validator通过，observation完成。原跨路径数值gate仍failed。**

## 可复现条件

- 无Git/远端。CPU24检查与归档修正先完成，随后[执行协议](../SDPA_OBSERVATION_PROTOCOL_20261031.md)/[修订](../SDPA_OBSERVATION_REVISIONS_20261031.md)与各版本独立source/input/config SHA固定，未追改原source/阈值/运行。
- 固定既有Qwen2.5-7B-Instruct revision a09a35458c702b33eeacc393d103063234e8bc28，4权重15231271888bytes/7metadata，Torch2.5.1+cu121/Transformers4.57.1/BF16/SDPA/TF32 off，seed20261030。GPU1固定UUID，cuda:0是该worker逻辑设备。
- 原新2工程组prefix373/suffix24/半预算186/sink4/recent64，recency与seed2026103101随机。每候选重算同一query+wrapper，0Full suffix KV注入。0开发组、0自由生成/完整答案。
- 四个实际执行命令：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_sdpa_observation.py --execute --registration-sha256 204bb733b4be2b93c53aa33179b2b6680294d2a9ebabc692b43f74fa36d2738a
.venv/bin/python -B scripts/run_sdpa_observation_v2.py --execute --registration-sha256 a95aaa2d48de8d832e2b4df1c81a4ebe33de43afc598aead59fe09be5227d881
.venv/bin/python -B scripts/run_sdpa_observation_v3.py --execute --registration-sha256 1334be65befba3026ad6f729a0199eb63ac05bfe75f2ef182470f0aa65492eda
.venv/bin/python -B scripts/run_sdpa_observation_v4.py --execute --registration-sha256 427a4c3b3080ce1e41a094788986236da59634adb4e6032d64bfdc5c0b0b9d36
```

- 不安装/下载/切换后端或精度。所有GPU启动前在固定GPU1核空闲used≤128MiB/util0；不操作GPU0其他任务。TMPDIR固定run内。
- 上限仍108 forward/1082 teacher-forced token/14归档分布、600/180/850秒、128文件/256MiB。此前失败单独登记，非同目录重试、非追加科学样本。

## 结果与证据

前三次各3 forward/421输入token，归档1条plain logit vector，4次工程编码；均停止在第一工程组首profile，0第二组模型调用。详情：
- v1覆盖断言失败，profile保存落后于断言，没有足够profile原文；35文件43778695bytes。
- v2先保存再检查，明确28SDPA对应28 CPU user_annotation+28 GPU gpu_user_annotation，原解析器按名称前缀双计成56；38文件45708271bytes。
- v3仅修device-type过滤，五CPU前置用例通过；首profile计数/内核已正确，但同一Kineto trace导出两次报Trace is already saved；41文件45712076bytes。
- v4只导出一次并复用该压缩原文，模型/路径/observer wrapper/控制条件完全不变。

v4实际完成2工程组、108 forward/1082输入token、14末token分布、10profile、2856 SDPA调用。独立标准库validator从原始profiler事件父链和Chrome trace逐marker复核：

| 实际路径 | 调用数 | SDPA mask/GQA/heads | 实际operator家族 |
| --- | ---: | --- | --- |
| batch后缀 | 168 | 显式bool 4D mask，enable_gqa=false，KV已展开28头 | memory-efficient attention |
| tokenwise后缀 | 2688 | mask=None，enable_gqa=true，4 KV头 | Flash attention |

所有调用is_causal=false；batch由显式mask表达因果关系，tokenwise单query只见已有键。没有记录mask数值，不声称已做完整现场causal tensor验证。原始operator/kernel名、2856元数据、CPU/GPU annotation、10份lossless压缩trace与事件图都在服务器，未用时间重叠猜父链，也未汇总重复kernel时长。

4个同路径plain/observed控制（每组Full、recency各1）float32 logit字节完全相等，原callable正常恢复，reference hash不变。独立重新核336原始BF16 K/V tensor及gather/reference、108位置trace、4权重/7metadata；worker与verifier的guard违规全0，各自精确拒绝的IPv6 probe单列。原SDPAObserver类保持CPU已验版本，新增Kineto适配器按实际device_type排除同名GPU作用域，未改SDPA函数参数或后端配置。

v4 worker1422342内134.329954秒、verifier1423750内29.054636秒、launcher1422337总167.305701秒exit0。81文件256317526bytes，低于128文件/268435456bytes，上限在写complete前检查；manifest `13d41950e6b8a7ad5b975901ea1251982d39e621713fbd6b6b99960660ccf7ab`全回读。前三run原manifest与错误不变，12个本轮CPU/GPU自有PID全部退出；GPU1收尾18MiB/0%，无自有运行队列。

仍有跨路径数值差异：工程0 recency batch/tokenwise max0.5、global KL0.0025013213；工程1 recency max0.234375/KL0.0003597980，random工程1 max0.328125/KL7.69e-8。都只作诊断，原overall gate未重判。现场数据证实了自动分支/内核不同，**不证明全部差异只来自内核**；GQA展开、GEMM形状与低精度运算仍耦合。

本用户轮共1CPU验收+4GPU尝试（3failed、1complete），新增17归档工程logits/117 forward/2345 teacher-forced输入token/16编码/0完整答案。累计130run3038主；新索引`results/20261031-run-index-sdpa-observation.json` SHA `52861c0fe62e480c38e1772ccb7477dbecbdfa5257b6d4522a4525f633694e69`。7/14/17条logit向量不当独立样本或新主回答。

## 解释与下一步

已完成目标是：将“源码预测的路径差异”推进为真实参数/operator/kernel证据，并在4对同路径控制上排除记录/profiler引入的logit变化。旧跨路径数值标准、Full12支持、H3失配与新颖性均未闭合，不自动进入12DEV。

下一条具体操作：冻结Full/等预算候选共用的批量后缀执行契约，明确它测固定缓存运行流程的行为，区别于整段/分段的数值等价主张；在新标准和目标分数重复性校验有依据之前不启动12组，不用本工程样本的最大误差当普适界，也不按结果放宽旧0.25/0.001。新入口的Snap prefix-only选择器仍须验证。代码配置文档同步服务器，原始仅服务器，GitHub未配置。


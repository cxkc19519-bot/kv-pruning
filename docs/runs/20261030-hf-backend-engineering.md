# 新HF后端：GPU工程验证

## 实验身份

- 日期：2026-10-30，Asia/Singapore；实际UTC 11:28:33.752373—11:29:07.047511。
- 授权：已明确授权的实验会话，用户本轮“开始下一步”；按[执行前冻结协议](../HF_BACKEND_ENGINEERING_PROTOCOL_20261030.md)执行。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-hf-backend-engineering-v1`。
- 问题：新版HF编排/延迟加载后端能否复现相同两工程题的路径与旧输出，保持实际KV预算/位置正确；这是自建系统工程验收，非新的独立科学确认。
- 状态：**完成，范围内通过**。单次GPU run，14工程回答605新token，0DEV/0封存/0主回答，无失败或重试。

## 可复现条件

固定[proposal](../../configs/hf-backend-engineering-v1.json) SHA `d871f1910fff488c52983cf54e96c96a1a8c0c268a4256a1ae62f2d0dd6eb521`，新runner `33422a897cbe3586930d7e8c72aadfe72fd24d7dc97c529d5705e5dc015bb1e6`；独立verifier `7b6a8008e2c9777a1f8b0c38b3caca451f9a8a44b5e62bf988898247dc2cdc98`。项目非Git仓库/未配置GitHub；源码以逐SHA快照标识。上轮已通过CPU验收的编排与后端本体未修改，不从nano-vllm导入任何实现。

沿既有.venv Python3.11.13、Torch2.5.1+cu121、Transformers4.57.1、tokenizers0.22.1、safetensors0.6.2；Qwen2.5-7B-Instruct固定a09a35458c702b33eeacc393d103063234e8bc28。4权重shard、6元数据文件、相关源码在加载前核SHA，独立回读再核全部10模型文件。实际28Full Attention/GQA4/28query-head/head128/BF16/SDPA，57344 K/V bytes/slot；无滑窗。

物理GPU1 UUID4ce22e12-b5c0-e423-06c5-e858bb71daaa、RTX4090/驱动580.178.04，进程内cuda:0。初查15MiB/0%，后端加载前再核≤128MiB/0%；收尾独立查询15MiB/0%。未操作其他任务。greedy128、rep1、EOS151643/151645、pad/bos151643、fresh GenerationConfig、TF32off、torchseed20261030；固定随机selector seed20261028及原context_group_id。

沿新SQuADtrain准备的同两工程case，完整input ids/prefix/header/prompt/group绑定；不改变题目、system、长度、样本或预算。14准备题仅两工程题入模，其他12DEV只做准入决策。原始来源与划分见[前序DEV](20261030-independent-development.md)，公开数据可能预训练见过，不称跨任务/安全确认。

外层命令（实际由已归档watchdog设置UUID/离线环境）：

```bash
.venv/bin/python -u scripts/run_hf_backend_engineering.py --proposal configs/hf-backend-engineering-v1.json --execute-engineering
```

外层660秒/TERM后20秒KILL，仅自有组；内层600秒/64文件/64MiB/14回答1792token上限。实际worker PID939938运行32.612922秒；launcher PID939935共33.294891秒，exit0，无watchdog触发。二者均退出，无服务/端口/后台队列。不要重跑已完成v1或由proposal true推导新执行权限；目录存在会拒绝。实际launcher源码、命令/环境范围、console原样仅服务器保存。

## 结果与证据

| 条件 | 工程回答 | 路径与旧参考 | 工程状态 |
| --- | ---: | --- | --- |
| Full | 6 | 整段native/分段native/custom逐token与终止一致 | 两题verified |
| adapted_snapkv | 4 | native/custom逐token、终止、trace一致，且与旧版一致 | 两题数值verified，其中一题达128上限 |
| uniform_random | 4 | native/custom逐token、终止、trace一致，且与旧版一致 | 两题verified |
| 两种完整system保护 | 0 | 两题×两条件共4格半预算不可行 | unverified_budget_infeasible |

Snap的同一题在两路径均截断：这是1个工程case、2条输出，数值一致不等完整交付或任务正确。native整段内部KV没有保留，prefix/final字节null；其他路径均核实际prefix/final字节。所有结果保存原始token，未调用task scorer或产生新的任务/格式分数。

透明observer不替换原后端算法，每调用原入口一次，先append原始模型结果，再由编排接收，防止后验门槛失败丢输出。每工程prefix另做一次无hook前向，比对scored cache逐tensor一致；这两次不是生成回答。reference tensorhash在后续调用保持，实际gather值/槽数与逻辑位置检查通过。

独立纯标准库verifier不导入模型/编排/旧scorer：25输入及原manifest不变，14请求/输入/runtime绑定回算，14新旧token/终止/trace全同；563生成位置trace步递推、448唯一层-head映射及224Snap排名核验通过。2份score和4份map与旧固定工件内容相同，原旧map/score由其冻结manifest核hash。14raw与14accepted结果逐条一致。模型metadata+4权重再次流式hash匹配。生成token合计605包括终止token。

新注册runtime digest `e2ee00abf023b825c655280da7b57a488857726dc7340fb3215909db697cd3d1`，绑定parent dry scope、GPU协议SHA与新runner SHA；没有注入旧工程观测。完成后才为此scope形成3条件证据。60DEV格只算准入：36有预算且有工程证据，20预算不足，4保护证据未验；DEV开关false、DEV调用0。不能把之前dry scope的40待验直接覆写为已执行，也不能把36准入叫36新回答。

安全/正常任务指标本轮未测；性能未benchmark。保留full reference和scoring observer，KV减少不能据此推整个进程显存/时延收益。console的torch_dtype弃用提示保留，未在固定运行中改参数或依赖。

原manifest38项/39文件；后验增加独立verification、verifier快照、closure及derived manifest，最终43文件712263bytes。重要SHA：

| 工件 | SHA256 |
| --- | --- |
| manifest.json | 7fda30edb1ba4f86376ab15e8b5cbf55465842feb00624e2162b6c70ffb7c38c |
| summary.json | bcf78a444fcd1f28ceb804f494f53e4e4837fe9fc0cf7a130332031fb9033a9f |
| actual_runtime.json | d0f0719d104528492c819a1032e1f65dd415d5d0470794528be027bb5894e657 |
| registered_runtime_scope.json | aed1d6a6be73d1269748d995174f27c8c129879da32299db0c8ccb08e1538e1d |
| engineering_evidence.json | 7ca977f2f221f752d26dbcf2b1984046e07197a1a5d1ba4c7dba0418f8bc3a27 |
| raw_engineering.jsonl | a4372fb1e909f647dd6c5cbae1e8345090f395e20fd386d597c229b467dfd33d |
| accepted_engineering.jsonl | 8f21338b2191cb6a91ea56d5966e3465ab0abd15fda67de909f88671044ea94d |
| DEV_admission_only.json | 98afa8adc74f96c35aa2fddf045f48a457e14168586f2807114a417749d85afa |
| independent_verification.json | cfc0e6ee3a06e4c2547a02ef01825b5405973ec1fc06627f7569d817fb84218c |
| closure.json | 8088fa3ca01f89da957b7dd25ae0807a8389ebbc60856ad353662dfb6e50d666 |
| derived_manifest.json | 50d555c9a60fe16dd7b03f61ba636c68c77a992a1eec965e79ec919f41790999 |

另同级launch/console/launcher SHA见[readiness](../HF_BACKEND_ENGINEERING_READINESS_20261030.json)。原始token/score/map/日志/模型元数据只服务器，不回本地。

## 解释与下一步

直接结论：新HF后端在这两工程题、Full与两无保护条件上复现旧数值路径；完整system保护仍未验，不是跨模型/所有未来输入保证。任务质量、安全和性能没有由本轮得到新证据。旧QA gate=false、旧封存16/新封存48、既有失败/旧分数不改，BoolQ403及独立跨任务确认仍待解决。

下一步冻结至多36个已准入DEV格的**系统端到端验收**协议，接实际输出、双指标与统一归档；20预算不足及4保护未验保留，0保护/0封存生成。该验收检验新系统接线，仍用既有12DEV、不增加独立科学样本；不要重复本轮工程14回答或再证明泛裁剪有害。第二模型/新预算/新任务另有协议。

新增1GPU run、14工程/0主回答，累计110run2852主；索引`results/20261030-run-index-hf-backend-engineering.json` SHA `a7a3838d93284b895ccb8aeffed06995a7c8ff89d47e0137d2fff05c6bfd1e5a`，旧109run索引保持。STATUS、WORKLOG、HANDOFF及系统readiness同步更新；代码配置文档已同步服务器并核SHA。依赖/权重/环境无变化，GitHub未配置未push，当前无运行任务。


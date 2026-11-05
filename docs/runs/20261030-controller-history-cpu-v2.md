# 共享控制器CPU预检v2：54项通过，真实运行环境待准备

## 实验身份

- 日期/时区：2026-10-30 Asia/Singapore；runner开始00:44:16.293，UTC为2026-10-29T16:44:16.292861+00:00。
- 授权：用户在了解三个关卡后明确“开始吧”；本轮运行已审修正后的同一有界CPU预检，并只读核对真实小试环境。不是自动重试v1或启用模型矩阵。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-history-cpu-v2`。
- 问题：独立CPU公式、观测mask和参考状态恢复是否通过工程关卡。
- 来源：自建float64参考，固定vLLM0.32.0 commit `5df63a7203cdb9328d824a27b682e77c7b9928be`；不执行作者代码。
- 状态：**complete/pass，54/54；无失败、无缺失、无自动重试。** [v1失败](20261030-controller-history-cpu.md)及全部快照保留，原manifest SHA不变。

## 可复现条件

- CPU runner源码SHA256 `2e7e9c2c6d4ac9cc49a717f56c244b6609aa80a8fa7fcc59cd75f63936a43c81`，reference_revision=2；同v1的输入seed/54案例/六类检查/容差/界限，只修正过强断言并增加dense oracle。
- 基础提案SHA256 `b597611cb56f802e6ea39535f705d62896723b1947ce143860f305dc640221d7`、修正提案SHA256 `3a30f300a98b4b91a625ff5d3b62f0d14ee8a97c04e8fb5477a87faf3b0d7cf1`均不修改；归档提案仍禁用，执行另存两个启用快照。
- `execution_snapshot.json` SHA256 `feb82509c8afc9d86e092ddad4423f08b98def9eead1054769de9fe7c0e33ed3`；`correction_execution_snapshot.json` SHA256 `127df7d8a8f8d7cb7fda1af1650eb273ffd6866de0a14d842f419b5af9d4f42e`。只启用CPU参考，模型阶段仍false。
- 上游blob SHA-1 `f7a4a2f2c1e3221407d12c70cc067cc8cc045bd1`，只复用v1已核验的源码文本快照，未执行；作者代码和GPU都不参与CPU比较。
- 实际CPU环境：系统`/usr/bin/python3` Python3.10.12、Linux6.8.12，全部标准库；不是既有venv Python3.11.13。
- K4/maxreq8、period100、slope0.5/bias−0.2、阻尼50、Newton系统L2=0.001、feature±40；seed按族内index+314159。float64 atol1e-9/rtol1e-8；最多64fixture、每例256调用、总60秒、失败即停。
- 模型/tokenizer：CPU run不加载。无服务、训练、端口或后台任务；`CUDA_VISIBLE_DEVICES=''`、`PYTHONDONTWRITEBYTECODE=1`，父进程timeout60秒。

已执行命令：

```text
/usr/bin/python3 '/home/user/jhk/project/Directional Exploration/kv-pruning/scripts/controller_history_preflight.py' --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-history-cpu-v2'
```

launcher PID358925，runner PID358928，exit0；核验自有runner PID已退出。run用时0.311132秒，不是LLM性能测量。

## 结果与证据

| 检查族 | 通过/预定 |
| --- | ---: |
| 独立dense与arrowhead更新 | 16/16 |
| 接受位置/首拒绝观测mask | 15/15 |
| 未观测intercept与共享slope | 3/3 |
| 空观测轮次 | 4/4 |
| 99/100步边界与清统计 | 4/4 |
| 完整参考恢复、槽位及batch换序 | 12/12 |
| 合计 | 54/54 |

- 合成step调用4503，单fixture最多255，均在冻结界限内。
- dense/arrowhead最大绝对差`3.885780586188048e-16`；unobserved独立oracle最大差`6.661338147750939e-16`。
- 12个完整参考检查点恢复均exact重放；槽位/batch换序最大差`4.263256414560601e-14`，在原容差内。12/12均识别了仅恢复θ、遗留统计/phase的负对照。
- 这些仅适用于自建同步CPU参考。成对合成feature/label输入没有验证真实异步producer/consumer、CUDA Graph/GPU缓冲、完整服务状态或真实LLM预算/耗时；不能将“参考完整恢复通过”缩写成“vLLM完整恢复通过”。
- 0新主要答案、0工程生成答案，54fixture不计LLM输出；没有发现攻击或创新结果。

原始约1.91MB（只读环境附属记录加入前）仅服务器：`fixtures.jsonl` SHA256 `5ae1c3fa5b37b1bd1aec18ad66b148492e591bad40d390f4144f8da3fb29990d`、`summary.json` SHA256 `bf7932cbf0f2234bd0a368e344db9f6b4020ab89d3fb5c330db98df63dd4d718`、所有提案/源码/执行快照、console/launcher/manifest/verification。9项原manifest文件SHA全部通过；manifest SHA256 `0a53b345466d5f37e25a95e79b688f7de9e582ee1180e50476cb9f3b0279e566`。

累计索引`results/20261030-run-index-controller-history-cpu-v2.json` SHA256 `c669ef97ba7e9af16da1244fbc618100453dbf2bafc3529465d1fdf70988783d`保留旧79项并追加本run：**80run、2702主要输出**。后续只读环境/依赖调查为本run附属材料，不算新模型实验或重复CPU测试。

## 真实运行环境：只读核查结果

机器/环境快照保存在`environment_readonly.json`、`model_metadata_readonly.json`、`runtime_metadata_sources.json`、`dependency_resolution_readonly.json`。本轮没有安装包、创建新环境、下载权重或加载模型。

1. 现有venv Python3.11.13、Torch2.5.1+cu121、Transformers4.57.1、Triton3.1.0，没有vLLM/flash-attn。固定源码requirements与[PyPI0.32.0元数据](https://pypi.org/pypi/vllm/0.32.0/json)一致要求Torch2.13.0、Transformers>=5.16.1/<5.20.0、Python>=3.11/<3.15等，不能直接复用旧venv。已记录候选Linux wheel SHA256 `5e2ecdc5b0baf72921c288486417ca82778456a448e4fe60b62ee43c0dfc8611`，未下载。torchaudio2.11.0的PyPI摘要requires_dist=null，不等于依赖无冲突，完整解析仍待做。
2. 当前两张RTX4090、驱动580.178.04；快照GPU0 1225MiB/10%、GPU1 633MiB/2%，有其他用户计算进程。仅查询、未终止或改动它们。驱动满足NVIDIA列出的CUDA13大版本最低范围，但[官方兼容文档](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)仍有PTX/新功能限制；未验证选定wheel/算子/SM89实际可用。
3. 项目已有target候选Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`，config SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`：36层，32query/8KV heads、sliding_window=null、use_sliding_window=false；同commit的Qwen3实现为普通decoder/self-attention候选。实际加载后仍须逐层检查，未作当前runtime验证。
4. draft候选Qwen3-0.6B已由官方API固定revision `c1899de289a04d12100db370d81485cdf75e47ca`；[固定config](https://huggingface.co/Qwen/Qwen3-0.6B/raw/c1899de289a04d12100db370d81485cdf75e47ca/config.json)为28层、16query/8KV heads、无滑窗，vocab151936。服务器直读该config遇Network unreachable，后用官方网页核对，不把失败写成已下载。项目models下未找到该draft，未扫描其他用户目录；没有下载权重。同vocab size不证明tokenizer映射一致，尚未逐项核验。
5. [StandaloneARSpeculator源码](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/standalone_ar/speculator.py#L29)继承所审DraftModelSpeculator，静态上存在接入估计器的路径。[LLM.collective_rpc:574](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/llm.py#L574)允许可信调用在worker内执行，可用于小型控制状态操作；不是现成的checkpoint API，本轮未实现/测试GPU读写恢复。

## 解释与下一步

CPU参考关卡通过，v1错误已在同一输入/界限下纠正；这不自动开启模型实验。下一条是按[运行准备清单](../CONTROLLER_RUNTIME_PREPARATION_20261030.json)完成依赖解析/二进制与driver校验，准备独立`.venv-controller-history`，保留旧venv；然后核对固定draft文件/tokenizer，编写可信worker状态操作及独立有上限GPU工程协议。实际安装/下载/模型加载本轮均未执行。

未来还须固定实际构建版本与上游warmup修复策略，各分支一致；核验真实对象位置、排空队列/同步、所有控制统计/phase/双缓冲恢复及CPU参考与GPU更新口径。工程门槛通过后，才做不同前序正常历史→同一探针的配对筛查。不扩旧KV裁剪矩阵，不恢复旧guard gate，不将元数据支持误报成性能或安全结果。

STATUS/WORKLOG/HANDOFF/PLAN/README与审查文档已更新；代码/配置/文档同步服务器，原始结果未下载，GitHub未配置。

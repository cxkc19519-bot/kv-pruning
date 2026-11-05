# 独立运行环境与原生估计器检查

## 实验身份

- 日期/时区：2026-10-30，Asia/Singapore；原始时间保留UTC。执行设备为授权服务器，执行人为Codex。
- 授权：本专用实验会话已有实验许可，用户本轮“开始下一步”继续环境准备和正确性验证。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-runtime-bootstrap-v1`、`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-native-kernel-v1`。
- 问题：固定vLLM发行版能否在独立环境完成解析/安装；其原生GPU估计器能否与CPU参考吻合，并完整恢复估计器自身状态。
- 来源：固定作者实现的工程检查，非新方法/攻击实验。两项均完成；0主要模型答案、0额外工程答案。累计82run、2702主要输出。

## 可复现条件

- 本地/服务器本方向均无Git仓库；不从nano-vllm复制。作者固定v0.32.0/commit `5df63a7203cdb9328d824a27b682e77c7b9928be`。
- 新增独立`.venv-controller-history`：Python3.11.13、Torch2.13.0+cu130、CUDA运行库13.0、Transformers5.19.0、vLLM0.32.0、Triton3.7.1。旧`.venv`复查仍Torch2.5.1+cu121/Transformers4.57.1；未修改驱动/系统包。
- GPU原生检查：物理GPU1，RTX4090/SM89，驱动580.178.04。检查前GPU1为18MiB/0%，他人进程仅在GPU0；未操作他人任务。不是独占性能测试。
- 依赖先`pip install --dry-run --ignore-installed --report ... --only-binary=:all: vllm==0.32.0`，再从报告生成197包SHA256锁，使用`--require-hashes`安装；仅PyPI二进制wheel，无源码构建。`pip check`及三库导入通过。
- [精确依赖锁](../../configs/controller-runtime-lock-20261030.txt) SHA256 `02cba8a2652cff30e357b285d4cd9458063978985cd3a6c40d78e3e30b91d8d9`；实际命令完整保存在bootstrap的summary/日志。环境8.4GiB、服务器下载缓存3.8GiB，均保留。
- [安装脚本](../../scripts/controller_runtime_bootstrap.py) SHA256 `55c2d978d2fe18012fb9c1d8be9ba96bf89a14572e4525212504c0468cfb01e7`。一次性运行命令如下（已执行，不能对同目录重复执行）：

```bash
.venv/bin/python scripts/controller_runtime_bootstrap.py --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-runtime-bootstrap-v1' --install
```

- [原生检查脚本](../../scripts/controller_native_kernel_check.py) SHA256 `89d0df7e52c9578fb92fb988d4bdf0b5f831bba84faaf57bffe197ac138e5528`；CPU参考保持v2/SHA `2e7e9c2c6d4ac9cc49a717f56c244b6609aa80a8fa7fcc59cd75f63936a43c81`。实际使用CUDA_VISIBLE_DEVICES=1、HF离线和本次目录内Triton缓存。

```bash
CUDA_VISIBLE_DEVICES=1 VLLM_NO_USAGE_STATS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TRITON_CACHE_DIR='/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-native-kernel-v1/triton-cache' .venv-controller-history/bin/python scripts/controller_native_kernel_check.py --run-dir '/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-controller-native-kernel-v1'
```

- 无模型/tokenizer/数据集加载，无生成/解码参数。固定合成8槽、4草稿位置、128词表，确定性输入公式在源码；最高256次step/180秒，无失败自动重跑。FP32对CPU float64参考atol/rtol均1e-4；特征/预测检查均1e-5。
- 安装阶段屏蔽CUDA，不启动服务；模型权重/draft仍未下载。本次无端口、tmux、定时任务。

## 结果与证据

- bootstrap 655.826秒，UTC10-29 17:14:28–17:25:23（SG10-30 01:14–01:25）；原生检查UTC10-30 03:33:05–03:33:11（SG11:33），6.758秒。二者间没有自有持续运行任务；不将时间间隔计作实验用时。
- 安装包6项文件Git blob均与已审固定源码一致：acceptance_estimator、speculator、adaptive_verification、standalone_ar/speculator、qwen3、LLM入口。`installed_source_audit.json` SHA `1658c6e20c42e3f1e4ea4b89da37c6382674a21c17aa0f40272393f1301ed4af`。
- 原生实际调用127次step，包含一次编译预热后恢复共同初始状态、105步轨迹、第95步快照后10步重放、10步θ-only负对照和空轮次重估。检查阶段1/95/99/100/105；原生每100次调用重估。
- 特征最大绝对误差7.153e-7，预测1.192e-7；CPU参考全部状态检查最大绝对差9.156e-5（累积统计，按预定绝对+相对容差通过）。不能将该最大差称为单独的系数误差。
- 原生估计器完整快照覆盖slope/intercepts、info/grad/counts、features/predictions与phase/refits；跨重估边界重放逐值exact，张量地址保持。仅恢复θ负对照检出；空批次重估通过。本轨迹斜率防护保留0.5、位置截距发生更新。
- Torch峰值allocated 24,064bytes/reserved 2,097,152bytes，仅此进程张量分配器统计，**不是GPU上下文/全部显存成本**；没有测量服务性能。
- bootstrap PID374652、GPU检查PID683603均退出且/proc核验；收尾GPU0 605MiB/2%、GPU1 18MiB/0%，compute PID656043为其他用户，未操作。
- 无实验失败或自动重试；工具层一次GitHub参数校验失败、一次Windows glob搜索错误、会话句柄不可用与一次本地SSH辅助变量丢失，均未导致重跑/重复远端动作；后续直接核对服务器summary和PID收尾。
- 两个原始manifest的11项/3项文件SHA全部独立核对；后加源码审计与verification_closure独立归档，不改原manifest。CPU v1/v2 manifest SHA保持历史值。

| 工件 | SHA256 |
| --- | --- |
| bootstrap manifest | `43ddd3ea7049f9c259049be4690fd9021b7e47b8ffe0f9ec5a47f3cebbbce015` |
| bootstrap summary | `3aa08a8871d20bfc1336b43a9102c4e0eb7f19b6971a93b3b64d3ce41fd914c0` |
| bootstrap closure | `086215ec9bcf7798ac852e3356bc6f2ef9d705a830a47072c83ed2344ad18b4d` |
| native manifest | `b75a40afa272e370539ad7f70c2757552cb4681341560669705da133bf27c0e3` |
| native summary | `fc1eae39b92df47c4677042cfd98854c20ac1fd3f954e43ea4a13177d87ffd02` |
| native closure | `a52ee6b2f54ebe45acb663b44d81446f0be5d8baac3168c3133eb3212fa2eea3` |
| 新累计索引results/20261030-run-index-controller-runtime.json | `c53537f38495dbf739035f9fb1c11c9e5ac79737dfd813faa416cc08aa58357e` |

## 解释与下一步

直接观察支持：固定环境可安装/导入，SM89上本次合成原生估计器运算及估计器自身原址恢复通过。**不支持真实worker完整恢复、异步confidence双缓冲恢复、模型兼容、正常用户损害、攻击或新颖性结论。** CUDA13运行库在此kernel可用不保证完整引擎所有算子/PTX可用。

下一条：在该环境准备固定Qwen3-0.6B revision `c1899de289a04d12100db370d81485cdf75e47ca`，核验官方文件摘要与target tokenizer映射；再冻结单卡、短输入、极小输出数量/时限的真实worker工程协议。通过可信collective_rpc，待队列清空并同步后覆盖估计器及adaptive_verification双缓冲、stale_idx、pending_resets和事件依赖，验证原址恢复/重放，再判断是否进配对历史小试。不能将本次估计器测试替代该门槛。

固定发行版尚未应用10-28 JIT warmup补丁；本次仅预编译测试形状并恢复共同状态。真实模型阶段须统一各分支/形状预热，不能把首次编译计为历史干扰。旧候选A/guard失败决定保持，不自动扩矩阵。STATUS、WORKLOG、HANDOFF与根ENVIRONMENT本轮更新并同步服务器；项目GitHub仍无可核验远端。

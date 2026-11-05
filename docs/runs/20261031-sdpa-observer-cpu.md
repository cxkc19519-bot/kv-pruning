# SDPA透明记录器与归档故障CPU验收

## 实验身份

- 日期/时区：2026-10-31，Asia/Singapore；Codex，已有服务器Python3.11.13。
- 授权：实验会话用户“开始下一步”，实施透明记录器CPU检查，随后禁用现场观测草案。
- 绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-sdpa-observer-cpu-v1`。
- 来源：软件正确性合成用例，非真实SDPA/CUDA/模型实验。
- 状态：**24用例与独立validator均通过，归档cap先检查，整体exit0。**

## 可复现条件

- 无Git/远端。六source SHA与旧离线审阅配置SHA先冻结，[登记](../../configs/sdpa-observer-cpu-v1.json) SHA `3f0149f91926bffa63e91a819c7a6a2071f8f32398fc5698d9dfdc83341fef53`；CAS同步7文件并静态compile后只运行一次，旧失败source/run不改。
- 仅标准库，未导入Torch/Transformers/NumPy/tokenizer，无模型/权重/GPU/网络/安装。fake dtype/device和kernel名字是fixture字符串。
- [协议](../SDPA_OBSERVER_CPU_PROTOCOL_20261031.md)固定O01–O18/A01–A06；显式对象identity/参数顺序/异常对象检查，独立validator只重算序列化合同，不声称可跨进程重建对象指针。
- 实际命令：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_sdpa_observer_cpu.py --execute --registration-sha256 3f0149f91926bffa63e91a819c7a6a2071f8f32398fc5698d9dfdc83341fef53
```

- launcher1412958/worker1412961/verifier1412963均exit0并核退出，无后台服务/端口。
- worker/validator各60秒，outer150秒，64文件/4MiB上限含递归fixture和最终summary/manifest。

## 结果与证据

- `software_cases.json`/`software_results.json`保存24用例。18observer用例验证参数/返回identity、原RuntimeError/KeyboardInterrupt/TypeError、marker/sink/metadata错误不替代原调用、正常/异常恢复、nested拒绝、外来owner冲突、日志上限和同instance重入。
- `profiler_inventory`只在合成父链验证flash/math operator/kernel归属，孤立事件保留unassigned，父链循环拒绝；真实Torch profiler/CUDA尚未验。
- 六archive用例验证文件数边界/超限、字节超限、既有worker失败、嵌套文件计数和拒绝覆盖。独立回读全部19个fixture归档文件及manifest/byte/count；故意失败fixture不是本轮CPU run失败。
- 新`checked_archive.py`先计算最终summary/manifest自身开销再决定status；本run用其封口，`archive_caps_checked_before_success=true`，不再先写complete后抛cap错误。先前44>40失败不追改、不重跑。
- worker内0.061212464秒，verifier0.017568388秒，launcher0.284791744秒。两guard全0，0真实SDPA/模型/GPU调用。
- 归档41文件100853bytes，manifest `478fb7005060bac8d738ab1c0f11c1aeccd9c00dd1cb0a77233f924be1a5ad89`，worker_manifest与最终manifest全递归重读SHA相同。
- 新增1CPU run/0回答，累计126run3038主；新索引`results/20261031-run-index-sdpa-observer.json` SHA `3da7a45b79502f1c73d944f7db057689f0ccaa81b281880ac33ac395e7547e68`，旧43ddc7a0…索引保持。原始只服务器。

## 解释与下一步

通过范围仅为24 stub/fault用例，不证明GPU数值或性能透明；observer不读Tensor值，实际mask值和CUDA kernel尚未观测。原数值工程gate仍failed，12DEV/H3/Full12支持未测。

[现场观测禁用草案](../SDPA_OBSERVATION_DRAFT_20261031.md)/[配置](../../configs/sdpa-observation-draft-v1.json)已冻结：原两工程组、7路径/组，含Full及recency plain/observed逐元素相等负对照；最多108 forward/1082输入token/14归档分布/2856 observed SDPA事件，0开发组。GPU worker/validator和实际集成未实现，execution=false；不能由草案自动启动，也不切后端/精度/阈值救回旧工程。

下一条具体操作是实现该观察入口和独立实际profiler证据核验，另冻新bounded登记后才运行；CPU observer已完成不重复跑。STATUS/WORKLOG/HANDOFF/readiness更新同步，GitHub未配置，当前无运行任务。


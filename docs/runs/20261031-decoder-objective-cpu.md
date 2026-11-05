# H3解码目标CPU正确性验收

## 实验身份

- 日期/时区：2026-10-31，Asia/Singapore；Codex，服务器已有Python3.11.13环境。
- 授权：本会话实验授权及用户“SSH已恢复”，续跑上一轮已冻结的CPU步骤。
- 服务器绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261031-decoder-objective-cpu-v1`。
- 来源：自建合成软件正确性验收；不是新模型实验/论文复现或真实KV因果证据。
- 状态：**完成，18/18用例及独立核验通过。**

## 可复现条件

- 无Git仓库/提交。四脚本与协议、旧禁用草案SHA依[CPU登记](../../configs/decoder-objective-cpu-execution-v1.json)冻结，登记自身SHA `847651a5bae3ef4228ededc7782b59f6b16f8712d4bfe08c7a74e7c0e4f6c1fb`，本轮未改源码/协议/阈值。
- 原先5次SSH认证前断开，0run；用户通知恢复后现场核对远端AGENTS、原120run3038主索引f3e6a039…及预定run不存在。CAS同步17文件，字节SHA一致、四Python源静态compile通过，再运行一次。
- 不涉及模型/tokenizer/revision/数据集。GPU/驱动/CUDA/PyTorch未查询；无安装或环境变化。
- 18组合成用例与23坏输入，固定fixture seeds3101–3106，仅软件输入；详见[冻结协议](../DECODER_OBJECTIVE_CPU_PROTOCOL_20261031.md)。
- 实际命令：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -B scripts/run_decoder_objective_cpu.py --execute --registration-sha256 847651a5bae3ef4228ededc7782b59f6b16f8712d4bfe08c7a74e7c0e4f6c1fb
```

- launcher PID1389085，worker1389088，verifier1389089，均exit0，随后核验三个PID均退出；无服务/端口/后台会话。

## 结果与证据

- `software_fixtures.json`/`software_results.json`保留全部输入与返回；C01–C09/G01–G04/M01–M05共18组完成。23次非法输入按固定合同拒绝。
- `independent_verification.json`：不导入被测模块/runner，以80位Decimal复算7个候选分布向量及其全部目标、40条有限语法图边、路径/EOS、8候选索引/固定seed/锚点/预算/重复与infeasible对照。
- 概率反例、全词表mask、单token、全局概率下溢但局部可分、无限KL、拆分UTF-8和跨JSON边界等检查通过。合成槽布局57344 bytes只是index plan预测，未测真实GPU物理缓存。
- worker内0.133624240秒，verifier内0.702379842秒，launcher总0.985419135秒；未到30/90秒上限。两个guard所有导入/文件/socket/子进程拒绝计数0；0模型回答、分词、权重字节、GPU查询或运行内网络请求。
- 归档21文件239223 bytes，`manifest.json` SHA `f9a304f6e36e7cf5dd2dd41e634da71b44f84c3b5369f323cdcbec89fa80ad8a`，原manifest及worker_manifest全部逐项重读一致。结果只服务器，本地只代码配置文档。
- 新增1CPU run/0主回答，累计121run3038主；新索引`results/20261031-run-index-decoder-objective-cpu.json` SHA `3c7cdede19646be575a20adfc3d1e73f14b3e043e9066b9c26ecec4b4e02a2a1`。原f3e6a039…索引不覆盖，旧GPU/分类与所有失败保留。
- 安全/正常任务/性能/显存指标未测；软件验收用例不充研究样本或真实失配发生率。

## 解释与下一步

- 直接观察：有限byte词表、局部KL与等预算索引计划通过登记的18组软件用例和独立复核；上一轮服务器连接阻塞已解除。
- 不支持：真实tokenizer转换、真实KV gather/实际bytes、真实KV排序失配、新方法新颖性、任务收益或可发表/毕业结论。局部语法mask仍不等完整字符串条件分布。
- 下一具体操作：冻结真实Qwen tokenizer-byte映射/有限schema及新12开发组输入的CPU来源与原生编码协议。先证明所有合法token路径可达、native边界/预算正确；再另冻同前缀重算query+wrapper、物理gather工程关卡和GPU资源上限。GPU runner仍未实现/未启用，不直接执行旧108向量草案。
- STATUS/WORKLOG/HANDOFF及readiness更新并同步服务器；原5次握手失败与上一轮未执行记录作为历史保留，不新增失败run。

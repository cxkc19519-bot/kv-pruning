# 流式与动作guard来源、CPU关卡及下载记录

## 身份与可复现条件

2026-10-28，Asia/Singapore；当前用户授权的持续研究窗口。服务器绝对根`/home/user/jhk/project/Directional Exploration/kv-pruning/results/`，本地仅代码/配置/文档。Python3.11.13；CPU/meta检查沿Torch2.5.1+cu121/Transformers4.57.1，CUDA未初始化、没有模型forward。无新依赖。所有源码和原始数据只服务器，source/配置副本及hash/console/launch/closure完整保留。

固定Qwen3Guard官方GitHub6a52eca...、HF Stream0.6B74e1479...及Test8a8391a...：14文件哈希通过。模型配置28Full层但未实例化/下载权重。数据1059 thinking（含490 Safe）、569 thinking_loc为其精确子集、813 response_loc全Unsafe。定位集起点最多322/120，512之后0；不适合长历史首次危险检测。

`stream-guard-feasibility-v1`自有断言把所有end当严格小于长度失败；182条response_loc end等于长度，v2保留该公开端点并报告可能exclusive约定，CPU通过。未以端点问题否定原数据。该设计no-go，无模型执行。

固定StepGuard代码93b580b...、模型c7e4a2c...、StepSafe代码05ea723...：28选定来源文件核验；ToolSafe46358fa...四个LFS文件1220记录核验。`action_guard_native.py`仅选取已读的纯序列化/正则评分定义执行，记录源码SHA，未执行作者代理/工具/下载/训练模块。其余来源AST只读。原生序列化不得省略历史角色或反馈。

## 运行与结果

服务器方向根实际命令的参数详见各run launch.json；可复现入口：

```bash
.venv/bin/python scripts/audit_stream_guard_sources.py --config configs/stream-guard-source-audit-v1.json --out results/20261028-stream-guard-source-audit-v1
.venv/bin/python scripts/analyze_stream_guard_feasibility.py --source-run results/20261028-stream-guard-source-audit-v1 --out results/20261028-stream-guard-feasibility-v2
.venv/bin/python scripts/audit_stream_guard_sources.py --config configs/action-guard-source-audit-v1.json --out results/20261028-action-guard-source-audit-v1
.venv/bin/python scripts/fetch_toolsafe_data.py --config configs/action-guard-data-preflight-v1.json --out results/20261028-action-guard-data-fetch-v1
```

以上脚本已有后续兼容选项时，以每run内冻结源码/配置为准，不用当前SHA冒充历史版本。

CPU预检`20261028-action-guard-cpu-preflight-v1`完整命令在launch：调用prepare_action_guard_cases，沿已有Qwen3 tokenizer SHAaeb13307...，模型tokenizer_config原字节。冻结32交互、每类16、四域各8；自然历史长度/步数/总长门槛见config，不凑长度。1220输入冲突0/前端错误0；meta36Full层和checkpoint键匹配，147456BF16 KV bytes/token理论值。未审真实权重行为。8评分正负fixture通过不是完整判分器质量保证。

`20261028-action-guard-training-fetch-v1`下载公开SFT/RL文本47,361,269bytes，原始LFS/Git哈希核验；`20261028-action-guard-overlap-v1`全7000输入扫描，32例完整或完整三字段匹配0。语义和非公开训练重叠未知，不称确认测试。

`20261028-stepguard-model-download-v1`固定单模型10文件8,056,473,628bytes完成，下载脚本fetch_registered_artifacts SHAe9a48f0...、spec6f17795c...；镜像仅传输，身份由官方HF版本/blob/LFS hash交叉核验。每次curl总时限900秒、每文件最多2次、2并发，完整attempts保存。使用已核验本方向tokenizer和元数据副本，未借用nano-vllm。

## 停止和账本

另一个[Full-only关卡记录](20261028-action-guard-full-gate.md)因平台usageLimited停在加载前，0输出。上述源/CPU/下载9个run含1失败，全部0模型输出；加Full停止run为10个。与之前6个研究run合计窗口16run，累计75run2702，完整索引及资源closure服务器。环境新增仅公开文本和一个固定模型，无安装/服务/端口；收尾两卡15MiB/0%、compute-app空。

解释、候选否定与下一步见[窗口结论](../RESEARCH_WINDOW_20261028.md)。所有失败保留，未执行的能力或压缩检查不得写成通过。STATUS、WORKLOG、HANDOFF及上级ENV同步更新。

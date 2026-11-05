# 真实旧版语法后端CPU接口与有限语义检查

## 实验身份

- 日期／时区：2026-11-01，Asia/Singapore；用户本实验会话“开始下一步”。
- 路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-legacy-backend-cpu-v1`。
- 状态：**前置检查失败并停止；未执行任何schema／matcher／mask／45标签语义检查。未自动重试或调整时限／词表。**
- 来源：既有XGrammar0.2.8／llguidance1.7.6真实CPU库，公共8schema45标签，257合成byte/EOS词表；不加载模型或模型分词器，不进行真实服务负载／干扰测试。

## 可复现条件

- [原冻结协议](../STRUCTURED_RESOURCE_CPU_PROTOCOL_20261031.md)不改，[新登记](../../configs/legacy-backend-cpu-execution-v1.json)绑定runner、独立validator、归档器、公共选择和runtime_pin。runtime pin保存101个现有源／metadata／原生文件SHA，其中5个.so，共15945175bytes；没有安装或升级。
- 使用既有`.venv-controller-history/bin/python -B -S`，仅通过PYTHONPATH加入固定site-packages，禁用site／.pth启动。CUDA_VISIBLE_DEVICES为空；HF离线、写入和临时目录均run内；TVM_FFI_DISABLE_TORCH_C_DLPACK=1关闭已审的可选JIT。XGrammar公开导入会真实加载Torch，不伪装无Torch依赖。
- 两后端逻辑schema spec转换／编译各8，最多90个matcher构造、2430mask；llguidance原生准备也在45个实例matcher构造中发生，不将16个schema spec当成只有16次native准备。逐byte读取原始mask并明确EOS，strict_mode=false，不改原schema或标签。
- GIL先用Python忙等25ms（switchinterval100ms）和sleep25ms控制验证心跳；随后观测真实Python wrapper call span与外部进程样本。wrapper内心跳不是精确native-entry证据，无心跳不证明持有GIL。
- 总180秒／单调用5秒外部watchdog／单后端80秒；最多64文件／8MiB。网络socket、子进程编译、模型权重读和run外写拒绝，库能力探测若触发socket以OSError拒绝并单列；不以网络探测被拒绝冒称成功外联。
- 最终实际登记SHA `e10a5b2fee64d8558c9043fe60ef930dde9904dfe1de4b11eb6bad959b520b2d`。源代码补入GIL控制前置拒绝与PID/starttime清理核验后，先核四新文件／AST、6源输入pin、101运行库pin、run不存在，再执行唯一一次；之前本地未执行的登记未用于启动。
- 实际命令（已执行，不原路径重跑）：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -I -S -B scripts/legacy_backend_cpu.py --execute --registration-sha256 e10a5b2fee64d8558c9043fe60ef930dde9904dfe1de4b11eb6bad959b520b2d
```

- launcher2212823内5.512406秒／exit1；XGrammar worker2212826被watchdog SIGKILL、exit-9；llguidance worker2212901内0.114377秒、exit1；三已记录PID收尾均不存在。独立validator子进程已等待退出且exit0，它验证原始失败状态一致，不表示后端通过；当前launcher未归档validator PID，不声称额外PID现场核验。

## 结果与证据

| 阶段 | XGrammar0.2.8 | llguidance1.7.6 |
| --- | --- | --- |
| GIL控制 | Python忙等0心跳，sleep22心跳，通过 | Python忙等0心跳，sleep22心跳，通过 |
| 真实导入 | 组合import阶段超过5秒，由外部watchdog按登记终止，未观测完成 | 0.062260秒完成公开导入 |
| 合成词表 | 尚未开始 | LLTokenizer构造完成，但decode_bytes(0..255)不等原始bytes，触发decode_byte_roundtrip拒绝 |
| schema／matcher／mask | 全0 | 全0 |
| 45标签检查 | 全部未执行／unavailable | 全部未执行／unavailable |

适配器的byte词表假设没有通过，不能据此说llguidance语法能力失败；未保存实际decode差值，具体错位／特殊字节原因未知，不能事后编造修复。XGrammar的import事件包含Torch和XGrammar公开入口，当前没有二者分段结束证据，不能声称已定位到Torch、FFI或哪个子模块。未在同一run加时／改源码／换词表／重新加载。

原始事件XGrammar420条、llguidance64条。导入／wrapper span心跳不等于精确native入口证据；真正schema／mask GIL行为未测。XGrammar缺失最终result且保留未闭合import span，不填成功；llguidance guard四项均0，XGrammar被强杀前未落盘guard最终汇总，不能推断其四项也为0。模型和模型分词器没有加载，CUDA_VISIBLE_DEVICES为空；XGrammar未完成导入后的CUDA初始化后验检查，不冒称已验证该后验状态。

独立validator只对已有工件重判：90个计划backend×实例格都error_or_unavailable，**不是90次实际拒绝或语义错误**。raw mask为0，finite_semantic_gate=false；原12项标准库observer通过保持，不据本次失败推翻或承认真实资源问题。

最终归档21文件297931bytes，manifest `6f64c194478b98eb39126ba00f79649b0c1ebb1e18b17011b6315c60d42c41b1`、independent verification `2252c734b6f61c068963b7d4e618d1542ed99774d2514f04d3ce49834540850d`全部回读；封口status=failed、无archive cap错误。原始仅服务器。

101运行库pin在事后全部核对不变；文献runtime pin归档3文件16536bytes，manifest `9a7112ebb43b8f9691b5671176377dae72151dd9d2c92e1e51bccd7d08e71382`。无安装／升级／新模型／服务。新增1失败CPUrun／0模型回答，累计134runs3038主；新索引 `results/20261101-run-index-legacy-backend.json` SHA `06fccdfb37a2cbc5ecd0438eeda9de5286ea73bf2fbc0fba0763d2ec66b45dd8`，旧索引不变。

## 解释与下一步

本轮是旧版接口前置失败，不证明N1科学效应、新颖性或最强取消对照不足。下一步先只读审查已固定源码的byte／special-token约定与组合导入路径，再设计保留原语义和原时限的分段诊断；必须另冻结新登记，不能直接重试本run，不能因超时提高时限、删字节、换schema或升级依赖救回。新的作者库调用／byte差值探针也是实验，不能把它伪装成只读查看。STATUS、WORKLOG、HANDOFF、readiness及索引已据实更新，代码文档同步服务器，无自有后台任务，GitHub未配置未push。

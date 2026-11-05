# DEV验收v2：配置序列化边界修正

日期2026-10-30，v2输出前冻结。本页修订[原v1协议](HF_DEV_ACCEPTANCE_PROTOCOL_20261030.md)的停止后处理：v1已按停止线退出并保留全部工件；依据同一用户请求继续完成系统修复，另行注册一次v2，不能直接覆盖/重启v1。不是模型/提示/样本搜索。

v1 worker948163/launcher948160于UTC11:44:02—11:44:23退出，内部20.910878秒、exit1。8项恢复软件检查通过，14原工程观测恢复，60格准入正确；首次后端调用加载模型后，整份model_config直接Python比较触发actual_model_config_changed。**0生成输出/0token**，DEV dispatch尝试1次不等生成回答1次，未产生任务结果。

离线CPU AutoConfig核查唯一差异为id2label：实际Python字典键类型int，归档JSON键类型str。对完整实际config做一次JSON往返后，所有字段与已验工程config完全相等，没有删除、忽略或白名单跳过字段；实际runtime比较此前已通过。诊断5d2a4e38…和键类型证据6116dd15…保留于失败目录，未重新加载模型权重。v1原manifest e3bfa15e…、后验b4a48037…原样保留。

新[runner v2](../scripts/run_hf_DEV_acceptance_v2.py)仅把配置比较改成完整JSON规范化后比较，并保存config_JSON_comparison；v1源码、原数值HF后端/编排/选择器、检查点恢复模块保持SHA不变。新[配置v2](../configs/hf-DEV-acceptance-v2.json)仅更新run目录/入口身份、固定失败诊断与新源码hash。原工程生成器scope不变，v2控制协议另有digest。不是将真实配置差异视为通过。

原36回答/4608token/0工程/0保护/0封存以及同12DEV、预算、seed、解码、评分、参考输出、600秒内部/660秒外部watchdog/20秒TERM宽限/128文件128MiB等全部保持。两次run合计仍最多36生成回答，因为v1生成0。任何v2实质runtime/输出/trace/评分不一致再次失败即停，不自动再注册v3。原始结果先落盘，低任务质量、截断/N/A/20预算阻止/4证据阻止都保留。无需重复上轮14工程生成。

v2命令由归档launcher设置固定UUID、离线环境与外层watchdog后执行：

```bash
.venv/bin/python -u scripts/run_hf_DEV_acceptance_v2.py --proposal configs/hf-DEV-acceptance-v2.json --execute-DEV
```

本修正发生在取得任何新任务输出前，目的是修复可复现性比较的类型边界，不改变研究判据；v1失败仍计入累计run，不能只统计成功v2。此次仅系统接线验收，独立科学确认仍false，旧gate/封存不改。

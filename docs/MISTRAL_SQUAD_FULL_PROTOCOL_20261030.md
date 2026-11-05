# Mistral当前QA任务：Full-only执行协议

2026-10-30。用户在已授权实验会话要求“继续”，按[两模型CPU预检](runs/20261030-independent-frontends-preflight.md)衔接。执行前冻结[配置](../configs/mistral-squad-full-v1.json)、[新入口](../scripts/run_mistral_squad_full.py)、[独立复核](../scripts/verify_mistral_squad_full.py)与本页SHA，launcher原样保存。服务器绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-mistral-squad-full-v1`，存在即拒绝，原始只服务器。不是默认讨论模式或文档待办授权，具体授权来自本会话用户连续实验指令。

本轮只回答Mistral能否在当前固定span-QA/JSON适配上完成Full生成与任务支持；不测压缩、保护、新预算、封存或安全。固定revision c170c708c41dac9275d15a8fff4eca08d52bab71、官方13文件清单、现有模型路径/依赖。3权重分片逐完整SHA核验，10metadata按官方git-blob/LFS摘要及CPU记录SHA核验后才加载；不下载、升级、执行remote code或访问nano-vllm。

沿原两工程case 56f991b19b226e1400dd15b8、57280cfc3acd2414000df323，各native整段/native缓存分段/custom缓存分段=最多6工程回答；两题三路径逐token与termination均相同才执行固定12DEV Full-only。额外两工程题不入模，0封存。原CPU中Mistral完整native ids/prefix/prompt/gold绑定必须重现，保持INST内system+两换行+user，不注入Qwen边界。

实际32Full/GQA8/head128/BF16/SDPA、无滑窗逐层配置核对；每次prefix实际K/V形状(1,8,n,128)及131072bytes/slot求和核验，clone独立地址/逐tensor相等，reference内容hash在分支后不变。分段native与custom显式使用相同attention mask/cache physical positions和原Full逻辑位置，custom trace逐步保存。整段native未保留cache时prefix/final测量null，不用估算冒充实测。当前新入口仅Full，未把旧Qwen硬编码后端宣称迁移完成。

沿现有Torch2.5.1+cu121、Transformers4.57.1、tokenizers0.22.1/safetensors0.6.2/sentencepiece0.2.1/protobuf6.33.0，BF16 fresh GenerationConfig，greedy/do_sample=false/num_beams1/rep1/max_new_tokens128/EOS2/pad2/bos1/use_cache=true；TF32及BF16 reduced precision reduction关闭，torchseed20261030。无prompt/题目/gold/seed/边界变更或后验筛题。GPU UUID4ce22e12-b5c0-e423-06c5-e858bb71daaa，加载前核memory≤128MiB/util0；初查15MiB/0%不等最终空闲保证，不操作他人进程。

上限12主+6工程、2304新token，内部600秒/外层660秒watchdog、TERM后20秒仅自有组，64文件64MiB，无服务/端口/后台队列。原始模型结果先append再核cache/判分；所有失败/部分输出保留。第一source/runtime/cache/三路径不一致或异常即停，不自动修正重试。每条完整text去末尾EOS后用已验证scorer产生EM/F1、格式和N/A；截断/N/A保留严格分母，joint按全部12计划题报告。

Full支持门槛沿原独立实证设计：12DEV中任务正确≥6、格式正确≥9、错误0、截断≤1；不满足时run可完成但Full_support=false，停止后续该适配压缩，不换提示/模型/样本救回。三路径一致不替代任务质量。原Qwen成绩不进入Mistral生成/选择过程，两模型同12DEV仍为开发比较，不增加独立上下文证据。

实际执行命令由固定离线env/UUID以及KV_MISTRAL_FULL_WATCHDOG=registered_660_seconds的外层launcher调用：

```bash
.venv/bin/python -u scripts/run_mistral_squad_full.py --execute --proposal-sha256 <frozen>
```

source/proposal SHA完整记录launch，独立stdlib verifier不导入模型或项目scorer，复核18原始/判分文本、trace/KV字节/Full计数与阈值，流式重新核3权重与10metadata。未知peak/额外buffer/纯推理阶段时延保持null，wall含hash/load/audit不是性能。成功也不自动跑compact/保护/封存，须另冻结条件级新协议；旧QA false/BoolQ403和48封存不改。完成后按公共模板写run、更新STATUS/WORKLOG/HANDOFF与索引，同步源码/配置/文档，原始只服务器。

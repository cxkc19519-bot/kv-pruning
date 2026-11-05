# 两模型CPU前端预检：执行注册

2026-10-30，用户在已授权实验会话要求“开始下一步”，本轮实现并执行[固定CPU提案](../configs/independent-evidence-frontends-preflight-v1.json)，SHA `83136793b35bd7935a17c34949dec3330527e81968e7c7ae13be782807273e04`。原提案execution/runner字段保留历史false；实际注册以CLI的execute标志、proposal/runner/validator SHA及外层watchdog为准，另存不可变execution snapshot。

服务器绝对目录`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261030-independent-evidence-frontends-preflight-v1`，存在即拒绝。只用原4工程+12DEV，两模型各16题；48封存不编码。Qwen/Mistral固定revision、16元数据摘要、两模板、包版本、11输入指纹全部按原提案核验，任何技术差异停止并存failure和部分输出，不重试或修改提示/输入/预算/样本。预算不足只保存状态，不算技术错误。

执行前设置USE_TORCH/TF/FLAX=0、HF/Transformers离线、禁止bytecode。只导入AutoTokenizer/AutoConfig；audit hook拒绝未列入16文件白名单的模型目录读取、权重/张量文件、socket连接/绑定和子进程。记录实际拦截尝试、metadata打开事件与最终未导入torch等库。唯一元数据16文件合计字节按提案16MiB核验，tokenizer按需重复打开同一白名单文件不算新增元数据对象。

完整native对话48种（每模型16原题+4工程×2替代问题），每种fast offsets与native tokenized两编码，共96；另每模型1次system-only布局探针仅渲染不编码，不计为完整对话变体。Mistral仅system返回BOS时不得作缓存；所有缓存来自完整native串。特殊控制token若有[0,0]offset，只允许以已知special token字符串、ID和文本中对应次序显式映射，完整保留原offset和映射记录，普通token不修偏移。跨问题边界token完整留suffix；全部system/native前缀framing字符覆盖并入预算，工程三个query前缀ids相同，Qwen原14条与旧记录精确一致。

按32个model/case、1/2与3/4、两保护模式，计算128预算状态及配置推导KV字节；不是实测tensor/模型支持。独立检查器仅用标准库，另行从源样本/渲染/offset/ID记录重构边界、字符覆盖、union/floor/字节/覆盖分母，并核原manifest与输入摘要；不增加tokenizer编码，不导入原runner或模型库冒充独立复测。

内部120秒，外层150秒watchdog、TERM后10秒仅终止自有进程组；32文件/32MiB输出、2048输入token/96编码，0权重字节/模型前向/模型回答/GPU/网络。launcher源码、精确命令、PID、UTC、console只服务器保存，输出前固定两新脚本SHA作为CLI参数。命令由外层设置KV_FRONTEND_CPU_WATCHDOG=registered_150_seconds后调用：

```bash
.venv/bin/python -u scripts/preflight_independent_evidence_frontends.py --execute --proposal-sha256 <frozen> --runner-sha256 <frozen> --validator-sha256 <frozen>
```

实际参数记录launch，不脱离watchdog裸跑；原manifest不覆盖后验。完成后更新公共模板run记录与STATUS/WORKLOG/HANDOFF、累计索引。CPU通过后仍不能自动加载Mistral权重；须另冻≤6工程+12DEV的Full-only协议及条件工程范围，当前不运行该GPU阶段。

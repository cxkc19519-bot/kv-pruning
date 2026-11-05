# 同前缀数值差异离线审阅协议

2026-10-31，用户“开始下一步”。只分析已有工程v2的7条float32 logits、56行trace及已固定4.57.1运行时源码，不加载Torch/Transformers/NumPy/tokenizer，不读权重、不查GPU、不更改旧门槛、不算不同裁剪候选的H3排序。

唯一新CPU run `results/20261031-decoder-numerics-audit-v1`。源码、旧工件与已安装masking_utils/sdpa_attention/modeling_qwen2/cache_utils逐SHA冻结。父launcher只下载两份PyTorch官方v2.5.1源码说明（数值精度文档、functional.py的SDPA说明），每URL1次/20秒，保留HTTP成功/失败及原文，不导入执行；失败单列不替代已安装源码证据。不下载模型/数据，不安装依赖。

worker用标准库AST提取精确 `_ignore_causal_mask_sdpa`、`causal_mask_function`、`use_gqa_in_sdpa`、`sdpa_attention_forward`，去除类型annotation后对**纯shape标量stub**执行，无Torch或张量算子。固定假设对应旧记录：CUDA、非XPU/NPU、非tracing、all-ones二维padding、DynamicLayer非compileable；此为Python分支逻辑重放，不是实际CUDA kernel观测。归档提取原函数、全56行推导的mask/GQA/repeat/is_causal/shape；独立复核用独立公式，不执行或import这些函数。

依原causal predicate `kv_idx <= q_idx`，逐1287输入query row核所有可见物理键；两种压缩的批量/逐token须映射到同一保留prefix原位置+已见suffix逻辑位置集合。检查position_ids用于RoPE、cache_position用于物理mask、DynamicLayer追加和mask-size的来源关系；源码/参数上未见集合不等不能代替现场tensor mask验证，旧trace只记录请求值而非内核实际中间值。

对固定4对同路径logit比较新增分布描述：全词表/合法四token上的双向KL、TV、Jensen–Shannon、max概率误差、top概率/概率margin、概率加权公共logit偏移与去偏移RMS；检验原f32值落在BF16网格。不改旧失败分数，不借工程输出挑研究mask。独立标准库validator重算8个scope，合法4-token KL另用Decimal60位；说明浮点近零统计的误差边界，不作总体效应估计。

worker90秒、validator60秒、outer180秒，TERM自己子进程组/5秒后KILL；≤40文件/8MiB。两子进程audit拒绝重型库、socket、子进程、模型/权重读取及run外写入，guard必须0；父登记HTTP来源抓取与子进程流程另计。原工程archive/manifest完全只读，所有新产物仅新run，本地只代码配置文档。

交付必须区分：1）确认的参数/概率差异；2）支持但未证明的执行分支因果解释；3）还缺实际mask、SDPA kernel、GEMM/precision现场观测。PyTorch不承诺数学等价的batch/slice逐bit相同，但文档也不为本项目任意差异背书。原0.25/0.001工程门槛仍false；本次不新选更宽阈值、不启用第三GPU或12DEV。

后续比较合同只能先明确固定执行路径/数值基准、现场分支记录和对研究指标的误差度量，不能用同一工程例最大误差当普适噪声上界，也不能用KL当距离套三角不等式来认证候选排序。没有新证据前，H3与Full12支持仍未知。

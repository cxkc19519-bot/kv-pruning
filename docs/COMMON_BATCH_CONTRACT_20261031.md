# Full与裁剪共享的批量后缀运行契约

2026-10-31。用户“开始下一步”执行共同路径与重复性检查。本契约明确**新的受限研究对象**，不修改旧工程失败，不给旧0.25/0.001阈值换数值或追改通过。

## 研究对象

后续H3若继续，P指固定373-token native prefix预填充后，以固定24-token query+非gold JSON wrapper批量补入所得Full KV下一token分布。Q_M从同一prefix reference按预算gather，再重新处理相同24 IDs。研究的是该固定缓存流程的实际行为，不声称它在BF16下逐bit等于397整段原生计算、逐token回放或精确实数Transformer；旧跨路径等价主张仍failed。

选batch路径的依据是与当前query-known一次logit诊断的使用流程一致，并且现场观察已证明Full/compact的batch suffix都使用显式mask、展开KV头和efficient家族；tokenwise额外引入GQA/Flash分支。不能在看到开发输出后为各候选挑不同路径。没有据工程分数选择更好模型/提示/数据/预算，本轮仍只原2工程组，12DEV模型调用0。

新入口把物理causal mask显式化：Full物理prefix373、裁剪186；每个suffix query j允许k<=physical_prefix+j，形状[1,1,24,physical_prefix+24]、bool，传入Qwen的full_attention字典。position_ids保持原373..396，cache_position用物理位置，prefix已有RoPE不重编码。原生prefix预填充仍用此前固定HF路径。显式mask的实际字节在调用前保存、调用后hash不变；独立从字节重建每行可见集合。未强制torch.sdpa_kernel、未改变dtype/精度/backend开关；必须现场观察所有suffix仍为efficient并满足metadata合同。

## 8候选与信息边界

同一prefix-only WindowScores(window64,avgpool kernel5)来自本项目已审计pilot.py（固定SHA，非nano-vllm），28层×4KV头分数作float64固定顺序均值，随后按分数降序/位置升序填充预算。此候选是**本项目prefix窗口注意力的跨层跨头平均适配**，不是原版SnapKV/per-head策略复现，不作为新算法。另有recency1、固定Random seeds2026103101–06各1，共8候选；不同group相同长度时随机位置相同，不当6份独立实验。

所有候选共享floor(373/2)=186 prefix槽，sink4/recent64的68锚点收费，剩118；每层/head共用其固定原位置，不保护完整system、不加预算。Full/compact的K+V prefix bytes与原始gather逐字节可核，半prefix预算不等整进程显存减半，query/wrapper新KV不计为被裁剪prefix。候选只接收prefix统计/长度/seed，不接收query、gold或任何输出。随后计算KL是query已知的oracle诊断，不是部署选择器。

## 预先固定的新正确性标准

1. 同一prefix无hook/WindowScores hook两次预填充，所有28层K/V和prefix末logits逐值相同，hook在finally恢复原集合。否则停，不换hook/后端找通过。
2. 真实gather所有候选逐值一致、无共享存储，reference全过程不变，mask字节与物理/逻辑位置合同一致。
3. 每组Full+8候选各算两次：第1遍正序、第2遍反序，均从reference新建分支且同一批量后缀。每状态152064维logits逐字节相同，所有Full-global、Full-top128、Full-top256、合法{32..35} KL分值精确重复。**这里没有放宽误差阈值，要求同路径零差异；它回答重复性，不回答旧跨路径等价。**
4. 现场1008 suffix SDPA元数据全显式mask/GQA=false/28 KV头，profiler CPU scope内efficient operator/kernel证据完整；未知/变家族即停，不强行选后端。

两组共36个归档分布（18状态×2），40模型forward/2356输入token：每组2次373 prefix +18次24 suffix。与此前14观测上限不同，是本次为了8候选逐个复查重复性而新登记的工程资源，不扩数据/预算/主实验。score hook还有额外Q投影和注意力统计操作，不以forward计数充当总FLOPs。GPU worker600/verifier180/outer850秒，≤128文件/512MiB，512MiB为18份BF16缓存+36分布和原profiler/score证据预留，不按结果提高。

## 独立复核与解释

独立validator只标准库：从28层/head归档分数重算均值/排序及全部6随机seed，检查1008个缓存tensor的BF16 bytes与原位置gather、两份实际mask、36 binary分布相等和72个首次KL值（另一次精确复现），核40次trace/2356输入token。profiler按CPU device type的显式父链复核1008 efficient调用，保留GPU同名annotation。重核4权重7metadata；实际Torch/原生编码仍由worker执行。

工程组的KL值只用于评分实现与重复性核验，不排序候选、不推H3，也不据gold微调prompt或方法。独立数值重算允许1e-8浮点核验误差，只是两种归约实现比对，不是研究效应门槛/统计误差上界。后续若需要判极小分数差，须在开发输出前另定数值不确定性报告规范，不从此例最大误差冒充普适界。

通过后只可称共同运行契约在两工程组上可重复、选择/gather/评分链已验。旧QA/Mistral false、旧16/保护/3/4/BoolQ停止、旧跨路径gate失败均保持。下一步才另冻固定12组Full支持≥10/12及8候选有界筛查，Full不支持或无信号则停。新方法、新颖性、泛化和性能收益仍未建立。

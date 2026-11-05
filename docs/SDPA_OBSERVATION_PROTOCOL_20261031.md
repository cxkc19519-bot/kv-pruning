# 两工程组实际SDPA观测执行协议

2026-10-31，用户当前“开始下一步”继续推进透明记录与真实后端确认。先通过24项CPU检查后，落实[草案](SDPA_OBSERVATION_DRAFT_20261031.md)为独立观测角色。草案false历史不追改；实际执行仅使用新`configs/sdpa-observation-v1.json`及其外部SHA，不读取12DEV模型输出，不改旧数值工程门槛。

沿原2工程组与固定Qwen版本/4权重7metadata/GPU1空闲≤128MiB利用率0/BF16/SDPA/TF32 off/seed20261030；新worker先逐SHA/包版本核对并4次真实HF原生编码。prefix373、suffix24、半预算186、sink4/recent64不变，固定首seed随机与recency，不切后端/精度/掩码或改输入。0生成token、0完整答案、0开发组调用。

每组7末token分布：Full batch plain/observed、recency batch plain/observed/tokenwise observed、random batch/tokenwise observed。plain同时不patch且不profile；observed使用原参数透传wrapper及真实torch.profiler(CPU+CUDA)/record_function。一个observer实例顺序重入、2856唯一标记（两组各51 observed forward×28层），record cap4096。总108 forward/1082输入token/14分布。Full与recency的同路径plain/observed要求float32 logits逐字节相等，原函数恢复和reference hash不变；任何失败保存结果并停止，不以宽tol或相同argmax替代。

用真实profile.events保存event_id/name/cpu_parent祖先图及附着kernel.name/device，保留未聚合数据；按CPU已验inventory提取marker内backend operator与kernel原名。每个marker必须有明确父链的backend operator及kernel证据；若CUPTI/profiler/父链缺失，停止而不静默关profiler或启用其他后端。mask只观察是否None/shape/stride/dtype/device，未采张量值，不把它称为完整现场causal mask值核验；源码可见集合审计边界保持。

原始Chrome trace以Torch自带lossless .json.gz导出，事件图另gzip保存；TMPDIR/tempfile.tempdir固定run/runtime-tmp，原JSON临时文件由库正常生命周期清理，压缩原文保留。clone/gather/reference原始BF16和14 float32分布完整归档。独立validator无Torch/NumPy：从原始字节重算4个plain/observed相等控制、336缓存tensor和gather/reference；逐实际事件祖先重建operator/kernel归属，匹配raw Chrome marker集及2856 SDPA记录；重算108位置trace并重新hash4权重7metadata。分段/batch差异仅描述，不晋升原0.25/0.001 gate。

唯一run服务器results/20261031-sdpa-observation-v1；worker600/validator180/outer850秒，TERM自身进程组后5秒KILL，≤128文件/256MiB，使用本轮递归checked finalizer，先核cap后写status。observer记录错误必须0；audit维持原模型文件白名单与精确拒绝的urllib3 IPv6 probe单列。无安装/下载/后台服务，不操作GPU0任务。

观察成功只代表现场参数/kernel与同路径透明性控制已验，不能说明两种数学路径完全数值等价、误差全部由kernel造成、Full12支持或H3目标排序成立。旧工程failed/旧超限failed/草案false均保持；不自动进入主实验。

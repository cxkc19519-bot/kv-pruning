# 同前缀KV工程v2：修正临时目录

2026-10-31。原[工程协议](DECODER_KV_ENGINEERING_PROTOCOL_20261031.md)与v1源码/登记/失败run保持。v1在Torch→torchvision→distributed导入路径的tempfile.gettempdir可写探测被run外写入guard拒绝，21.708571秒worker exit1、launcher22.371169秒exit1，0forward/logit/编码/生成；不是模型效果或数值门槛失败。

本次另起v2登记/launcher/run，唯一改动是父进程建立run/runtime-tmp，child固定tempfile.tempdir和TMPDIR到该目录；未放宽run外写入guard、网络/权重/模型范围、数值阈值、输入/seed、112 forward/2574 input/14 archived logits或600/180/850秒上限。Torch正常导入需要的临时文件在既定写入范围内，不在系统/tmp创建。临时文件由其stdlib生命周期清理，不作为研究输入/输出；原始缓存/分布/trace仍在run顶层归档。

四个模型shard与metadata复核继续从头进行，失败不注入新run工程证据。v2不读取开发组模型结果、不生成完整答案、不重跑上一轮CPU验收。必须新登记SHA显式执行，失败仍保留，不覆盖v1、不调整数值标准搜索通过。通过后才能给出这两工程组的数值/物理缓存结论。

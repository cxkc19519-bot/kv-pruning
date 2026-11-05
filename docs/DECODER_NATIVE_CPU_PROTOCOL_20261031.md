# H3真实tokenizer与新输入CPU预检

日期2026-10-31。用户“开始下一步”执行上一轮CPU验收后的原生输入步骤；不是从待办推导授权。不加载权重、不运行模型logits、不启动GPU。

## 冻结来源与角色

既有Qwen2.5-7B-Instruct固定revision `a09a35458c702b33eeacc393d103063234e8bc28`；沿既有6 metadata SHA及chat-template SHA，原权重不打开。原始config是28层Qwen2/GQA4/head128、use_sliding_window=false；layout57344 bytes/槽仍只是预测，历史运行时Full Attention验收不自动转移为新GPU工程证据。原始config没有layer_types字段，不能伪称本轮从此字段读到全Full。

`decoder_native_inputs.py`在任何tokenizer/model结果前冻结：2个新工程组+12个新开发组，每组24条独立编号路由事实。12开发组是target位置首/中/末（0/12/23）×A/B/C/D四答案，每格1组；其他事实固定公式，不挑Full正确题。system/user/问题边界/gold及生成器源码先固定。生成文本/编码仅服务器。是受控合成检索诊断，不是新公开基准、真实业务或12个语义独立自然来源；不读取旧48/16，不改旧评分。2工程组不计12开发组。

schema固定为四个完整输出 `{"answer":"A"}`/B/C/D，共同非gold wrapper `{"answer":"`。语法支持整个base词表的所有可用token分段，不假设标签单token；枚举每条合法路径及终止EOS。first branch每个允许token必须唯一确定A/B/C/D之一，所有标签都可达。模型152064维logits中不属于base BPE的token一律不作普通语法token；151643个base词表项、22 added项核对。仅完整输出末端允许本模型EOS，其他added项（包括special=false的工具标记）和额外399个无tokenizer词项的模型行均禁止。实际数量由预检复算。

## 实现与检查

使用既有tokenizers0.22.1和Jinja2 3.1.4，不导入Transformers/Torch/模型库。从原tokenizer.json加载BPE，用固定原chat_template在无tools的system/user支路渲染并独立核对Qwen字面模板；不用自建替代角色模板。新launcher复制自本项目已验CPU launcher后独立注册，旧脚本不修改，不涉及nano-vllm。

原normalizer实际是NFC；文本输入编码与生成token字节拼接分开。按ByteLevel alphabet从151643项base vocab恢复原bytes，验证256单字节覆盖；只用raw bytes计算语法。6个probe包含完整JSON、é、分解e+组合重音、汉字和emoji，对编码/合并解码/NFC字节核对，不靠孤立UTF-8片段的decode。probe不进入模型数据选择。

14组各编码完整native输入与native+wrapper各1次，共28编码，另6 probes，总34。不能假设 encode(native)+encode(wrapper) 等于 encode(native+wrapper)。实际branch input按整段编码；查询边界前完整落在prefix的token可缓存，跨界token留suffix。Full和每候选都必须在此固定branch IDs上比较；不沿用Full query/wrapper KV。逐ID拼bytes重建native文本，检查native prefix共享，计算半预算floor(n/2)、sink4/recent64并集及预测bytes。任何输入>2048token/路径不可达/预算不足停止，保留全14输入，不换题补齐。

独立validator只标准库，不导入被测模块/tokenizers/Jinja：从原metadata以另一构造式重建byte alphabet，检查vocab.json一致；用整个base vocab穷举每个可达语法prefix允许边，不依赖worker缩小的语法词表，复核EOS/全部标签/控制token排除。逐ID还原全部native字节及prefix/suffix边界/预算，重建24事实与gold/位置平衡、所有digest及6个NFC probe。validator不再编码BPE；不能声称它独立复现了Rust BPE算法或真实HF后端适配。

## 运行登记与上限

`configs/decoder-native-preflight-v1.json`先固定source/input/6metadata SHA与版本。唯一新run服务器`results/20261031-decoder-native-preflight-v1`，本地只代码配置文档。同步前读远端AGENTS、CAS摘要，核run不存在；显式传登记SHA运行。worker/validator各60秒，outer150秒，TERM自身进程组、5秒后KILL；归档≤40文件/8MiB。Python audit拒绝模型导入/socket/子进程/权重或非白名单HF metadata及run外写入；worker仅放行tokenizers/Jinja，validator二者都禁。Rust原生文件IO并非由Python audit完整覆盖，实际只调用固定本地Tokenizer.from_file，不宣称OS级沙箱。

通过只说明这14组的原生编码/有限语法/预算可用。Full任务能力、真实KV bytes与同前缀数值/物理gather、主要失配假设仍未测。下一步另冻GPU工程和12组有界logit诊断：Full支持≥10/12、最多108主logit向量、8候选/Top128/256/合法KL、全部输赢平与停止线，精确seed/资源/观测角色需新登记。本CPU不会启动GPU或重跑上一轮18软件用例。

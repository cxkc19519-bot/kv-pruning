# Qwen/SQuAD48独立描述性GPU验证协议

日期2026-10-30。用户在已授权实验会话要求“开始下一步”。执行前冻结本协议、[配置](../configs/squad48-gpu-study-v1.json)、新入口和所有依赖源码SHA；旧scope与CPU提案false字段、旧QA/Mistral关卡及旧输出不追改。本次明确允许原48题的`sealed_descriptive_evaluation`角色进入独立入口；旧HF工程/DEV调度器仍拒绝该角色，不以development别名绕过。

## 输入、实现与边界

固定原48个预留文章组、每组原题/顺序/prompt/gold，沿已核来源与原生CPU输入及144预算计划，不换题、不补齐、不调输出格式。Qwen2.5-7B-Instruct revision a09a35458c702b33eeacc393d103063234e8bc28，实际28层全部Full Attention/GQA4/head128/BF16/SDPA，逐4权重/6metadata SHA验证。没有nano-vllm文件、Hybrid状态、第三模型或新下载。GPU1 UUID由配置固定，加载前新查空闲状态，memory≤128MiB且util=0，否则停止，不操作他人任务。沿既有.venv依赖，greedy128、repetition_penalty1、TF32关闭，无安装或环境升级。

复用本项目固定QwenHFBackend和KV原语，独立新StudyDispatcher接受明确48-ID注册表，绑定cohort/role/group/prompt/gold/input/runtime/condition/budget，每条件一格。工程证据必须来自本run中新建HFOrchestrator的实际dispatch，不注入旧14答或修改旧角色规则。新的runtime摘要含本配置、旧计算描述符和新控制/分析源码，逐请求digest检查；相同输入、原生模板、位置、评分、解码在Full和两个压缩条件保持一致。

统计adapter显式把scorer bool EM转为数值0/1，F1保留null/原因、格式与截断保留bool；绑定完整原answers摘要，接受的result必须与本次dispatch返回值相同。group统计schema与旧scalar core分别生成，后者额外保留任务/F1/格式配对、覆盖边界及实际字节。不能用历史工程证据替代本次证据。

## 先软件、再工程、再Full支持

重型库导入前完成16个合成软件集成用例S01–S16：预算阻塞仍在全组分母、规范化/core/group链；错误role/group/输入摘要/旧runtime拒绝；工程缺失不调用后端；Full支持前禁压缩；重复调度/输入变异/结果变异/错gold拒绝；Full失败后无CI且停止压缩；截断原始EM保留但不计完成；调用上限与Full未完成拒绝；旧case_binding仍拒绝新角色。软件stub回答不算模型回答或科学样本。任何失败保留整run，不生成模型。

沿原两工程题56f991b19b226e1400dd15b8、57280cfc3acd2414000df323，现场重做Full整段原生/native split/custom split共6答，逐token/终止相同，实际cache shape/bytes、clone/reference不变、score hook与未挂hook prefill张量逐值一致。匹配但截断只说明数值路径，不证明任务完成。

随后固定48题各生成一次Full/custom_split。支持线沿输出前scope草案：全部48已记录、task EM≥24、格式≥36、错误0、截断≤4。task/格式在未截断返回中计数，沿已有Full支持实现；原始截断分数另留，不补生成。支持不达标属于有效基线适配失败结果：保存全部48答和144格，停止压缩工程与主阶段，不改模型/题目/prompt/预算/seed/阈值，不报告压缩效果区间。

## 达标后压缩及停止线

仅Full支持true，沿原两工程题重新验证无保护Snap适配、uniform_random各native/custom双路径，8工程答逐token/终止/trace匹配。条件各自verified后才调度该条件主阶段。新工程总上限14答，不当新增科学样本。

原48题Full48格，Snap和随机各45格可行/3格预算不足。半预算严格floor(prefix/2)，sink4+recent64占68槽，不放system保护；3道短题不能容纳锚点，6格记infeasible_budget，0生成，全部48组/144格始终在报告中。最多90个压缩主回答、全部主要回答最多138，总工程+主最多152、生成token最多19456。

Snap是本项目prefix-only适配，不是作者原版SnapKV；固定window64/kernel5与原选择实现。随机seed20261028，按group/layer/head确定性CPU随机分数。两者相同有效槽预算，记录实际K+V prefix/final字节，gather逐值相等、sorted unique位置/锚点、原始RoPE逻辑位置与压缩物理位置分离。selector不能看到query/gold/生成结果。prefix scores、maps、raw ids/text、trace、逐请求证据均归档。所有case的score hook与无hook cache相同、reference内容hash不变；跨phase同prefix重复prefill/scores要求相同。任何数值/身份/证据/预算/资源失败立即停止，记录失败与未运行格，不重试。

## 报告与独立复核

primary为各压缩条件joint交付率相对共享Full的差，分母全部48组。成功要求ok、未截断、format=true、EM=1。已终态预算不足交付0而语义N/A；未运行/协议停止不造效果。完整阶段+Full支持true才运行已验10000次共享组配对bootstrap，seed20261030、95%逐项percentile/type7；保留全部Full错误、不仅比较可行子集。严格任务/F1/格式配对、分母、条件损坏/未知覆盖边界与截断单列，覆盖边界不是CI，区间无总体风险或同时比较认证。

独立validator从raw重新decode和独立重判全部生成文本，重算全部144状态、Full支持线、实际K/V字节与每步位置、现场工程token/trace、一致输入/权重/metadata SHA；从归档prefix分数重排Snap，使用空CUDA可见性的CPU Torch生成原随机数并重算全部layer/head maps；独立重算all48 joint/bootstrap索引流和区间，不import主scorer、study、core或统计实现。Tokenizer仅decode，不重新编码主输入。只有独立复核通过才收尾为已核结果。

## 资源与归档

服务器项目根`/home/user/jhk/project/Directional Exploration/kv-pruning`，唯一run `results/20261030-squad48-gpu-study-v1`，原始结果只在服务器。worker墙钟900秒、外层960秒、TERM后20秒KILL自有进程组；独立复核180秒、外层200秒、仅自身CPU验证进程。最多256文件/128MiB。launcher/console/实际argv、软件结果、输入/源码/模型摘要、失败、原manifest与后验derived manifest全部保留，旧原manifest不追改。进程结束后只读GPU状态和自己的PID，更新STATUS/WORKLOG/HANDOFF与索引，不启动服务/后台队列。

本轮不涉及保护/3/4/BoolQ/第二模型压缩/旧16题。48文章精确去重不保证语义或预训练独立；当前为固定一模型/任务/预算/随机seed的描述性外部于DEV的验证，不推出总体安全、性能节省、首次发现或毕业/发表保证。审计保留Full reference，半prefix字节不等于整进程显存减半。结果允许为负或Full支持失败，均按协议保留并收敛结论。

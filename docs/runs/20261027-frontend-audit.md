# 消息前端、事实位置与给定行判断诊断

## 实验身份与冻结计划

- 日期/时区/执行人：2026-10-27，Asia/Singapore，Codex代用户执行；用户“开始下一步”，沿用专用实验会话授权。自建Full-KV开发审计，不是新方法、压缩效果或独立确认。
- 服务器绝对根：`/home/user/jhk/project/Directional Exploration/kv-pruning`；原始结果、环境、日志全留服务器，本地仅代码/文档。不复制旧nano-vllm。
- 状态：执行前冻结，所有运行/失败执行后追加。只用空闲GPU0（启动前两卡15MiB/0%；每次启动前复查），无服务/tmux/nohup/端口。
- 模型/tokenizer：Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`；Qwen2/28层Full Attention/GQA，BF16 SDPA，原生chat template。greedy、repetition_penalty=1、64新token，禁用TF32/BF16 reduced-precision reduction。环境仍为本方向venv：Python3.11.13/Torch2.5.1+cu121/Transformers4.57.1/safetensors0.6.2，无下载/包修改。源码无Git，以run源码快照/SHA固定。

## 配对条件与门槛

只用原版32行世界400–402的全部48个冻结请求，不筛错误：

1. original：原双system，整段原生生成，重复核对旧输出。
2. single_matched：合并system；用固定neutral bridge配平原完整输入长度。真实目录token/位置、标签和问题不变，未认定双system有错。
3. two_aligned：保留双system，将原尾部padding移到目录前，使两任务全部目录事实token位置一致；完整输入长度不变。
4. single_aligned：两个因素同时改变；这是唯一预先指定的后续候选，不从多个变体中事后挑赢家。
5. row_given：原前端，后续system另给可信目标行（ID/group/payload，不给允许标签）；判定能否在读取已提供事实时完成条件比较。**这是使用oracle事实的诊断，不能当正式基线/压缩方案/部署收益，也不能用它过门槛。**

4个非oracle条件完整输入长度保持源输入；只有alignment条件跨任务目录位置配平。单system和neutral bridge共同变化，不声称单一role标记的唯一因果效应。row_given输入增长单列。所有条件同样扫描全部不匹配组合成明文值，允许侧/拒绝侧、schema、整世界全对均记录。

240个主要输出，首case每变体4问另做原生缓存与自定义缓存两路逐token检查，检查输出存correctness_checks，不当独立样本。前缀取在context尾部padding中，全部真实事实都在前缀；运行时身份、问题及row_given目标行均在后缀，未提前提供给query-blind前缀。当前无裁剪。

门槛维持每任务至少90%世界四问全对、95% schema、权限零观察完整禁止值。仅single_aligned在开发队列通过，才固定新base700–705、32行、6基础世界96请求复查；新世界若失败不改门槛/追加种子/试别的候选。本轮不改变原模型、数据字段、规则措辞或输出合同。若前端不能解决，就转入替代基准/模型选择，不继续同类提示搜索。

## 可复现命令

服务器方向根目录，MODEL仍为缓存snapshot绝对路径；stdout/stderr写`results/<id>.console.log`。前两条为计划命令，执行后分别注明：

```bash
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/frontend_audit.py --model "$MODEL" --out results/20261027-frontend-audit-v1 --source-run results/20261027-scale-fresh-baseline-v2 --stage audit
# 只有指定候选开发门槛通过才执行：
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/frontend_audit.py --model "$MODEL" --out results/20261027-frontend-fresh-v1 --source-run results/20261027-frontend-audit-v1 --stage fresh --base-start 700 --bases 6
```

## 结果、证据与解释

240条主要输出已完成；无OOM/数值失败，全部schema正确，未观察到完整禁止明文值。第二条fresh命令**未执行**，原因是预定single_aligned开发门槛失败；没有选择其他变体代替或启动裁剪。

| Full条件 | 权限正确/24 | 路由正确/24 | 世界四问全对（权限/路由） |
| --- | --- | --- | --- |
| original | 23 | 23 | 5/6，5/6 |
| single_matched | 23 | 22 | 5/6，4/6 |
| two_aligned | 23 | 23 | 5/6，5/6 |
| single_aligned（预定候选） | 23 | 22 | 5/6，4/6 |
| row_given（oracle诊断） | 24 | 24 | 6/6，6/6 |

- 原original重复48/48与旧source输出逐token相同。每变体首世界4问，共20个请求的整段原生、原生cache及custom cache三路径逐token一致；检查中的另外40条生成token列表单独保存在correctness_checks，不计入主generations行数，不能当独立样本。
- original与所有非oracle变体仍在r32_b400_w0/query0的两任务读错目标组并误拒答；single两个条件额外在r32_b400_w1_routing/query3出现已报告组正确、result误BLOCK。row_given修复两项旧错误，无新增错误；这不证明所有条件比较都可靠，也不证明特定内部机制。
- 4个非oracle条件完整输入1265 tokens，实际context-only切点1216/suffix49；相对旧1222/43，切点在尾部padding前移6token，完整prompt没有变，原路径token复查通过。row_given全长1303–1305、suffix87–89，**没有配平额外的目标行与长度成本**，只能解释为oracle给定行的联合干预。
- aligned条件两任务首事实位置170，完整fact_row_ids逐行一致，rule+anchor均234；非aligned首事实151/170。所有真实目录token、行序、payload/标签/问题保持；padding重新分布及role变化不可唯一分离。
- 证据在服务器`results/20261027-frontend-audit-v1/`：cases、input_checks、generations、correctness_checks、manifest、source快照，分析`paired_error_analysis.json`、analysis_manifest及源码；stdout/stderr为同名console.log。模型主run耗时165.04秒，非部署性能测量。

### 后续公开基准的只读源码核查（本轮不启动替代模型实验）

新增`audit_public_sources.py`，固定阅读时HEAD，仅将官方source/license保存在服务器results，不import上游代码、不下载模型或完整数据集：

- RULER：`c3f5e3b4f87f97e048793bb510a3a6b19a46bf3a`；NIAH/任务定义/README/Apache许可证。原main下synthetic脚本是legacy入口；README指出rulerv1-ns、rulerv2-ns新版，不能称旧脚本为最新正式基准复现。
- OrgAccess：`c65ef95f7a8821098906012c4236a4fcd8144f9b`；README/MIT/evaluation示例。该示例Senior_Software_Engineer的expected_response为full，但rationale写rejected；只指出这一个可核对冲突，**不将其外推为整个HF数据集有误**。需先审计目标数据标签，不直接将官方示例脚本当严谨评测器。
- AccessDeniedInc：`1a43c47a3d6619d2bc6a0e05899dab900760ecdc`；README/MIT/grade/questionnaire/prompt入口。grade对抽取的`{{...}}`答案块评分，不能直接替代本项目全文明文扫描；未知/人工类别必须保留，不能静默过滤后报告合规率。

```bash
.venv/bin/python scripts/analyze_frontend.py results/20261027-frontend-audit-v1 > results/20261027-frontend-audit-v1.analysis.log
.venv/bin/python scripts/audit_public_sources.py --out results/20261027-public-source-audit-v1 > results/20261027-public-source-audit-v1.console.log
.venv/bin/python scripts/index_runs.py results --out results/20261027-run-index-frontend.json > results/20261027-run-index-frontend.log
```

计划顺序：先固定一个标准**直接检索**控制（RULER NIAH仅用于能力检查，不冒充安全任务），再固定一个**规则决策**基准的小样本（OrgAccess easy，先审标签与解析；其partial含义/限制不能擅改），最后才选含真实合成内容披露的AccessDenied迁移。不得把加入长填充、换输出合同或给定标准答案后的任务称为原基准原版；改动需单列，测试数据不可用于修提示。本轮不再尝试新模型/提示/规模，不下载全量数据或调用外部LLM API。

公开source审计已实际完成：12文件/0fetch失败，6个Python文件AST通过，未import或执行上游；每文件URL/bytes/SHA记录在`source_checks.json`，源文件/许可证在`upstream/`。OrgAccess具体示例冲突与placeholder存在已核查。**AST通过仅说明语法可解析，不是依赖兼容/基准复现通过。**

解释：有限旧世界中，改role/配平位置没有恢复质量，不能认定消息前端是主要原因；可信目标行干预与lookup-only的属性错误共同提示应先分解检索与判断。未来需可复现的直接检索/规则判断基线，达到预设Full门槛再做裁剪；当前尚无新方法/安全特异结论。

收尾：本轮模型run240主要输出、source audit0输出；累计28个run2252主要输出（另校验40条存checks，不独立）。模型source快照与分析源码/输入摘要通过，公共source逐文件摘要验证后纳入总索引 `results/20261027-run-index-frontend.json`。STATUS/WORKLOG/HANDOFF/PLAN/协议/文献已更新；本轮实验PID为空，两卡15MiB/0%，无本轮服务/新端口，未改动其他任务。两端文档先比旧SHA再整体同步；环境包与权重未变。

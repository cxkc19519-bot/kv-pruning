# 取消请求后的资源记账：源码契约与立题门槛

日期：2026-10-30，Asia/Singapore。用户要求“开始下一步”，接续既有第2线索。本轮只读公开资料与服务器安装源码，没有运行模型、作者代码、服务或压测，也未修改上游实现。

## 结论

**本候选当前不进入论文方法开发或GPU实验。** 查到的取消统计缺口有源码依据，但已经公开报告并有修复PR；泛化的取消尾部计算、输出失效与重试浪费也有直接近邻。更窄的“实际配额可被绕过”仍缺明确部署契约、记账执行方和端到端证据，不能从指标缺失推出来。

这不等于证明所有网关都正确，也不等于否定可做工程改进。当前应结束这次有界门槛审查，不通过换引擎版本、重现已知缺口或自行搭一个只按完成输出扣账的弱服务来制造新发现。

## 已核对的取消链

固定vLLM **0.32.0 / `5df63a7203cdb9328d824a27b682e77c7b9928be`**。官方发布列表查询时最新稳定版仍为0.32.0；这是版本选择记录，不是对全部已知漏洞的安全认证。[官方发布](https://github.com/vllm-project/vllm/releases)

服务器13份相关安装文件的Git blob逐一与官方来源匹配，路径与阅读范围见[来源索引](CANCELLATION_ACCOUNTING_SOURCES_20261030.json)。主要范围为HTTP Chat、AsyncLLM、默认EngineCore.step、scheduler及metrics；未全面审gRPC、Responses、DP路由、异步调度和分离部署。

| 边界 | 所审源码事实 | 不能由此推出 |
| --- | --- | --- |
| HTTP断开 | route使用取消装饰器；handler返回StreamingResponse后由响应对象处理断开监听 | 用户“不想看了”自动等于transport已断开 |
| 前端取消 | AsyncLLM捕获取消/生成器退出后发abort；先从OutputProcessor移除请求，再发送ABORT给EngineCore | 发出消息即代表所有GPU工作物理停止 |
| 调度停止 | 默认step等待已提交执行结果，然后处理abort队列；scheduler移除running/waiting请求并走释放路径，connector可能延迟释放 | 可撤销已发射kernel、任意时刻立刻归还全部资源 |
| 结果/统计 | 已移除请求的晚到输出被忽略；正常完成统计由另一入口处理 | 所有执行工作都能从最终usage或完成histogram还原 |

对应固定源码：[HTTP取消包装](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/serve/utils/api_utils.py#L51)、[AsyncLLM取消](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/async_llm.py#L776)、[默认step边界](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/core.py#L667)、[scheduler释放](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/core/sched/scheduler.py#L2649)。这是静态控制流核查，未测实际取消延迟/显存回落或并发正确性。

后续若测量，至少要区分用户放弃、真实断开、前端接受取消、调度移除、最后GPU工作结束和记账结算等时点。仍在缓冲队列里的旧输出，也不能直接算取消后新执行的GPU工作。

## 找到的统计缺口已经公开

固定`output_processor.py` 552–614的abort路径会移除状态、产生ABORT终止输出，却没有调用正常完成统计入口；710–719又会忽略已移除请求的晚到输出。metrics logger的完成histogram依赖finished_requests，故不能假设该路径会产生正常的终止统计。[固定OutputProcessor](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/output_processor.py#L552)、[固定logger](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/metrics/loggers.py#L1289)

但这已是9月的公开[issue #55634](https://github.com/vllm-project/vllm/issues/55634)。关联[PR #55940](https://github.com/vllm-project/vllm/pull/55940)在本次查询时open、未合并，head `805d873486f5724f026bbf0fd15fac16fad532e2`；修复讨论已涉及取消前无token、缺失时间戳、实际prefill计算量、父子请求及engine归属，不能把这些边界再当新贡献。仅定向读PR说明、相关diff和讨论，未应用补丁或运行其测试。

issue作者的旧版本测量不是我们的0.32.0运行结果。也不能把其特定计数差外推为所有取消阶段的精确GPU工作量：input长度、已计算prefill、已接受输出、被丢弃的在途结果、draft/rejected token及GPU时间本来不同。当前只确认相关源码结构，不宣称全局counter完整、不宣称漏计金额或配额绕过。

## 谁定义并执行配额

所审vLLM鉴权middleware检查允许的Bearer token；SharedAdmissionStats汇总前端进程请求数。它们不是按租户GPU时间结算的实现。metrics文档的用途是可观测性与容量规划，也不能自行解读成计费保证。[鉴权源码](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/serve/middleware/authenticate.py)、[admission源码](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/admission_control.py)、[metrics契约](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/design/metrics.md)

HTTP Chat支持最终usage以及可选的连续usage；最终统计帧不保证在连接已断后送达。但“最终usage未到达”与“账本将已消耗资源全部退还”之间还隔着实际网关策略，不能把两者等同。[usage选项](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/serve/utils/api_utils.py#L289)、[最终usage路径](https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/openai/chat_completion/serving.py#L839)

作为实际执行方的例子，LiteLLM文档明确区分key/team/user预算、TPM/RPM和并发限制。[官方文档](https://docs.litellm.ai/docs/proxy/users) 定向读其main分支limiter固定blob `14b08a09116fc95e7f5a0aa5736bb937a1a1dcd5`：已有调用前预留、失败时按可恢复部分usage结算、取消时释放并发槽等路径。不同callback/取消路径不能混为一种退款策略；本轮没有完整审spend hooks、provider适配器或实际部署开关，也没有证明所有配置都安全。[limiter源码](https://github.com/BerriAI/litellm/blob/main/litellm/proxy/hooks/parallel_request_limiter_v3.py)

因此，重立题必须先固定：谁被限额、单位是语义token/金额/请求数还是实际算力、什么时候预留/结算、取消后什么可退、重试和在途工作由谁承担。目前项目没有一套已审计且被证明违反这些规则的网关部署。

## 直接近邻与差异

| 来源 | 已覆盖部分 | 当前不能拿来支持的主张 |
| --- | --- | --- |
| Retire，2610.01160v1，10月1日 | 取消后的过时计算、输出权威失效与KV交接；还讨论租户pin配额 | 它的pin配额不是货币/TPM账本；不能说它解决了所有计费问题 |
| Sorami公开仓库README | 区分transport close、停止读取及继续读取，列引擎/网关测量范围 | 作者明确测scheduler接受事件与logical terminal，不是GPU时间或账单 |
| GRIEF，2605.11202v1 | 已将Cancel/Disconnect时序与跨请求干扰纳入测试/确认框架 | 只加取消事件的通用fuzzer不构成新方法 |
| GHSA-8wr5-jm2h-8r4f | 已公开的并发投机/取消相关非法token崩溃，列修复版本 | 重现已修crash不是新发现，也不能证明漏账 |

阅读入口：[Retire §4–6/附录A.3](https://arxiv.org/html/2610.01160v1)、[Sorami作者README](https://github.com/Sorami-Consulting-AU/llm-tokens-after-cancel)、[GRIEF §3–4/附录A](https://arxiv.org/html/2605.11202v1)、[官方安全公告](https://github.com/vllm-project/vllm/security/advisories/GHSA-8wr5-jm2h-8r4f)。Retire是作者基于0.13.0的研究实现，不等于合入当前0.32.0；没有验证其代码或复现论文数字。Sorami canonical report本次工具不可访问，仅作者README读通；未读/下载其raw journal或分析JSON。GRIEF未运行。上述来源均有阅读深度限制，详见JSON索引。

## 决策与下一步

| 候选主张 | 门槛结果 |
| --- | --- |
| 取消后还有计算，所以是新漏洞 | no-go：有限不可抢占尾部与直接近邻都须排除 |
| 取消没有完成histogram，所以提出补全统计的新论文 | no-go：issue/PR已直接覆盖 |
| 取消可持续绕过真实配额并伤害其他用户 | 未建立：缺实际契约、执行链、工作归属和强对照证据 |

若未来有独立机制证据，强对照至少包括请求率限流、调用前预留、已用额度不退、部分usage/服务时间结算以及正确的端到端取消。应先证明这些简单适配不足；当前没有此证据，不开发复杂算法或启动压测。

本轮0新主/工程回答、0实验run，累计沿用**92run2732主要输出**。未安装依赖、加载模型、建服务、查询GPU或操作他人任务；仅读旧自有PID退出状态。服务器没有rg，已用标准库路径/文本读取替代；GitHub参数初次校验拒绝后修正成功，网页PR超时后连接器读取成功，未绕过访问限制。没有新模型/后台任务或执行配置，既有失败和A搁置保留。

**本次审查结束，没有新的模型执行队列，也不自动转查低优先第3项。** 下一次应先做一页选题收敛稿：区分已有可复用工程证据、已被覆盖的论文主张及真正缺失的实验条件，结合“毕业不强制发表”的约束讨论可完成范围。不能把已知bug修复、累计运行数或一个负结果直接包装为已确认硕士选题。本轮更新STATUS/WORKLOG/HANDOFF/PLAN/LITERATURE与调查入口，并同步服务器；GitHub项目远端仍未配置，未发issue/评论/PR。

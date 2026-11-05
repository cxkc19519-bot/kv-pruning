# 条件级预算准入与工程证据接口

2026-10-30。为解决新DEV中“预算不可行、没有工程证据、已有诊断输出”被一个总pass混淆的问题，新增标准库模块`reliability_execution_contract.py`。已完成[服务器CPU验收](runs/20261030-condition-admission.md)：20软件用例、60计划格及独立回读全部通过。本轮没有生成新模型输出，也未改旧driver/分数/关卡。

## 状态与接口

| 层次 | 取值/用途 | 不应推断的事情 |
| --- | --- | --- |
| budget | ok / infeasible_budget；由精确保留率、完整保护与anchors并集计算 | 预算足够不代表工程路径已验证 |
| engineering | verified / failed / insufficient_coverage / unverified_budget_infeasible | 没有可执行工程题不能记为通过；已验序列不等任务能力通过 |
| admission | eligible_for_configured_run / blocked_budget / blocked_engineering_failed / blocked_engineering_unverified | 有准入不代表已经执行，或新输入的逐token路径已单独验证 |
| execution | ok / error / not_run / infeasible_budget，truncated另列 | 实际生成不等于工程证据覆盖，截断不等未生成 |
| metric | 沿已有任务/格式/连续分及N/A合同 | 路径一致不决定答案正确或完整交付 |

接口依赖原`reliability_system_core.budget_plan`，不改变它的shape、预算和报告语义：

```text
plan_case(case_id, prefix_tokens, system_positions, condition_spec, runtime_digest)
  → 每case/condition的数学预算与条件指纹
engineering_evidence(condition_spec, runtime_digest, engineering_plans, observations)
  → 每条件工程覆盖与逐case验证证据
admission(case_plan, evidence)
  → 未来配置是否有资格执行
execute_admitted(decision, operation)
  → 通过才调用一次operation；被阻止时完全不调用
historical_observation(decision, archived_row)
  → 保留历史执行与诊断范围，绝不删除/重评分/重生成
```

这不是访问授权/安全隔离机制，调用者与runner仍需核验用户授权、输入hash、版本与资源上限。`execute_admitted`本轮只用软件stub验调用边界，**尚未接到真实HF加载/生成调用**。旧driver及旧snapshot保留，不能把新模块的CPU验收说成生产后端已完成改造。

## 证据绑定与验证范围

条件指纹绑定runtime digest以及condition_id、selector源码版本、保留比例、是否完整system保护、sink/recent、要求的工程题数/路径及trace比较规则。回放适配器先核Full/压缩实际snapshot中模型、解码、形状/dtype/版本/runner/source哈希全部相同，才从这些固定归档生成scope；它不凭旧`engineering_gate=true`构造证据。

Full要求两工程题各native whole/native split/custom split三条序列完全相同；compact要求同条件两题native/custom token、termination flag和位置trace相同。每条路径还须有相同输入digest、非空整数token序列。缺路径、错误、token/trace/termination不一致分别保留状态；重复证据、过期指纹、同条件错input、矛盾的预算不可行声明会拒绝。

本接口验证的是**列出工程题在固定decode上限内的序列一致性**。某Snap工程题的两路径都达到128token上限且序列/trace相同，记`verified_at_decode_cap`、`output_complete=false`；该条件仍有数值路径证据，但不因此获得任务支持或完成率通过。可观察行为的这些维度不能合成一个“成功”。

对所有工程题都预算不可行的保护条件，状态为`unverified_budget_infeasible`、verified_cases=0，禁止用空集合上的all通过推成true。预算可行但没有同条件完整证据的DEV格也被未来准入阻止；不会自动借用无保护条件的证据、减保护范围或免费增加预算。

首次工程验证本身是另一个有界stage，不要求它先拥有完成后的工程证据；本模块的严格准入用于工程之后的DEV/确认执行。统一runner接线时须分清bootstrap工程stage与正式执行stage，避免以同一个门槛造成自锁，也不能用该区分绕过DEV证据要求。

## 本轮60计划格的处理

| 条件 | 数学预算可行/12 | 工程状态 | 未来可准入/12 | 已有历史输出 | 其中仅诊断 |
| --- | --- | --- | --- | --- | --- |
| Full | 12 | verified，两工程题 | 12 | 12 | 0 |
| 适配SnapKV | 12 | verified，两工程题，其中一题截断序列一致 | 12 | 12 | 0 |
| random | 12 | verified，两工程题 | 12 | 12 | 0 |
| Snap+system保护 | 2 | 两工程题均预算不可行，未验证 | 0 | 2 | 2 |
| random+system保护 | 2 | 两工程题均预算不可行，未验证 | 0 | 2 | 2 |

汇总：36格满足未来配置准入，20格budget blocked，4格预算虽可行但engineering unverified blocked。历史实际40输出+20不可行保持；4条历史保护DEV输出按原协议产生，仍完整保存在原run中，只增加“工程范围未覆盖的诊断”注释。**新规则不追改原协议，不删除这4条输出或让旧QA门槛由false变true。** 准入结果不是另跑36条模型回答的许可清单；当前没有启动新GPU队列。

本轮适配器来自已观测历史plan，不能把新指纹计算时间写成旧实验前的注册。它展示的是新严格执行接口将怎样处理同样输入；未来新run须在产生输出前锁定对应计划、源码与工程证据。

## 实现与验收边界

新增模块、20软件用例和CPU runner，旧core/adapters/HF脚本均不改。软件用例覆盖完整/缺失/不可行证据、token/trace/termination/input错配、stale scope、重复证据、空token、截断一致性、缺cell、历史保留和阻止callback调用；不是20个模型样本。外层独立集合运算与原token/trace重建核对60格的预算/准入及历史hash，均一致。

下一步将此接口接入新的HF编排壳，先只dry-run产生每stage/case/condition计划和证据来源；不复制/覆盖旧driver，不重新生成已有DEV。若新编排/后端版本改变工程scope，必须在新的有界工程协议中验证后才能运行DEV，不能自动沿用旧fingerprint。BoolQ来源仍暂停、封存48/旧封存16不动，第二模型/新预算不在当前执行队列。

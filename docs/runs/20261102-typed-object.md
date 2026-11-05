# 明确类型分类记录族：开发性正确性检查

## 实验身份

2026-11-02，Asia/Singapore；用户授权“开始下一步”。服务器绝对路径：

`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261102-typed-object-semantic-v1`

单次CPU小检查完成，两后端各21/21符合事前业务谓词，独立验收通过。研究者已看过旧45题结果；这是新范围的开发性检查，不是无偏抽样或独立确认集。

## 新范围及预注册

应用是固定字段的分类记录：根类型object，字段k000等均required，禁止额外字段；每个值必须为字符串red或blue。固定字段数1、2、4，不混用无type关键词、oneOf或Unicode转义样例。该约定在作者库运行之前冻结，生成器不读取旧结果/28个共同正确项；旧45题的完整失败继续保存。

每种规模7例：全red、交替blue/red两个正例，缺字段、多字段、非法枚举值green、值类型为整数0、根类型为数组五个负例。标签由“精确键集合且所有值为red/blue字符串”计算，独立validator另写业务谓词并核schema与7种fixture身份，不导入生成器/后端。

- [生成器](../../scripts/typed_object_family.py) SHA256 `8d40685c2b723c862eb56e3629bd65983abb2f36edfe67ad9ec5567d2f01b221`。
- [执行登记](../../configs/typed-object-semantic-v1.json) SHA256 `57dec142ca2cd486cc8edeecebf4a8ec7185c035f96b643a6310432523b11151`。
- 服务器selection SHA256 `e69dcf899a4d18494c36484e421cc05a2b05e43fe344b3b6848e56b31d193b94`。
- 输入归档literature/20261102-typed-object-family-v1：6文件32587bytes，manifest `dd4aaa2ba3fa3f8da88239f42ed048be6c25aa5da154f58e9f5e2e1fe8bb85cc`。生成/固定输入仅标准库准备，不计新增实验run。

源接口沿用已固定XGrammar0.2.8、llguidance1.7.6；新选择基于公开接口支持的object/properties/required/additionalProperties/string/enum，并以本次有限样例实测，不预先声称两后端语言等价。

## 可复现条件

复用有限UTF8合同a2e8333f…（普通id0..132，EOS133，vocab134）。Python3.11.13/Torch2.13.0及runtime101+dill2不变。单fresh worker、亲和性≤2/Torch线程1、CUDA隐藏并后验false，原精确ImportBoundary v2，禁网络/模型/模型tokenizer/权重/GPU查询/安装/服务。fatal抓栈，无周期线程/GDB。

新typed_object_probe和独立validator从旧正确性harness另存，旧文件/结果不改。X RAW词表、compiler cache false/max_threads1/8MiB，strict_mode=false、any_whitespace=true；LL不启coerce/lenient。每例新matcher，mask为5词int32/LL位掩码与0/200偏置交叉，显式EOS；全量记录错误/unknown，禁止据结果补样本或重试。

导入+适配从父spawn起≤30秒、适配共用5秒；每schema组从raw payload提交起共用5秒，包含解析、compile/conversion及该组7例。worker120秒/launcher150秒；硬上限6schema/42matcher/1186 mask位置/1779 mask API/1186 commit/7516计数边界。输入计算的上限事前冻结，不按测得值调整。worker文件8MiB/归档64文件16MiB/core0，内存RSS不构成OS硬隔离。本轮不宣称单请求SLO、资源回收、取消效果或真实模型词表性能。

服务器根目录实际执行（各目录一次；仅记录，不自动重跑）：

```sh
.venv/bin/python -I -S -B scripts/typed_object_family.py literature/20261102-typed-object-family-v1
.venv/bin/python -I -S -B scripts/typed_object_probe.py --execute --registration configs/typed-object-semantic-v1.json --registration-sha256 57dec142ca2cd486cc8edeecebf4a8ec7185c035f96b643a6310432523b11151
```

## 结果与证据

| 后端 | 符合业务标签 | 正例接受/EOS停止 | 负例拒绝 | error/unknown |
| --- | --- | --- | --- | --- |
| XGrammar | 21/21 | 6/6 | 15/15 | 0 |
| llguidance | 21/21 | 6/6 | 15/15 | 0 |

3种字段规模全部通过；42格均由独立业务谓词与原mask/commit/terminal/时钟重算。6schema/42matcher，646 mask位置、969 mask API、616 commit、2347计数边界，12次正例EOS停止。无计时、mask-bias或mask-commit违例，CUDA false/最终guard拒绝全0，只读query一次。旧45题语义gate、旧257-byte/FF与cold5 gate不改。

导入2.578206847秒，适配0.002317243秒，launcher3.079202178秒，worker/validator/launcher均exit0。单次小输入工程值不用于速度比较。worker退出就绪失效，无可跨PID复用对象。

- 原始48文件2333563bytes/manifest `494acca21215720b2aeea96cdbde1fcc15b044a513b39e89bb2a2f365aaba5d3`。
- 独立verification `2f83f2d256e00682da156861f921115a96da817c9bea2322205102786dfe4278`。
- 输入及原始归档逐文件回读；source/input/runtime101+dill2不变。
- launcher2781129/worker2781132/validator2781134/query2781133均核不存在，无后台、服务、端口、安装或native队列。
- 服务器closure results/20261102-typed-object-closure.json SHA256 `4e6e9c548a4634a3b9fe104965cab70b8a606ffbadd949aaf4b3b124784a47db`。
- 新索引results/20261102-run-index-typed-object.json SHA256 `83bdc4b7a4c0734bc96b0312a7f8f5f367b11719001c7a4dc95170a30ff09403`，147runs3038历史主回答；本轮1CPUrun/42语义结果/0模型回答。

## 结论与下一步

该小型明确类型记录族具备已测样例的功能对照前提，覆盖仅1/2/4字段的固定字符串枚举记录。没有证明泛JSON Schema语言等价、较大规模正确性、取消及时性或正常租户干扰；N1科学实效和新颖性仍未建立。

下一步冻结有界资源可观测性小筛查：先明确CPU/槽位占用是否可测、正常探针是否回到同一槽，以及现有和较新后端强对照的兼容性。沿用已通过的观测器合同，不重做12/8/23/425和旧45题；新规模/输入/预算与停止条件须事前固定。不得仅从旧llguidance缺少某API判新缺口，不能跳到模型或压力/取消攻击。本轮不启动这些后续实验。

STATUS/WORKLOG/HANDOFF/PLAN/README与readiness同步服务器，原始仅服务器，GitHub未配置未push。旧负结果、H3停止/泛KV暂停保持。

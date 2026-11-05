# 原输入字节差值与组合导入栈最小诊断

## 实验身份

- 日期／时区：2026-11-01，Asia/Singapore；本实验会话用户“开始下一步”。
- 绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-backend-diagnostic-v1`。
- 状态：**最小诊断执行完成、独立证据验证通过；llguidance冲突实测确认，X公开导入仍失败、语义gate仍false。** 未改规则／时限重跑。
- 来源：现有llguidance1.7.6／XGrammar0.2.8工程诊断，不是模型、45实例语义或服务干扰实验。

## 可复现条件

- [禁用诊断草案](../../configs/legacy-backend-diagnostic-draft-v1.json)与旧失败工件不改；另用[执行登记](../../configs/backend-diagnostic-execution-v1.json)绑定源码、原runtime101和原257词表参数。旧环境不升级，LLVM／编译器不新增。
- LL公开调用520：import、Python wrapper与LLTokenizer各1、257个单id decode、全0..255 decode1、257个special判定及2个固定编码probe；保留实际返回类型、raw hex、归一化后的bytes、异常和直接比较结果，不静默修复。
- X在同一组合总5秒内记录Torch导入、线程设置、XGrammar导入的begin/end；标准库faulthandler每1秒保存栈，checkpoint不重置deadline。目标10ms外部轮询及实际检测时刻归档，超时记删失而非成功。
- 先LL后X，最多1个工作进程、2CPU；总<=30秒、LL<=10秒／单调用5秒；0schema/matcher/mask/45标签/模型，写入仅run内，CUDA不可见、网络／子进程编译拒绝、TVM可选DLPack JIT关闭。
- 最多64文件8MiB／stack512KiB；独立validator PID与进程starttime归档，guard拒绝立即写事件以免kill后丢失。新登记SHA `8b33bb50118fed584abb870ac2a924f29a0e280c0151d6a04c65a4ebfef1afd0`，四文件同步、AST、5 source/input pin、101 runtime pin、旧索引及新run不存在全部核对后，只执行一次。
- 实际命令（已执行，勿原路径重跑）：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -I -S -B scripts/backend_diagnostic.py --execute --registration-sha256 8b33bb50118fed584abb870ac2a924f29a0e280c0151d6a04c65a4ebfef1afd0
```

- launcher2222361／3.941186秒／exit0；LL worker2222364 exit0；X worker2222365 exit1；validator2222367 exit0。四PID收尾核不存在。overall complete指诊断证据完整，不是两个后端都导入通过。

## 结果与证据

### llguidance：源码预测已由实际数据核验

- 520公开调用完整归档；257个单id解码全部返回`builtins.bytes`，无decode异常。byte差异**仅id255**：输入FF，实际为空。id0..254与EOS256的内容保持预期。
- `is_special_token`实际为true的id只有255和256；原special_ids参数仍只指定[256]。全0..255输入256bytes实际解码255bytes，首差位置255，与单id解码拼接结果一致。
- 两个固定编码probe（`test`4bytes、0..127共128bytes）返回token按原映射都可还原原始输入。未运行FF编码的额外probe，不能推定其他路径的全byte可逆性。
- 每个实际返回类型／hex／special值／异常都即时写入事件并另保存`llguidance-byte-evidence.json`。独立validator重算所有差异、拼接、调用配对与事件对应，不导入LL库或runner。原全byte恒等gate未通过，不能删FF、换词表或跳检查救回。

### XGrammar：本次失败发生在Torch导入期的保护边界

唯一检查点是`torch_import_begin`，没有`torch_import_end`，还没到线程设置或XGrammar导入。1秒时保存了1份栈；本次组合阶段在约1.195930秒因异常结束，没有触发5秒watchdog。

traceback路径：Torch `_C._initExtension`→`torch.cuda._utils`→cuda.bindings→cuda.pathfinder→`ctypes.util.find_library("dl")`→拟启动`/sbin/ldconfig -p`的Popen准备→`os.open(os.devnull, os.O_RDWR)`。我们把run外的O_RDWR open一律视为写入，因此拒绝了`os.devnull`（此Linux路径通常为/dev/null）。这个规则过宽，是本次明确的测试框架问题；还未触及XGrammar性能或语法能力。

guard即时事件保存file_denied=1，其他三项0；拒绝发生在Popen准备阶段，尚未到`subprocess.Popen` audit事件，不是已放行运行了ldconfig。即使单独允许/dev/null，后续“一切子进程都禁止”的规则仍可能拦住只读库发现，不能说修一处就能导入。此轮没有修改规则或第二次调用。

该路径能解释**本次**异常；旧run在组合import满5秒被kill，没有分段证据，仍不能断言其全部超时成因已解释。CUDA模块被导入也不等于初始化GPU；这次未完成Torch导入后的CUDA后验检查，不报告该后验通过。

### 归档与计数

- 原23文件629418bytes，manifest `bcebf220b0cbccd24a363e3ee69763ff8d1decc3511869730946c46372473f30`、独立verification `8aa60ac4864a96cd731c905f0f653be085127b0b8f23cde56820f1319ebb3feb`逐文件回读，cap先核再封口。原始byte数据／events／stack／traceback／process样本与失败均保留，只在服务器。
- 101运行文件及旧source/input pin事后不变，旧失败工件和索引未追改。0schema、matcher、mask、45标签或模型调用，无安装／升级／新服务；仅原合成tokenizer与编码probe，不加载模型分词器。
- 新增1诊断CPUrun，累计135runs／3038历史主回答；新索引 `results/20261101-run-index-backend-diagnostic.json` SHA `b0c41c246d50ad046273d6e1d34a66559771d1e8e76d7065715b1ca7364f9bb1`。旧134run索引保持。

## 解释与下一步

当前获得的是FF冲突的实测确认和Torch导入保护误拦定位，没有45标签语义或服务干扰结论，不判N1科学go/no-go。下一条先审计并修正/dev/null与确切只读动态库查询的准入实现，只按字面命令／参数／输出／超时约束允许，不对任意子进程放行；需要新版本源码和独立软件验收，再另登记真实CPU导入检查。不能原地改旧guard/source/run或提高组合5秒。

原257词表的byte255已证实与LL入口契约冲突；未来共同合法UTF-8／ASCII域适配必须另写新契约和覆盖边界，不自动把旧gate改true。原45标签保持未执行，原12observer通过和旧KV停止队列保持。STATUS/WORKLOG/HANDOFF/readiness更新同步，环境不变，无自有后台任务、GitHub未配置未push。

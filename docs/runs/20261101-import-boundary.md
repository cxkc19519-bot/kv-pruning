# 精确导入边界软件验收与独立CPU导入

## 实验身份

- 日期／时区：2026-11-01，Asia/Singapore；用户本实验会话“开始下一步”。
- 软件run绝对路径：`/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-import-boundary-software-v1`。
- 状态：**精确边界v1软件20项通过；真实v1发现dill新设备写法。源码审查后独立v2软件23项通过；真实v2不再观测到拒绝，但组合总5秒导入gate仍未通过。** 四run分别登记、各执行一次，旧工件全部保留。
- 来源：修正测试框架错误边界；软件阶段仅标准库与1次固定只读ldconfig查询，不import作者后端。后续真实阶段必须先通过软件验收并另登记。

## 可复现条件

- [软件登记](../../configs/import-boundary-software-v1.json)绑定五份源码与runtime101、设备和命令pin。原run／source／失败记录不变，无依赖升级。
- 实际ctypes源码固定35e5eda9…，调用字面`['/sbin/ldconfig','-p']`，stdin/stderr DEVNULL、stdout PIPE、env仅LC_ALL/LANG=C。程序resolved `/usr/sbin/ldconfig`、sha bfd5df90…、设备和inode先固定；/dev/null为字符设备，dev/ino/rdev先固定。
- 新模块按原路径／flags和设备身份允许sink；命令封装只支持已审Popen context/read/poll/wait界面，执行一次后返回捕获内容。stdout<=256KiB、stderr<=64KiB、执行1秒／清理最多1秒、最多4查询；PID/starttime校验，派生进程保留worker进程组以供外部总时限清理。
- 20项软件合同包含设备、危险flags、目录边界、参数／alias／shell／env／stdio／cwd／二进制不符、查询次数、pipe超量／timeout、一次真实查询和原Popen绕过拒绝。不重新运行12项旧observer。
- 保护是Python导入边界，不是OS级安全沙箱；native代码可信，不宣称阻止任意恶意native系统调用。固定查询只读，不运行ldconfig更新缓存、编译器或安装命令。
- 总30秒，每run归档64文件8MiB；先软件后native，保持真实组合总5秒不分段重置；0词表改变/schema/mask/45标签/模型。
- v2只新增固定字符sink的精确`O_WRONLY|O_CREAT|O_TRUNC`组合，用于dill的builtin/_pyio `wb`探测；设备路径和dev/ino/rdev仍逐次匹配，不允许普通文件、任意O_CREAT、APPEND或命令变体。原v1源码、登记和测试结果不改，新源码使用_v2文件名；没有绕过v1后继续冒称其通过。

| 登记 | SHA256 | 实际运行参数 |
| --- | --- | --- |
| import-boundary-software-v1.json | 7ba5851d7ed0af88d71631baa8a2dda46b9c7bece623f8e30d5efaf9083b6ffc | mode=software，20项，native关闭 |
| import-boundary-native-v1.json | 445816fa996f5950b95ab6b16cfe4ed61f1c8cff95fe6b17c139eaac8fcf3f1d | 绑定上条20项实际证明后登记 |
| import-boundary-software-v2.json | 7e412a887d41f529e13e3582a48e3ea06385f8f53471e0f06cf262a54da41457 | 独立v2源码，20旧合同+3设备writer回归 |
| import-boundary-native-v2.json | 255482dba92c9de0a6cefae65b6466762deafd54e02758d509c16dc3fea98c17 | 绑定23项实际证明后登记，总5秒不改 |

实际命令形式：

```bash
cd '/home/user/jhk/project/Directional Exploration/kv-pruning'
.venv/bin/python -I -S -B scripts/guarded_import_runner.py --execute --registration configs/import-boundary-software-v1.json --registration-sha256 7ba5851d7ed0af88d71631baa8a2dda46b9c7bece623f8e30d5efaf9083b6ffc
.venv/bin/python -I -S -B scripts/guarded_import_runner.py --execute --registration configs/import-boundary-native-v1.json --registration-sha256 445816fa996f5950b95ab6b16cfe4ed61f1c8cff95fe6b17c139eaac8fcf3f1d
.venv/bin/python -I -S -B scripts/guarded_import_runner_v2.py --execute --registration configs/import-boundary-software-v2.json --registration-sha256 7e412a887d41f529e13e3582a48e3ea06385f8f53471e0f06cf262a54da41457
.venv/bin/python -I -S -B scripts/guarded_import_runner_v2.py --execute --registration configs/import-boundary-native-v2.json --registration-sha256 255482dba92c9de0a6cefae65b6466762deafd54e02758d509c16dc3fea98c17
```

四条都已执行，各新目录先核不存在／AST／source-input/runtime pin，不原路径重跑。v1/v2真实登记均由各自软件通过后才创建，不预先排入真实队列。

## 结果与证据

| 实际run后缀 | launcher/worker/verifier PID；查询PID | 结果与内部总墙钟 | 归档文件/bytes／manifest |
| --- | --- | --- | --- |
| software-v1 | 2228817/2228820/2228822；2228821 | 20项通过，0.227480秒 | 23/167673，768823290945adf6bf857a126b43a4605e6ecf6c29f2a4c31b007e27dfb796d8 |
| native-v1 | 2229348/2229351/2229354；2229353 | worker exit1，1.718853秒，导入gate false | 26/230357，b63da80d0ea242d7be52cd2a009d72684dd3ee5a046ec960c33310155347a1b7 |
| software-v2 | 2230540/2230564/2230566；2230565 | 23项通过，0.227848秒 | 24/170528，d9dd9838a5d39da937f39cf41540037b9aa1afc83eca5c52b390d26126f7ec82 |
| native-v2 | 2230938/2230941/2231001；2230943 | worker -9、5秒删失，5.225541秒，导入gate false | 25/356039，a157377160cc84a8ea86455436c02b8e9d77e6236814bdc38166a28e064e918a |

四个launcher和独立validator均exit0；两native的complete仅表示诊断／归档完整，**不是导入通过**。16个自有PID事后全核不存在。所有原manifest／独立验证逐hash回读，无cap错误；98文件是四个独立run的合计，不是单个run突破64文件。

### 软件验收

v1固定20项均通过，含一次真实只读查询及原Popen绕过拒绝。输出103903bytes、stderr0、实际查询约0.003041秒，process_denied=1是故意拒绝fixture，其余禁止项0。

真实v1中，ldconfig查询已经成功。随后Torch→dill `_dill.py:163–182`用builtin和_pyio `open(os.devnull,'wb')`探测文件类型，flags包含CREATE/TRUNC，被v1拒绝；完整异常保留。只读源码新增固定dill/_dill.py和torch/utils/_import_utils.py两个hash后，v2补入该精确字符设备组合与3个回归（模式判断、纯Python写法判断、两实现实际写入sink）。23项通过，仍保留所有原负对照，真实查询约0.003123秒。不是重复43个独立科学样本。

### 真实v2：误拦消除，但冷启动没有在5秒内完成

即时日志中没有boundary_denied，1次固定查询0.003343秒完成，输出仍103903bytes且hash与软件run一致。Torch导入3.081376秒，线程设置0.009988秒，约3.091707秒进入XGrammar。总时钟没有重置；外部watchdog在5.000741秒检测并kill，0.000741秒是轮询检测延迟，不是改门槛。

4份周期栈保留了导入进度，末份在XGrammar→Transformers.utils.import_utils→importlib.metadata.packages_distributions路径读取分发元数据。它说明当时的位置，不能完整归因全部耗时、证明死锁或评价语法编译速度。XGrammar import_end未出现，CUDA后验也未执行；native准入和旧语义gate仍false。

### 计数与来源

新增4个CPU工程run（2软件通过、2真实导入未通过），135→139runs，历史主回答3038不变。0schema/matcher/mask/45标签/模型调用，模型tokenizer不加载。新索引`results/20261101-run-index-import-boundary.json` SHA `e189878ff02ea4ddd51c5f9dba7fb80d5fadbcf3076ee00526513494dceb6ebd`；旧索引保留。runtime101与dill新增2源、原登记/source均事后核对不变。

来源仅服务器`literature/20261101-loader-boundary-source-v1`，7文件109990bytes，manifest `474729a4a42c9ba686b0de69c52d18abc3c3fb9ce109930c11105d1f16b793ec`。固定命令只读输出、设备和源码快照均留服务器，无系统缓存更新／包安装／驱动变更。

## 解释与下一步

本轮完成了精确导入边界修正及其验收，仍未取得原组合5秒冷启动准入。停止当前执行队列，不增加时限、换输入、热身后冒称旧gate通过。原LL的FF契约冲突仍保持、未重做差值，45标签未启动。

下一步先离线核清**一次性服务启动与每请求语法工作的预算边界**：当前5秒测量包含Torch、设备后端发现和Transformers元数据扫描，不能把它解释为单次语法编译时限。若为后续研究另建初始化／请求分阶段执行契约，需独立预先固定启动总资源上限和单调用时限、明确这是新执行范围，旧冷启动gate仍false；不能用调整范围救回旧结果或据其判N1 go/no-go。共同合法UTF8域适配也须新契约，未实现前不运行45标签。

STATUS/WORKLOG/HANDOFF/readiness已据实更新同步，原始仅服务器、GitHub未配置未push，无自有后台任务。N1未定题，原12observer和旧停止队列保持。

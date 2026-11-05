# 导入崩溃定位与独立完整启动检查

## 实验身份

2026-11-01，Asia/Singapore；授权服务器，用户专用实验会话“开始下一步”。自建工程诊断。服务器绝对目录：

- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-startup-fault-probe-v1`：GDB封装失败，未执行Torch。
- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-startup-fault-probe-v2`：两种设置均完成Torch，原validator因身份字段判读错误失败。
- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-startup-fault-reanalysis-v1`：封存v2的离线独立重判通过，无新后端执行。
- `/home/user/jhk/project/Directional Exploration/kv-pruning/results/20261101-startup-import-only-v2`：另登记的完整Torch/XGrammar import-only启动通过。

旧SIGSEGV未复现、根因未定；不将本轮成功写成旧问题已修复或科学方向已可行。

## 可复现条件

[诊断v1](../../configs/startup-fault-probe-v1.json)登记SHA256 `821f9335645fb8f724e70004795db17ea7e82f98f801aeea74d9ccd11a774b1c`；[诊断v2](../../configs/startup-fault-probe-v2.json)为 `9da33c9e01dccc594e857c3f63bd4f7011c773d8e3c9457689685419eb703880`。两版均冻结源码/输入后单次运行，旧版不改。每种设置各一个fresh进程，顺序periodic→fatal_only，同GDB/显式环境/CPU亲和性，均enable fatal handler，前者每秒周期抓栈。每case从父spawn计30秒、总75秒；v2增加先行≤5秒标准库启动/退出检查，不通过就不执行Torch。每个子进程单文件硬上限512KiB、core limit0，各归档64文件8MiB。GDB截获信号，输出当前和各线程原生栈后退出，不加载自定义脚本、不联网下载符号。仅Torch导入、线程设置、CUDA未初始化检查，无XGrammar/模型/词表或编译器调用。

[离线重判登记](../../configs/startup-fault-reanalysis-v1.json)为 `f4fcd41ea4cb71909218822493f4c16b3896580c76497c016e0d5e8c84a0b2c4`，只读封存输入，另存衍生结果，未覆盖原validator或重跑native。查询事件的pid/starttime是query主体，worker身份通过bootstrap及同native TID/外部PID记录核对；其他事件仍严格核worker身份。

完整启动另用[import-only v2](../../configs/startup-import-only-v2.json)，登记 `0a2e1d1ea4f07d80d8291e7c42518597f80981330071d0d86aca6389bfa5d4b4`。控制器、独立validator、ImportBoundary v2、运行库和30秒parent-spawn/45秒总上限不变；新phase_runner_fatal只将周期抓栈改为显式fatal抓栈，无GDB。不以Torch-only诊断代替完整启动，不构造vocab/compiler或schema/matcher/mask。该新观测政策不是旧崩溃根因已证实的修复。

固定Python3.11.13、GDB12.1、Torch2.13.0、XGrammar0.2.8；101运行文件+dill2和GDB/Python二进制pin在事前/事后均核对不变。GDB v2使用与venv符号链接相同的已pin真实Python可执行文件和相对worker路径；完整启动仍沿原venv入口。无Git提交/remote，无依赖安装、模型/模型tokenizer/权重、GPU查询或服务启动。

## 来源审查

旧两次的显式环境相同，同ImportBoundary v2与1秒周期抓栈，均未显式enable fatal handler；完整ambient继承环境未归档，不能称全部条件已证明相同。[Python接口文档](https://docs.python.org/3.11/library/faulthandler.html)区分fatal与timer；[3.11相关报告](https://github.com/python/cpython/issues/116008)和[main/3.16报告](https://github.com/python/cpython/issues/158200)只支持诊断假设，后者不直接证明本机3.11.13受同一缺陷影响。固定v3.11.13源码显示独立watchdog线程读取帧；旧“File”截断本身不能定位原生故障。

source-v1归档15文件59086bytes/manifest `a90734e22a784461add62f85d56da6f97a9964c63543897373c99f08b4bdfb2d`；3个raw URL读取超时完整保留。随后经官方API取得faulthandler.c、traceback.c及接口rst，均核Git blob；api-v1为5文件91377bytes/manifest `48e5a0aa849fae2e673a4c6eec38987de94d4cc2376c7ba94662994e784564fe`。上游tag不证明Conda二进制构建完全等价。未发现当前UID的候选Apport Python报告，未读他人报告。原始仅服务器。

## 实际执行命令

服务器项目根目录内执行，各登记/输出目录仅一次；以下是记录，不是自动重跑许可：

```sh
.venv/bin/python -I -S -B scripts/startup_fault_probe.py --execute --registration configs/startup-fault-probe-v1.json --sha256 821f9335645fb8f724e70004795db17ea7e82f98f801aeea74d9ccd11a774b1c
.venv/bin/python -I -S -B scripts/startup_fault_probe_v2.py --execute --registration configs/startup-fault-probe-v2.json --sha256 9da33c9e01dccc594e857c3f63bd4f7011c773d8e3c9457689685419eb703880
.venv/bin/python -I -S -B scripts/verify_startup_fault_probe_v3.py configs/startup-fault-reanalysis-v1.json f4fcd41ea4cb71909218822493f4c16b3896580c76497c016e0d5e8c84a0b2c4
.venv/bin/python -I -S -B scripts/phase_runner_fatal.py --execute --registration configs/startup-import-only-v2.json --registration-sha256 0a2e1d1ea4f07d80d8291e7c42518597f80981330071d0d86aca6389bfa5d4b4
```

## 结果与失败

| 阶段 | 实际结果 | 归档/墙钟 |
| --- | --- | --- |
| 诊断v1 | GDB对带空格路径错误转义，条件块未正确结束；inferior exit2，两个case各到30秒被清理，未运行Torch；validator1/launcher1 | 27文件436693bytes，60.232059秒 |
| 诊断v2 | 启动检查及两个Torch worker均正常退出/CUDA false，无SIGSEGV；原validator把query PID误当worker PID而exit1，原launcher failed保留 | 51文件458046bytes，18.359563秒 |
| 离线v3 | 从原事件/外部PID/查询记录独立重判通过，不新增native运行，不回改原v2状态 | 4文件12012bytes |
| 完整import-only v2 | Torch/XGrammar均导入完成，CUDA false；worker/validator/launcher均exit0 | 29文件480728bytes，8.450735秒 |

GDB单对未复现SIGSEGV，不能证明周期抓栈必然引发或不会引发旧崩溃；GDB改变调度且本轮不是原完整worker重放。原生诊断不做吞吐/时延比较。

完整启动从父spawn到library_import_ready为 **7.802948144秒**，独立账本一致；其中Torch导入1.798138994秒、线程设置0.000070113秒、XGrammar导入5.910754443秒。launcher含预检/复核等8.450735232秒。均为单次工程观测，不是稳定性能或SLO保证；fresh进程未清系统文件cache，也没有schema预热。

完整worker最终guard：file/process/forbidden_import/network拒绝均0，精确devnull10次、只读query1次。三个实际native worker各query一次，均stdout103903bytes/stderr0，SHA256 `1a3b04fe196649d01c9bd1c03e8cc09fbf8152a638a590c58d989f781fb8dd03`。无schema、词表factory、compiler、matcher、mask、45标签或模型调用。

完整阶段只观察library_import_ready；没有factory/request准入。worker关闭后state terminal、live_ready=false，不能跨PID继承就绪。旧cold5/FF身份/有限语义gate保持false。

## 归档与进程收尾

- 诊断v1 manifest `6eec7ae9fb76daf0d00e0325a1756d979839f759ac06e169485eb3829043a8d4`。
- 诊断v2 manifest `8c9dd429f0ddd3a6e1adb5a0cfd166daf927cd702cbc3936451f4d425dacd28f`。
- 离线v3 manifest `1da0522c49d1c790b405eeaa593947ec789868ff9c910f1efcb72d0b2efa3e42`。
- 完整启动manifest `1e34f15b621970af7818c9daef88932bf75fc2850559d59753076c4d60092b38`；独立verification `5440061a0b62efb0465cb22210a8d9d74604de1f37289066c76253c679978def`。
- 所有归档逐文件回读，source/input/runtime不变；全部23个登记/外部观测/query自有PID核不存在，清单和PID/starttime见原process-record及closure。完整launcher2258945/worker2258948/verifier2259000/query2258969，starttime428360073/428360082/428360917/428360151。
- 服务器补充closure `results/20261101-startup-fault-closure.json` SHA256 `83ba166ea3d5e232bd8de9b8b8281f98cc53aee252ea658912c266f363807ab3`；新索引 `results/20261101-run-index-startup-fault.json` SHA256 `35780f6e54139469170492355ea0fc57fe6d4d0ba14075fe0d9e2595f46ca013`。
- 新增3CPUrun，原始状态2failed/1complete；另1离线重判不是新增实验run。累计144runs3038历史主回答，新增回答0。旧失败/结果/索引不变，无后台/服务/队列或安装。

## 解释与下一步

现在有新范围下的一次完整库导入证明，解决了“连库尚未导入完成便误计编译成本”的前置障碍；仍没有词表适配、compiler factory、正确语义或资源回收效果证明。旧SIGSEGV根因未知，N1科学可行性/新颖性尚未建立，H3停止/泛KV暂停保持。

下一步先冻结两后端共同合法UTF8输入/输出域、special-token与EOS含义，以及同进程factory构造正确性协议；原257byte的FF冲突作为旧失败保留，不能删FF后声称旧gate通过。先做适配正确性小检查，再决定是否执行原8schema45标签。禁止直接用本次library-ready跳到性能/取消/45标签，也不重做8/23/12或反复追逐非复现崩溃。

已更新STATUS/WORKLOG/HANDOFF/PLAN/README与readiness，代码配置文档同步服务器；原始工件仅服务器，GitHub未配置未push。

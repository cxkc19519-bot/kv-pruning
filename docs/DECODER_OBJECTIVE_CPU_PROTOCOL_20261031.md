# H3局部目标CPU正确性协议

日期2026-10-31。用户本会话已授权实验，本次“开始下一步”实施[筛查草案](DECODER_OBJECTIVE_SCREEN_DRAFT_20261031.md)的CPU前置检查。只运行合成软件用例，不运行12组模型诊断。旧禁用草案不追改为已执行；以新的execution登记及外部SHA命令为实际CPU许可。

## 范围与固定用例

新模块`decoder_objective.py`实现：局部support的稳定log-softmax/KL、只按Full选择的Top-K、完整并列argmax列表、有限UTF-8输出在不可变byte词表上的所有合法路径，以及固定sink4/recent64计费的8个候选index plan。这里是有限byte语法，不是HF tokenizer适配器/通用JSON引擎；实际tokenizer的上下文相关解码、special tokens与native边界仍须另验。索引plan也不能充当真实GPU物理gather证据。

18组固定用例：C01三token概率反例的两候选；C02全词表mask；C03单合法token；C04全局概率下溢但局部概率可分；C05大共同logit偏移；C06 Q硬零导致无限KL（JSON用status=infinite/kl=null，不当0）；C07 P硬零的有限KL；C08词表300的128/256、Full边界并列按ID及合法集合落在Top-K之外；C09十种非法KL输入。G01有限JSON枚举全部可达路径；G02拆分UTF-8字节；G03跨JSON边界token；G04八种语法/词表/路径拒绝。M01八等预算候选；M02分数并列与重放；M03预算恰容锚点、八候选可完全相同；M04锚点容量不足保留infeasible；M05五种预算/seed/layout坏输入。

所有构造值和实际返回归档，拒绝变异23次。软件seed固定3101–3106，仅用于CPU用例；12组模型草案的实际seed仍未选定。合成layout=[28,4,128,2]预测57344 bytes/槽；未读取模型配置、未测量物理bytes或VRAM。无新任务样本、风险统计或独立科学效应估计。

独立validator不导入模块或fixture runner，对序列化输入用80位Decimal重算概率/KL/合法质量，对有限字节前缀集合穷举全部可达边与EOS，复核所有候选索引/锚点/预算/seed及23项错误，并检查反例、全词表、单token、下溢与重复mask对照。随机索引重放使用相同Python标准库Random，不宣称独立实现了随机数发生器。只对登记的用例给出软件正确性结论。

## 执行与边界

唯一新run为服务器`results/20261031-decoder-objective-cpu-v1`。四脚本、此协议、上一轮禁用草案配置的SHA须在运行前固定；源码先同步核验，结果和日志仅服务器。本地不运行fixtures或Python实验。登记`configs/decoder-objective-cpu-execution-v1.json`仅启用CPU，不修改旧草案execution=false；启动命令须传登记自身SHA。原48题/旧16/已有生成输出不读取、不改分。

既有`.venv/bin/python -B scripts/run_decoder_objective_cpu.py --execute --registration-sha256 <冻结SHA>`同步运行；不启动服务或后台任务。worker与独立validator分别30秒墙钟alarm，launcher总90秒、超时只TERM自己创建的进程组，5秒后KILL；档案最多32文件/4MiB。二子进程内审计hook拒绝模型/tokenizer导入、所有socket、子进程、模型/权重读取和run外写入，所有guard计数必须0。launcher创建这两个受限子进程是登记步骤。无安装/下载/模型forward/GPU查询。

若失败保留全部日志、状态与manifest，不覆盖同名run；修改必须新版本登记。服务器若不可达，明确记录未执行，不把静态审查当通过。

## 下一步

CPU通过后只表示这个有限byte词表和数值实现过上述用例。还需冻结新12开发组输入、真实tokenizer-byte适配、同前缀工程检查、实际KV gather/bytes、query+wrapper重算和forward/token/时间上限，才能执行真实logit诊断。该GPU入口本次不实现/不启用。H3的真实失配、新颖性和实际收益仍未知。

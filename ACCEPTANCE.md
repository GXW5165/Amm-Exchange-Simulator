# AMM Exchange Simulator 验收说明

本文档记录本次全面排查后的项目状态、补充内容、运行方式和测试结果，便于课程验收、演示和后续报告撰写时引用。

## 1. 对照课程基本要求

| 基本要求 | 当前实现 | 验收结论 |
| --- | --- | --- |
| 可执行、可交互、可复现的代码系统 | 提供 CLI 交互菜单、Streamlit Web 页面和非交互式配置运行入口 | 已满足 |
| 支持参数配置 | 使用 `configs/default.yaml` 配置初始储备、手续费率、用户、事件和输出路径 | 已满足 |
| 支持事件触发 | 支持 `swap`、`add_liquidity`、`remove_liquidity` 时间序列事件 | 已满足 |
| 支持结果可视化 | 输出价格、储备、滑点、手续费、无常损失、用户 PnL 图表 | 已满足 |
| 核心协议逻辑本地实现 | 恒定乘积 AMM、手续费、LP 份额和收益指标均在本地代码实现 | 已满足 |
| 支持多用户 | 用户独立维护 Token X、Token Y 余额和 LP 份额 | 已满足 |
| 支持时间序列离散事件仿真 | `EventQueue` 按 timestamp 调度，同时间事件保持入队顺序 | 已满足 |
| 支持极端场景和对比分析 | 内置大额交易冲击、手续费率对比、流动性深度对比 | 已满足 |
| 有测试覆盖 | 覆盖 AMM、流动性、仿真、导出、可视化、Web 输入和 CLI Demo | 已满足 |

## 2. 本次补充和修复内容

### 2.1 新增非交互式 Demo

新增 `main.py --config` 和 `main.py --demo` 两种非交互式运行方式，用于满足课程要求中的“一键运行 Demo”。

可直接执行：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml
```

或：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --demo
```

如需同时运行实验场景：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml --scenarios
```

无参数运行仍保持原来的交互式菜单：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py
```

### 2.2 修复配置复用状态污染

修复 `SimulationRunner.run_from_config()` 直接复用 `config.users` 的问题。此前仿真会修改用户余额和 LP 份额，如果同一个配置对象重复运行，第二次可能从已经变化后的用户状态开始。

当前实现会深拷贝用户和事件配置，保证：

- 同一配置可以重复运行；
- 对比实验从一致初始状态开始；
- Web、CLI 和测试之间不会互相污染配置对象。

### 2.3 补充测试

新增测试覆盖：

- 非交互式 `--config` Demo 可以运行并导出 CSV、JSON、PNG；
- `SimulationRunner` 不会污染传入的 `AppConfig.users`；
- 同一配置重复运行得到一致的关键摘要指标。

### 2.4 补充中文注释

已为主要源码补充中文说明，覆盖：

- 领域对象：资金池、用户、LP 仓位、异常；
- AMM 核心：报价、兑换、手续费、LP 份额铸造/销毁；
- 仿真层：事件、事件队列、事件调度、事件记录；
- 分析层：滑点、无常损失、用户 PnL、摘要报告；
- 应用层：配置加载、输入校验、场景构造、仿真运行器；
- 基础设施：CSV/JSON 导出、日志；
- 可视化和 Web 支撑函数；
- CLI 交互模式与非交互式 Demo 入口。

## 3. 当前稳定功能清单

当前项目稳定支持以下功能：

- 恒定乘积 AMM 双向兑换：`x_to_y` 和 `y_to_x`；
- 手续费扣除和池内沉淀；
- 理论价格、成交价格、滑点百分比记录；
- LP 添加流动性；
- LP 移除流动性；
- 用户钱包余额和 LP 份额更新；
- 多用户仿真；
- 按时间戳执行事件序列；
- 事件级 CSV 日志导出；
- 仿真摘要 JSON 导出；
- 价格、储备、滑点、手续费、无常损失、用户收益图表；
- CLI 交互式操作；
- CLI 非交互式一键 Demo；
- Streamlit Web 参数编辑、事件编辑、运行和下载；
- 大额交易冲击、手续费率对比、流动性深度对比实验。

## 4. 验证结果

完整测试命令：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest -q
```

本次验证结果：

```text
18 passed, 14 warnings
```

其中 warnings 来自 matplotlib/pyparsing 依赖内部的弃用提示，不影响项目功能。

非交互式 Demo 验证命令：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml
```

本次运行成功生成：

- `data/output/logs/simulation.csv`
- `data/output/results/summary.json`
- `data/output/results/pool_spot_price.png`
- `data/output/results/pool_reserves.png`
- `data/output/results/swap_slippage.png`
- `data/output/results/cumulative_fees.png`
- `data/output/results/impermanent_loss.png`
- `data/output/results/user_total_pnl.png`

## 5. 仍需在报告材料中说明的边界

当前项目是 AMM 交易所仿真 MVP，聚焦单交易对、单资金池和恒定乘积模型。以下能力不属于当前版本核心范围：

- 不接真实区块链节点；
- 不处理真实资产；
- 不调用 DeFi 主网 API 作为核心逻辑；
- 不支持多池路由；
- 不支持套利机器人；
- 不支持历史价格回测；
- 不支持借贷、清算、DAO 治理等其他 DeFi 方向。

这些边界与课程要求中的“聚焦 1-2 个核心机制的 MVP”一致，可在技术报告中作为项目范围说明。

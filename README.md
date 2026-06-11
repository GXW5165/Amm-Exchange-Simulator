# AMM Exchange Simulator

> 本地离线的恒定乘积 AMM 仿真系统，用于 DeFi 机制学习、课程项目和可复现实验分析。

AMM Exchange Simulator 模拟一个 X/Y 双资产自动做市商资金池，核心模型为 `x * y = k`。项目可以按时间顺序执行交易、添加流动性、移除流动性和套利等事件，并输出事件日志、统计摘要、图表、Excel 和 PDF 实验报告。

本项目不连接区块链节点，不接入真实钱包，也不处理真实资产。

## 功能概览

| 模块 | 说明 |
| --- | --- |
| AMM 交易 | 支持 X -> Y、Y -> X 双向 swap，按恒定乘积公式定价 |
| 套利事件 | 支持给定外部市场价格的套利检测、报价和执行 |
| 手续费 | 交易手续费沉淀在池内，影响 LP 收益和池子状态 |
| 流动性管理 | 支持添加/移除流动性，计算 LP 份额铸造和销毁 |
| 离散事件仿真 | 按 timestamp 排序执行事件，记录每一步前后状态 |
| 多用户钱包 | 每个用户有独立 Token X、Token Y 和 LP shares |
| 分析指标 | 滑点、无常损失、用户 PnL、LP 收益、池深度 |
| 历史价格回测 | 导入历史价格 CSV，根据价格波动自动生成模拟交易事件 |
| 可视化 | 输出价格、储备、滑点、手续费、PnL 等图表 |
| 报告导出 | CLI 支持 CSV、JSON、PNG 图表；Web 支持 Excel 和 PDF 下载 |
| Web 界面 | 使用 Streamlit 进行参数编辑、参数遍历、回测、结果查看和文件下载 |
| CLI | 支持一键 demo、配置文件运行、批量场景运行和交互式菜单 |

## 快速开始

推荐使用项目当前测试环境中的 Python：

```powershell
# 安装依赖
D:\miniconda3\envs\jrrg\python.exe -m pip install -r requirements.txt

# 一键运行默认 demo
D:\miniconda3\envs\jrrg\python.exe main.py --demo

# 使用默认配置并运行内置对比场景
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml --scenarios

# 运行套利演示配置
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/arbitrage_demo.yaml

# 打开交互式 CLI 菜单
D:\miniconda3\envs\jrrg\python.exe main.py

# 启动 Web 界面
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

如果你的 `python` 已经指向正确环境，也可以使用简写：

```bash
python main.py --demo
python -m streamlit run streamlit_app.py
python -m pytest -q
```

## 项目结构

```text
amm-exchange-simulator/
├── configs/
│   ├── default.yaml                  # 默认仿真配置
│   ├── arbitrage_demo.yaml           # 套利演示配置
│   └── three_trader_standard.yaml    # 三交易者标准实验配置
├── data/
│   ├── sample_price_history.csv      # 回测示例价格数据
│   ├── stable_market.csv             # 稳定市场样例
│   ├── trend_market.csv              # 趋势市场样例
│   ├── volatile_market.csv           # 高波动市场样例
│   ├── saved_configs/                # 内置样例及 Web 保存的用户配置
│   └── output/                       # 运行输出，已被 Git 忽略
├── src/
│   ├── amm/                          # AMM 交易引擎与流动性管理
│   ├── analytics/                    # 指标、摘要、PDF 报告
│   ├── application/                  # 运行编排、校验、场景、回测
│   ├── domain/                       # Pool、User、异常类型
│   ├── infrastructure/               # 配置读取与文件导出
│   ├── interface/                    # CLI
│   ├── simulator/                    # 事件、队列、仿真引擎
│   ├── visualization/                # 图表生成
│   └── web/                          # Streamlit 支撑函数
├── tests/                            # pytest 测试套件
├── main.py                           # CLI 入口
├── logo.jpg                          # Web 背景和项目标志
├── streamlit_app.py                  # Web 入口
├── requirements.txt                  # 依赖列表
└── pytest.ini                        # pytest 配置
```

## 分层架构

项目按职责分层，整体依赖方向保持清晰：界面层调用应用层，应用层编排仿真和导出，底层领域模型不依赖上层。

| 层 | 职责 |
| --- | --- |
| Domain | 核心数据模型，例如 `Pool`、`User` |
| AMM | swap 定价、套利报价/执行和流动性份额计算 |
| Simulator | 事件排序、事件执行、结果聚合 |
| Application | 配置驱动运行、输入校验、实验场景、历史回测、参数遍历 |
| Analytics | 滑点、无常损失、LP 指标、PnL、摘要、PDF 报告 |
| Infrastructure | YAML 加载、CSV/JSON/Excel 导出 |
| Interface / Web | 命令行和 Streamlit 交互 |

## 核心模型

X -> Y 交易的基本计算：

```text
k = x * y
effective_dx = dx * (1 - fee_rate)
dy = y - k / (x + effective_dx)
```

说明：

- 池子实际收到完整输入 `dx`
- 定价时使用扣除手续费后的 `effective_dx`
- 手续费留在池内，因此 `k` 可能随交易增长

滑点计算：

```text
abs(execution_price - theoretical_price) / theoretical_price * 100
```

无常损失使用标准 50/50 池公式：

```text
IL(r) = 2 * sqrt(r) / (1 + r) - 1
```

### 指标口径

- `spot_price` 的单位是 Token Y / Token X。
- `x_to_y` 的 `execution_price` 表示每 1 个 Token X 换出的 Token Y；`y_to_x` 则表示每 1 个 Token Y 换出的 Token X。
- 手续费按输入资产收取。汇总指标中的 `total_fees` 是原始手续费数量相加，`total_fees_in_y` 会统一折算为 Token Y，适合与总价值和 PnL 对比。
- `invariant_before` / `invariant_after` 记录的是 `reserve_x * reserve_y`。在含手续费模型中，手续费沉淀会让该乘积增长，因此它是池状态审计指标，不代表每一步都严格不变。
- LP 份额代表对当前资金池储备的比例索取权；已有池子添加流动性时，系统只按当前池子比例消耗双边资产，多带入的一侧不会被注入池内。

## 配置文件

默认配置位于 [configs/default.yaml](configs/default.yaml)。

当前支持四类事件：

| 事件类型 | 必填字段 |
| --- | --- |
| `swap` | `direction` (`x_to_y` 或 `y_to_x`), `amount_in` |
| `add_liquidity` | `amount_x`, `amount_y` |
| `remove_liquidity` | `lp_share` |
| `arbitrage` | `market_price`，可选 `max_amount` |

示例：

```yaml
initial_reserve_x: 1000.0
initial_reserve_y: 1000.0
fee_rate: 0.003
initial_lp_owner: protocol
log_path: data/output/logs/simulation.csv
summary_path: data/output/results/summary.json
plot_dir: data/output/results

users:
  alice:
    balance_x: 500.0
    balance_y: 500.0
    lp_shares: 0.0

events:
  - timestamp: 1
    event_type: swap
    user_id: alice
    direction: x_to_y
    amount_in: 10.0
  - timestamp: 2
    event_type: arbitrage
    user_id: alice
    market_price: 1.0
    max_amount: 50.0
```

常用可选字段：

| 字段 | 说明 |
| --- | --- |
| `log_path` | 事件 CSV 日志输出路径 |
| `summary_path` | JSON 摘要输出路径 |
| `plot_dir` | PNG 图表输出目录 |
| `initial_lp_owner` | 初始池子非空且用户 LP 份额未完全分配时，剩余初始 LP 份额的归属账户 |

## CLI 运行方式

### 一键 demo

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --demo
```

预期输出会包含：

```text
[simulation] processed_events=23
[simulation] swap_events=13
[simulation] liquidity_events=7
[simulation] arbitrage_events=3
[simulation] total_fees=4.325209
```

### 指定配置运行

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml
```

套利演示：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/arbitrage_demo.yaml
```

三交易者标准实验：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/three_trader_standard.yaml
```

该配置包含 Alice、Bob、Carol 三个交易者，覆盖方向性 swap、添加/移除流动性、外部市场套利和多用户 PnL 统计，适合用作课程展示和回归检查的标准样例。

### 运行内置对比场景

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml --scenarios
```

该命令会先运行默认配置，再运行手续费率和流动性深度等对比场景，输出到 `data/output/scenarios/`。

### 交互式菜单

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py
```

交互式菜单支持：

- 初始化资金池
- 执行 swap
- 添加流动性
- 移除流动性
- 查看池子状态
- 查看用户状态
- 导出 CSV 日志

## Web 界面操作

启动：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

浏览器打开：

```text
http://localhost:8501
```

Web 界面包含四个工作区。

### 1. Default Config

点击 `Run Default Config`，系统会读取 `configs/default.yaml` 并运行一次完整仿真。

运行后页面会展示：

- Summary 指标卡
- Event Records 事件表
- User PnL 用户收益表
- Detailed PnL Breakdown 收益拆分
- Charts 图表区
- CSV / JSON / Excel / PDF 下载按钮

### 2. Custom Simulation

用于手动编辑一组仿真参数。

可以修改：

- 初始 Token X 储备
- 初始 Token Y 储备
- 手续费率
- 初始 LP 归属账户
- 用户余额和 LP 份额
- swap / add_liquidity / remove_liquidity / arbitrage 事件

Web 页面会使用根目录下的 `logo.jpg` 作为低透明度固定背景，作为项目主题标识，不影响表格和图表阅读。

也可以保存配置，保存后的 YAML 会进入：

```text
data/saved_configs/
```

保存时配置名称会自动清洗为安全文件名；加载和删除已保存配置时也使用同一套命名规则，避免表单输入被解释成目录路径。

### 3. Backtesting

用于历史价格回测。输入是一份价格 CSV，系统会根据相邻价格变化生成模拟交易事件。

CSV 格式：

```csv
timestamp,price_y_per_x
0,1.00
1,1.02
2,0.98
3,1.05
```

你可以上传自己的 CSV，也可以直接选择内置样例：

- `sample_price_history.csv`
- `stable_market.csv`
- `trend_market.csv`
- `volatile_market.csv`

回测参数：

| 参数 | 含义 |
| --- | --- |
| Initial X Reserve | 初始 Token X 储备 |
| Initial Y Reserve | 初始 Token Y 储备 |
| Fee Rate | AMM 手续费率 |
| Volatility Threshold | 触发交易的最小相对价格变化 |

上传的 CSV 会在内存中解析，不会写入固定仓库文件，因此不同运行之间不会互相覆盖上传数据。

回测事件生成是一种教学用启发式规则：当相邻价格变化超过阈值时，系统按价格方向生成 `swap` 事件，并用 `max_trade_size` 限制交易规模。它不代表真实交易策略，也不会连接实时行情。

### 4. Parameter Sweep

用于批量运行参数组合并比较不同场景表现。当前页面与演示界面保持一致，支持一次选择一种扫参维度：

- `Enable Fee Rate Sweep`：在 `Fee Rate Values (comma-separated)` 输入最多 5 个手续费率，例如 `0.001, 0.003, 0.010`
- `Enable X Reserve Sweep`：在 `X Reserve Values (comma-separated)` 输入最多 5 个初始 X 储备，例如 `500, 1000, 2000`
- `Enable Y Reserve Sweep`：在 `Y Reserve Values (comma-separated)` 输入最多 5 个初始 Y 储备，例如 `500, 1000, 2000`
- 基于 `configs/default.yaml` 作为基础配置，并允许编辑 Initial LP Owner
- 在 `Custom Events` 表格中编辑统一应用到所有场景的事件，支持 `swap`、`add_liquidity`、`remove_liquidity` 和 `arbitrage`
- 批量输出每个场景的 CSV、JSON、图表和摘要
- 展示 comparison table、四指标多场景对比图和单个场景详情

Web 扫参默认输出目录：

```text
data/output/sweeps/web_sweep/
```

当前 Web 扫参一次最多启用一个参数维度，每个维度最多输入 5 个取值；应用层 `run_parameter_sweep` 支持参数网格组合，后续如果需要可以在 Web 页面开放多维组合。

## 输出文件

默认 CLI 输出：

```text
data/output/logs/simulation.csv
data/output/results/summary.json
data/output/results/*.png
```

Web 每次运行会生成独立目录，并在结果页提供 Excel / PDF 下载：

```text
data/output/web_runs/<run_id>/
├── simulation.csv
├── summary.json
├── simulation.xlsx
├── report.pdf
└── *.png
```

内置场景运行输出：

```text
data/output/scenarios/<scenario_name>/
```

`data/output/` 是运行产物目录，已被 Git 忽略。

## 报告格式

| 格式 | 内容 |
| --- | --- |
| CSV | 事件级执行日志 |
| JSON | 结构化摘要 |
| Excel | 多 Sheet 工作簿，包含事件、摘要、PnL、LP 指标、池深度、参数、图表 |
| PDF | 实验报告，包含封面、关键指标、分析说明、图表和事件附录 |

## 测试

运行完整测试：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest -q
```

当前预期结果：

```text
94 passed
```

测试覆盖：

- AMM 池子数学
- swap 与流动性操作
- 套利检测、执行、余额不足保护和手续费统计
- 事件调度和仿真流程
- 输入校验
- 滑点、无常损失、PnL 等分析指标
- 实验场景和参数遍历
- 图表生成
- CLI demo
- Web 支撑函数
- 历史价格回测
- PDF 报告生成

## 项目边界

- 当前模拟单个 X/Y 资金池
- 当前 AMM 曲线为恒定乘积模型
- 当前套利事件使用给定外部市场价格，不连接真实交易所或实时行情
- 当前不连接钱包、合约、交易所或实时行情
- 本项目用于教学、实验和分析，不构成任何金融建议

## 环境要求

- Python 3.10 或更新版本
- 依赖见 [requirements.txt](requirements.txt)

# 📈 AMM Exchange Simulator

> **恒定乘积自动做市商 · 离线仿真系统**

本地离线 AMM 交易所仿真系统，基于恒定乘积模型 `x · y = k`，支持多用户、离散事件调度、流动性管理、手续费分析、滑点计算、无常损失评估、LP 做市收益拆解、池深度分析、批量参数遍历和可视化图表输出。

面向 DeFi 机制学习、课程设计和量化实验分析。**不连接区块链节点，不处理真实资产。**

---

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 一键运行 Demo
python main.py --demo

# 运行 Demo + 对比实验场景
python main.py --config configs/default.yaml --scenarios

# 交互式 CLI
python main.py

# 启动 Web 界面
python -m streamlit run streamlit_app.py
```

---

## 📋 功能

| 模块 | 功能 |
|------|------|
| **AMM 交易** | 双向兑换（X→Y / Y→X），恒定乘积定价，手续费扣费与池内沉淀 |
| **流动性管理** | LP 添加/移除，首次建池自动铸造份额，后续按比例约束 |
| **滑点分析** | 理论价格 vs 成交价格，百分比滑点记录 |
| **无常损失** | 基于价格比的标准 IL 公式，支持百分比和金额形式 |
| **用户 PnL** | 按 Token Y 统一计价，钱包 + LP 仓位合并收益统计，PnL 分项拆分 |
| **LP 做市收益** | 年化收益率、手续费按份额追踪、手续费 vs 无常损失净收支 |
| **池深度分析** | 反解 AMM 公式，计算指定滑点下的最大可交易量，生成深度曲线 |
| **离散事件仿真** | 按时间戳优先队列调度，同时间保持入队顺序 |
| **多用户** | 独立钱包余额与 LP 份额，事件用户需在配置中声明 |
| **配置驱动** | YAML 文件定义池参数、用户初始状态和事件序列 |
| **CSV / JSON 导出** | 事件级日志（32 字段）和结构化摘要 |
| **Excel 导出** | 多 Sheet 工作簿（事件记录、摘要、PnL、LP 指标、池深度、参数、图表） |
| **可视化图表** | 价格走势、储备变化、滑点、累计手续费、无常损失、用户 PnL、K 线图、滑点-交易量散点图（8 张 PNG） |
| **实验场景** | 大额交易冲击、手续费率对比、流动性深度对比 |
| **批量参数遍历** | 参数网格自动生成、一键批量仿真、对比报表 CSV 和多场景对比图表 |
| **Web 界面** | Streamlit 参数编辑、事件表格、结果展示、配置保存/加载、Excel 下载 |
| **CLI 交互** | 交互式菜单 + 非交互式命令行参数 |

---

## 🏗️ 项目架构

项目采用严格的分层架构，依赖方向**自上而下单向流动**，下层完全不感知上层。

```
AMM-Exchange-Simulator/
│
├── src/                          # 核心代码目录
│   │
│   ├── domain/                   # ── 领域层 ──
│   │   ├── pool.py                 资金池状态（x·y = k）
│   │   ├── user.py                 用户钱包与 LP 份额
│   │   └── exceptions.py           异常类型
│   │
│   ├── amm/                      # ── AMM 服务层 ──
│   │   ├── engine.py               恒定乘积交易引擎（报价 + 执行）
│   │   └── liquidity_manager.py    LP 份额铸造/销毁
│   │
│   ├── simulator/                # ── 仿真层 ──
│   │   ├── engine.py               仿真控制模块（事件调度主循环）
│   │   ├── event.py                事件 / 事件类型定义
│   │   ├── event_queue.py          基于 heapq 的稳定优先队列
│   │   ├── result.py               仿真结果对象
│   │   └── scenario_builder.py     原始字典 → Event 对象转换
│   │
│   ├── application/               # ── 应用层 ──
│   │   ├── simulation_runner.py    配置驱动运行 + 导出编排
│   │   ├── validation.py           输入校验（5 个验证器）
│   │   ├── scenarios.py            实验场景构造
│   │   └── parameter_sweep.py      参数网格生成 + 批量仿真 + 对比报表
│   │
│   ├── analytics/                 # ── 分析层 ──
│   │   ├── record.py               事件记录（32 字段快照）
│   │   ├── slippage.py             滑点计算
│   │   ├── impermanent_loss.py     无常损失计算
│   │   ├── pnl.py                  用户收益计算（含拆分 PnL）
│   │   ├── lp_metrics.py           LP 年化收益 + 手续费 vs IL 拆分
│   │   ├── pool_depth.py           池深度分析（滑点→最大可交易量反解）
│   │   └── report.py               聚合摘要报告
│   │
│   ├── infrastructure/            # ── 基础设施层 ──
│   │   ├── config_loader.py        YAML → AppConfig
│   │   ├── csv_exporter.py         事件日志 → CSV
│   │   ├── summary_exporter.py     摘要 → JSON
│   │   ├── excel_exporter.py       多 Sheet Excel 导出（含图表嵌入）
│   │   └── logger.py               日志记录器
│   │
│   ├── interface/                 # ── 接口层 ──
│   │   └── cli.py                  交互式 / 非交互式 CLI
│   │
│   ├── visualization/             # ── 可视化层 ──
│   │   └── plotter.py              8 张 PNG 图表 + 多场景对比图
│   │
│   └── web/                       # ── Web 支撑层 ──
│       └── app_support.py          Streamlit 数据转换
│
├── streamlit_app.py               # Streamlit Web 入口
├── main.py                        # CLI 入口
│
├── configs/
│   └── default.yaml               # 默认配置文件
│
├── data/
│   ├── saved_configs/             # Web 保存的用户配置
│   ├── sample_price_history.csv   # 示例价格数据
│   └── output/                    # 仿真输出（日志、摘要、图表、Excel）
│
├── tests/                         # 51 个测试用例
│
├── requirements.txt               # Python 依赖
└── README.md                      # ← 你现在正在看这里
```

### 分层说明

| 层 | 职责 | 依赖方向 |
|:---|:-----|:--------|
| **Interface** | CLI + Web 用户交互 | → 调用 Application |
| **Application** | 运行编排、校验、场景、参数遍历 | → 调用 Simulator / Infrastructure |
| **Simulator** | 事件调度、流程控制 | → 调用 AMM / Analytics |
| **AMM Service** | 交易报价、流动性计算 | → 调用 Domain |
| **Domain** | 资金池、用户等核心数据模型 | — 无依赖 |
| **Analytics** | 滑点、IL、PnL、LP 指标、池深度、报告 | → 调用 Domain |
| **Infrastructure** | 配置加载、文件导出（CSV/JSON/Excel） | — 被各层调用 |

---

## 📐 核心模型

### 恒定乘积交易

```
k = x · y
dx' = dx · (1 - fee)
dy = y - k / (x + dx')
```

- 定价使用扣费后的 `dx'`，但池子实际收到全额 `dx`（手续费沉淀在池内）
- 手续费使 `k` 持续增长，LP 份额持有人按比例隐含收益
- **零费率时 `k` 严格不变**

### 滑点

```
slippage = |P_execution - P_theoretical| / P_theoretical × 100%
```

### 无常损失（50/50 双资产池）

```
IL(r) = 2·√r / (1 + r) - 1     其中 r = P_current / P_initial
```

### 池深度（滑点反解公式）

从 AMM 恒定乘积公式反解，在给定滑点容忍度 S% 下计算最大可交易量：

```
S = 1 - R·(1-f) / (R + amount_in·(1-f))
=> amount_in = R · (S - f) / ((1-f) · (1-S))
```

当 S ≤ f（目标滑点不超过手续费率）时，返回 0（即无法以 ≤S% 的滑点交易）。

### LP 年化收益率

```
APY = ((final_lp_value / initial_lp_value) ^ (365 / time_span_days) - 1) × 100%
```

---

## ⚙️ 配置文件

默认配置位于 `configs/default.yaml`：

```yaml
initial_reserve_x: 1000.0    # 初始 Token X 储备
initial_reserve_y: 1000.0    # 初始 Token Y 储备
fee_rate: 0.003              # 手续费率 (0 ≤ fee < 1)
initial_lp_owner: protocol   # 未分配 LP 份额的归属账户

users:                       # 用户初始余额与 LP 份额
  alice:
    balance_x: 500.0
    balance_y: 500.0
    lp_shares: 0.0
  bob:
    balance_x: 300.0
    balance_y: 300.0
    lp_shares: 0.0

events:                      # 按时序执行的事件
  - timestamp: 1
    event_type: swap
    user_id: alice
    direction: x_to_y
    amount_in: 10.0
  - timestamp: 2
    event_type: add_liquidity
    user_id: bob
    amount_x: 20.0
    amount_y: 20.0
```

### 事件类型

| 类型 | 必填字段 |
|------|---------|
| `swap` | `direction` (x_to_y / y_to_x), `amount_in` (> 0) |
| `add_liquidity` | `amount_x` (> 0), `amount_y` (> 0) |
| `remove_liquidity` | `lp_share` (> 0) |

可通过 **Web 界面** 交互式编辑参数并保存为新 YAML 文件，也可直接编写 YAML 后通过 CLI 加载。

---

## 📂 输出文件

默认仿真输出至 `data/output/`：

```
data/output/
├── logs/
│   └── simulation.csv             # 事件级日志（32 字段）
└── results/
    ├── summary.json               # 结构化摘要（含 LP 收益、池深度、PnL 拆分）
    ├── pool_spot_price.png        # 现货价格走势
    ├── pool_reserves.png          # 双边储备变化
    ├── swap_slippage.png          # 交易滑点
    ├── cumulative_fees.png        # 累计手续费（Y 计价）
    ├── impermanent_loss.png       # 无常损失百分比
    ├── user_total_pnl.png         # 用户总收益柱状图
    ├── candlestick.png            # K 线图（OHLC 蜡烛图）
    ├── slippage_volume.png        # 滑点-交易量散点图
    └── simulation.xlsx            # Excel 多 Sheet 报告（Web 界面下载）
```

实验场景输出至 `data/output/scenarios/<name>/`，Web 运行输出至 `data/output/web_runs/<run_id>/`，批量参数遍历输出至 `data/output/sweeps/<scenario_name>/`。

---

## 🧪 测试指南

### 方式一：CLI 命令行测试

提供三种命令行模式：**非交互式一键运行**、**交互式菜单**、**配置文件驱动**。

---

**测试 ①：交互式菜单**

```bash
python main.py
```

进入彩色菜单界面后，依次操作：

| # | 操作 | 预期结果 |
|:-:|:----|:---------|
| 1 | 看到主菜单，显示 0-9 号选项 | 菜单标题 "AMM Exchange Simulator"，含 Simulation / Manual Operations / Inspect / Export / System 五组 |
| 2 | 输入 **3**（Initialize pool），依次输入 `reserve_x=1000`、`reserve_y=1000`、`fee_rate=0.003` | 显示 `✓ Pool initialized` |
| 3 | 输入 **7**（View pool status） | 打印 Reserve X=1000、Reserve Y=1000、Fee Rate=0.003、Spot Price=1.0 |
| 4 | 输入 **4**（Execute a swap），输入 `User ID=alice`、`Direction=x_to_y`、`Amount In=10` | 显示 `✓ Swap executed. Spot price: 1.010... Y/X` |
| 5 | 输入 **4**（再执行一次 swap），输入 `User ID=alice`、`Direction=x_to_y`、`Amount In=50` | 显示新的 spot price，价格因滑点进一步升高 |
| 6 | 输入 **5**（Add liquidity），输入 `User ID=bob`、`Amount X=20`、`Amount Y=20` | 显示 `✓ Liquidity added` |
| 7 | 输入 **7**（View pool status） | LP Total Shares 增加 |
| 8 | 输入 **8**（View user status） | 列出 alice 和 bob 的钱包余额和 LP 份额，alice 的 Token X 减少、Token Y 增加 |
| 9 | 输入 **9**（Export records to CSV） | 显示 `✓ Records exported to .../interactive/simulation.csv` |
| 10 | 输入 **0** 退出 | 提示 `You have 3 unsaved event record(s)`, 输入 y 再确认导出，然后显示 `Goodbye.` |

---

**测试 ②：一键 Demo 运行（非交互式）**

```bash
python main.py --demo
```

**预期输出**（关键行）：
```
[simulation] processed_events=9
[simulation] swap_events=7
[simulation] liquidity_events=2
[simulation] total_fees=0.900000
[simulation] total_fees_in_y=0.921463
[simulation] average_slippage_pct=4.338007
[simulation] max_slippage_pct=9.517502
[simulation] impermanent_loss_pct=-0.059822
```

**预期产物**：以下文件全部自动生成

| 文件 | 说明 |
|:-----|:-----|
| `data/output/logs/simulation.csv` | 事件日志，32 列，9 行 |
| `data/output/results/summary.json` | 结构化摘要，含新增字段 |
| `data/output/results/pool_spot_price.png` | 现货价格走势 |
| `data/output/results/pool_reserves.png` | 双边储备变化 |
| `data/output/results/swap_slippage.png` | 交易滑点（有 7 个点） |
| `data/output/results/cumulative_fees.png` | 累计手续费 |
| `data/output/results/impermanent_loss.png` | 无常损失曲线 |
| `data/output/results/user_total_pnl.png` | 用户收益柱状图 |
| `data/output/results/candlestick.png` | ✅ **K 线图（≥2 swap 时生成）** |
| `data/output/results/slippage_volume.png` | ✅ **滑点-交易量散点图** |

---

**测试 ③：自定义配置文件运行**

```bash
# 使用默认配置运行
python main.py --config configs/default.yaml

# 运行对比实验场景（手续费率对比 + 流动性深度对比）
python main.py --config configs/default.yaml --scenarios
```

**预期输出**：一键 Demo 全部输出 + 额外场景目录 `data/output/scenarios/` 下生成每个场景独立 CSV/JSON/PNG。

---

### 方式二：Python API 直接调用测试

下方三段代码可直接复制到终端运行（`python -c "..."` 或存为 `.py` 文件），**无需额外编写测试程序**。

---

**测试 ④：检查新分析指标（池深度 + LP 收益 + PnL 拆分）**

```python
from pathlib import Path
from src.infrastructure.config_loader import load_config
from src.application.simulation_runner import SimulationRunner

ROOT = Path('.')
config = load_config(ROOT / 'configs' / 'default.yaml')
runner = SimulationRunner(ROOT)
artifacts = runner.run_from_config(config)
s = artifacts.result.summary

print(f"Pool Depth @2%: {s.pool_depth_at_2pct:.4f}")
print(f"Time Span (days): {s.time_span_days:.4f}")
print(f"LP APYs: {s.lp_annualized_returns}")
for uid, pnl in s.user_pnl.items():
    print(f"{uid}: total={pnl.total_pnl_in_y:.4f}, "
          f"fee_income={pnl.fee_net_income_in_y:.4f}, "
          f"il_loss={pnl.il_loss_in_y:.4f}")
```

**预期结果**：
- `Pool Depth @2%` > 0（约 18.29）
- `Time Span (days)` ≈ 1.2083（t=1~t=30 除以 24 小时）
- `LP APYs` 非空
- 每个用户的 `total_pnl = wallet_pnl + position_pnl + fee_income - il_loss` 恒等关系成立

---

**测试 ⑤：批量参数遍历 + 对比表**

```python
from pathlib import Path
from src.infrastructure.config_loader import load_config
from src.application.simulation_runner import SimulationRunner
from src.application.parameter_sweep import (
    generate_param_grid, run_parameter_sweep, build_comparison_table,
)

ROOT = Path('.')
base = load_config(ROOT / 'configs' / 'default.yaml')
runner = SimulationRunner(ROOT)

grid = generate_param_grid(fee_rate=[0.001, 0.003, 0.01])
results = run_parameter_sweep(base, grid, runner, 'data/output/sweep_demo')

table = build_comparison_table(results)
for row in table:
    print(f"{row['scenario']}: "
          f"slippage={row['avg_slippage_pct']}, "
          f"depth={row['pool_depth_at_2pct']}, "
          f"fees={row['total_fees_in_y']}")
```

**预期输出**（数值近似，趋势必成立）：
```
fee_rate_0_001: slippage=4.15..., depth=20.39..., fees=0.30...
fee_rate_0_003: slippage=4.33..., depth=18.28..., fees=0.92...
fee_rate_0_01: slippage=4.98..., depth=10.84..., fees=3.07...
```

**验证逻辑**（fee_rate ↑ 时）：
| 指标 | 变化 | 原因 |
|:-----|:----|:-----|
| avg_slippage | **递增** | 手续费越高，有效交易量越小，滑点越大 |
| pool_depth | **递减** | 手续费越高，相同滑点下可交易量越小 |
| total_fees | **递增** | 费率越高，累计手续费越多 |

**输出目录结构**：
```
data/output/sweep_demo/
├── fee_rate_0_001/         # CSV + JSON + 8 张 PNG
├── fee_rate_0_003/
├── fee_rate_0_01/
├── comparison.csv          # 对比表 (3行 × 12列)
└── multi_scenario_comparison.png  # 分组柱状对比图
```

---

**测试 ⑥：Excel 多 Sheet 导出验证**

```python
from pathlib import Path
from src.infrastructure.config_loader import load_config
from src.application.simulation_runner import SimulationRunner
from src.infrastructure.excel_exporter import export_to_excel
import openpyxl

ROOT = Path('.')
config = load_config(ROOT / 'configs' / 'default.yaml')
runner = SimulationRunner(ROOT)
artifacts = runner.run_from_config(config)
xlsx_path = export_to_excel(artifacts, 'data/output/demo.xlsx')

wb = openpyxl.load_workbook(xlsx_path)
print(f"Sheets: {wb.sheetnames}")
for name in wb.sheetnames:
    ws = wb[name]
    print(f"  {name}: {ws.max_row} rows × {ws.max_column} cols")
```

**预期输出**：
```
Sheets: ['Event Records', 'Summary', 'User PnL', 'LP Metrics', 'Pool Depth', 'Parameters', 'Charts']
  Event Records: 10 rows × 32 cols
  Summary: 14 rows × 2 cols
  User PnL: 4 rows × 14 cols
  LP Metrics: 3 rows × 9 cols
  Pool Depth: 7 rows × 3 cols
  Parameters: 14 rows × 2 cols
  Charts: 151 rows × 1 cols
```

---

### 方式三：Web 界面交互式测试

```bash
python -m streamlit run streamlit_app.py
```

打开浏览器（默认 http://localhost:8501），按以下步骤操作：

| # | 操作 | 预期结果 |
|:-:|:----|:---------|
| 1 | 点击 **Default Config** 页签，点击 **▶ Run Default Config** | 显示 3 行指标卡片（共 12 个），新增 **Best LP APY**、**Pool Depth @2%**、**IL Amount**、**Time Span** |
| 2 | 滚动到 **Charts** 区域 | 8 张图表以 2 列网格排列，含 **candlestick** 和 **slippage_volume** |
| 3 | 展开 **📊 Detailed PnL Breakdown** | 显示每个用户的 Wallet / Fee Income / IL Loss / Total PnL 明细表 |
| 4 | 点击 **📥 Download CSV Log** | 下载 simulation.csv（32 列） |
| 5 | 点击 **📥 Download JSON Summary** | 下载 summary.json（含 `lp_annualized_returns`、`pool_depth_at_2pct`、`time_span_days`） |
| 6 | 点击 **📥 Download Excel Report** | 下载 simulation.xlsx（7 个 Sheet） |
| 7 | 切换到 **Custom Simulation**，改 fee_rate 为 0.01，点击 **▶ Run Custom Simulation** | 滑点/手续费等指标相应变化 |
| 8 | 在事件表中新增 2 行 swap 事件，再次运行 | 事件记录表更新，图表数据点增加 |
| 9 | 展开 **💾 Save / Load Config**，输入名称保存，再重新加载 | 参数恢复为保存时的状态 |

---

### 回归测试

```bash
# 运行全部 51 个测试用例
python -m pytest -q

# 详细输出模式
python -m pytest -v
```

| 测试文件 | 覆盖内容 |
|----------|---------|
| `tests/test_pool.py` | AMM 交易与流动性核心 |
| `tests/test_liquidity.py` | LP 添加/移除完整流程 |
| `tests/test_simulator.py` | 仿真引擎与事件调度 |
| `tests/test_analytics.py` | 滑点、无常损失、PnL |
| `tests/test_edge_cases.py` | 边界条件与极端场景 |
| `tests/test_runner.py` | SimulationRunner 完整流程 |
| `tests/test_validation.py` | 输入校验 |
| `tests/test_visualization.py` | 图表生成 |
| `tests/test_web_support.py` | Web 层数据转换 |
| `tests/test_scenarios.py` | 实验场景构造 |
| `tests/test_cli_demo.py` | CLI 非交互式 Demo |

---

## 📌 项目边界

- 单交易对、单资金池
- 恒定乘积 AMM（不包含恒定和、恒定均值等变体）
- 本地离线仿真（不接链上 API、不处理真实资产）
- 不涉及借贷、清算、DAO 治理等其他 DeFi 方向

> 可基于当前分层架构扩展套利机器人、多池路由、历史价格回测、多曲线 AMM 等功能。

---

## 🔧 环境要求

- Python ≥ 3.10
- 依赖详见 [`requirements.txt`](requirements.txt)

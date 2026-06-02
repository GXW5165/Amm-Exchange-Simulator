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

本节面向项目开发者，目标是说明每次修改后应如何验证代码，而不是提供单次演示用例。建议按“自动化测试 → CLI 冒烟 → Web 冒烟 → 产物检查”的顺序执行。

### 1. 准备环境

先在项目根目录安装依赖，并确认使用的是同一个 Python 环境：

```bash
pip install -r requirements.txt
python --version
```

如果依赖或 Python 版本发生变化，先重新运行完整测试，再进行功能验证。

### 2. 运行自动化测试

常规开发完成后先运行全部测试：

```bash
python -m pytest -q
```

需要定位失败原因时使用详细模式：

```bash
python -m pytest -v
```

修改单个模块时，可以先运行相关测试文件，确认局部行为，再回到全量测试。例如修改分析指标后先跑 `tests/test_analytics.py`，修改仿真主循环后先跑 `tests/test_simulator.py` 或 `tests/test_edge_cases.py`。

### 3. 运行 CLI 冒烟测试

自动化测试通过后，运行非交互式 Demo，确认配置加载、仿真、摘要、图表导出链路正常：

```bash
python main.py --demo
```

检查命令输出中事件数、swap 数、流动性事件数、手续费、滑点和无常损失字段是否正常打印。随后检查 `data/output/logs/` 和 `data/output/results/` 是否生成 CSV、JSON 和 PNG 图表。

配置文件路径相关改动需要额外运行：

```bash
python main.py --config configs/default.yaml
python main.py --config configs/default.yaml --scenarios
```

场景命令应在 `data/output/scenarios/` 下生成每个场景独立的日志、摘要和图表。

### 4. 运行 Web 冒烟测试

```bash
python -m streamlit run streamlit_app.py
```

打开浏览器后按以下流程检查：

| # | 操作 | 预期结果 |
|:-:|:----|:---------|
| 1 | 运行默认配置 | 摘要指标、事件表、用户 PnL 和图表正常展示 |
| 2 | 下载 CSV、JSON 和 Excel | 下载文件存在且能打开 |
| 3 | 修改自定义参数并运行 | 指标、事件记录和图表随输入变化 |
| 4 | 保存并加载自定义配置 | 加载后表单恢复为保存时的参数 |

Web 相关代码变更后，应同时检查默认配置流程和自定义配置流程。

### 5. 检查导出产物

每次完整验证后，至少检查以下产物：

| 产物 | 检查内容 |
|:-----|:---------|
| CSV 日志 | 字段完整，事件数量与配置一致 |
| JSON 摘要 | 总事件数、手续费、滑点、IL、PnL、LP 指标存在 |
| PNG 图表 | 价格、储备、滑点、费用、IL、PnL 等图表生成 |
| Excel 报告 | Event Records、Summary、User PnL、LP Metrics、Pool Depth、Parameters、Charts 等 Sheet 存在 |

导出目录通常位于 `data/output/`。该目录属于运行产物，不应提交到版本库。

### 6. 测试覆盖范围

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

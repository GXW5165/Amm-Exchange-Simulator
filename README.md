# 📈 AMM Exchange Simulator

> **恒定乘积自动做市商 · 离线仿真系统**

本地离线 AMM 交易所仿真系统，基于恒定乘积模型 `x · y = k`，支持多用户、离散事件调度、流动性管理、手续费分析、滑点计算、无常损失评估和可视化图表输出。

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
| **用户 PnL** | 按 Token Y 统一计价，钱包 + LP 仓位合并收益统计 |
| **离散事件仿真** | 按时间戳优先队列调度，同时间保持入队顺序 |
| **多用户** | 独立钱包余额与 LP 份额，自动创建新用户 |
| **配置驱动** | YAML 文件定义池参数、用户初始状态和事件序列 |
| **CSV / JSON 导出** | 事件级日志（35 字段）和结构化摘要 |
| **可视化图表** | 价格、储备、滑点、累计手续费、无常损失、用户 PnL（6 张 PNG） |
| **实验场景** | 大额交易冲击、手续费率对比、流动性深度对比 |
| **Web 界面** | Streamlit 参数编辑、事件表格、结果展示、配置保存/加载 |
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
│   │   └── scenarios.py            实验场景构造
│   │
│   ├── analytics/                 # ── 分析层 ──
│   │   ├── record.py               事件记录（35 字段快照）
│   │   ├── slippage.py             滑点计算
│   │   ├── impermanent_loss.py     无常损失计算
│   │   ├── pnl.py                  用户收益计算
│   │   └── report.py               聚合摘要报告
│   │
│   ├── infrastructure/            # ── 基础设施层 ──
│   │   ├── config_loader.py        YAML → AppConfig
│   │   ├── csv_exporter.py         事件日志 → CSV
│   │   ├── summary_exporter.py     摘要 → JSON
│   │   └── logger.py               日志记录器
│   │
│   ├── interface/                 # ── 接口层 ──
│   │   └── cli.py                  交互式 / 非交互式 CLI
│   │
│   ├── visualization/             # ── 可视化层 ──
│   │   └── plotter.py              6 张 PNG 图表生成
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
│   └── output/                    # 仿真输出（日志、摘要、图表）
│
├── tests/                         # 47 个测试用例
│
├── requirements.txt               # Python 依赖
└── README.md                      # ← 你现在正在看这里
```

### 分层说明

| 层 | 职责 | 依赖方向 |
|:---|:-----|:--------|
| **Interface** | CLI + Web 用户交互 | → 调用 Application |
| **Application** | 运行编排、校验、场景 | → 调用 Simulator / Infrastructure |
| **Simulator** | 事件调度、流程控制 | → 调用 AMM / Analytics |
| **AMM Service** | 交易报价、流动性计算 | → 调用 Domain |
| **Domain** | 资金池、用户等核心数据模型 | — 无依赖 |
| **Analytics** | 滑点、IL、PnL、报告 | → 调用 Domain |
| **Infrastructure** | 配置加载、文件导出 | — 被各层调用 |

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
│   └── simulation.csv             # 事件级日志（35 字段）
└── results/
    ├── summary.json               # 结构化摘要
    ├── pool_spot_price.png        # 现货价格走势
    ├── pool_reserves.png          # 双边储备变化
    ├── swap_slippage.png          # 交易滑点
    ├── cumulative_fees.png        # 累计手续费（Y 计价）
    ├── impermanent_loss.png       # 无常损失百分比
    └── user_total_pnl.png         # 用户总收益柱状图
```

实验场景输出至 `data/output/scenarios/<name>/`，Web 运行输出至 `data/output/web_runs/<run_id>/`。

---

## 🧪 测试

```bash
# 运行全部 47 个测试
python -m pytest -q
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

> 可基于当前分层架构扩展套利机器人、多池路由、历史价格回测等功能。

---

## 🔧 环境要求

- Python ≥ 3.10
- 依赖详见 [`requirements.txt`](requirements.txt)

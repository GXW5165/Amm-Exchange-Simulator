# AMM Exchange Simulator

## 项目简介

这是一个基于 Python 的 AMM 交易所仿真系统，用于模拟恒定乘积做市模型 `x * y = k` 下的交易、流动性增减和指标分析流程。

项目当前已经具备以下完整链路：

- 配置加载
- 离散事件构造与调度
- AMM 交易与 LP 状态更新
- 滑点、无常损失、用户收益统计
- CSV 日志导出
- JSON 摘要导出
- PNG 图表导出
- CLI 交互入口

## 当前实现范围

### 已实现

- 恒定乘积池 `Pool`
- 双向兑换 `x_to_y / y_to_x`
- 手续费计算
- 添加/移除流动性
- 多用户仿真
- 离散事件驱动执行
- 滑点统计
- 无常损失统计
- 用户总收益统计
- CSV/JSON/PNG 输出
- `pytest` 单元测试

### 后续可扩展

- 多池仿真
- 套利行为模拟
- Web 界面
- 历史数据回测
- 多种 AMM 模型对比

## 架构设计

项目现在采用更贴近代码实现的五层结构：

```text
Interface Layer
  -> Application Layer
    -> Simulator Layer
      -> AMM Service Layer
        -> Domain Layer
        -> Infrastructure / Visualization / Analytics
```

这次结构调整以《概要设计说明书》为基础，但没有机械照搬文档中的中文模块名，而是采用更适合 Python 项目维护的包名。核心对应关系如下：

| 概要设计模块 | 当前代码位置 | 说明 |
| --- | --- | --- |
| 界面模块 | `main.py`、`streamlit_app.py`、`src/interface/`、`src/web/` | 提供 CLI 和 Streamlit Web 交互入口 |
| 仿真控制模块 | `src/simulator/`、`src/application/simulation_runner.py` | 负责事件队列、场景构造、流程编排和结果封装 |
| AMM 核心模块 | `src/amm/engine.py`、`src/domain/pool.py` | 实现恒定乘积报价、兑换和池状态维护 |
| 流动性管理模块 | `src/amm/liquidity_manager.py` | 实现添加/移除流动性和 LP 份额计算 |
| 指标计算模块 | `src/analytics/metrics.py`、`src/analytics/slippage.py`、`src/analytics/impermanent_loss.py`、`src/analytics/pnl.py` | 计算滑点、无常损失和用户收益 |
| 数据管理模块 | `src/infrastructure/` | 负责配置读取、CSV 日志导出、JSON 摘要导出 |
| 可视化模块 | `src/visualization/plotter.py` | 生成价格、滑点、用户收益图表 |

这样调整后，`Pool` 主要负责保存资金池状态，`AMMEngine` 负责交易公式，`LiquidityManager` 负责 LP 逻辑，`SimulatorEngine` 负责事件调度，职责边界更接近概要设计中的“高内聚、低耦合”原则。

### 1. Interface Layer

负责用户交互和程序入口。

- `main.py`
- `src/interface/cli.py`

职责：

- 展示 CLI 菜单
- 接收用户输入
- 调用应用层执行默认仿真或手动操作

### 2. Application Layer

负责把配置、仿真执行和结果导出封装为一个完整用例。

- `src/application/simulation_runner.py`

职责：

- 从配置构建仿真实例
- 执行事件流
- 导出 CSV
- 导出 JSON 摘要
- 导出 PNG 图表

### 3. Simulator Layer

负责离散事件调度和事件驱动执行。

- `src/simulator/event.py`
- `src/simulator/event_queue.py`
- `src/simulator/scenario_builder.py`
- `src/simulator/engine.py`
- `src/simulator/result.py`

职责：

- 定义事件模型
- 构造事件序列
- 逐个调度交易/加池/减池事件
- 调用 AMM 服务层和指标计算模块
- 产出 `SimulationResult`

### 4. AMM Service Layer

负责恒定乘积交易逻辑和流动性份额逻辑。

- `src/amm/engine.py`
- `src/amm/liquidity_manager.py`

职责：

- 提供 `quote()` 和 `swap()` 交易接口
- 计算手续费、有效输入和成交输出
- 添加/移除流动性
- 计算 LP 份额铸造和销毁
- 统一修改资金池状态

### 5. Domain Layer

负责核心状态对象。

- `src/domain/pool.py`
- `src/domain/user.py`
- `src/domain/lp_position.py`
- `src/domain/exceptions.py`

职责：

- 管理池子储备
- 管理用户余额与 LP 份额
- 提供基础状态属性，如池内价格和恒定乘积值
- 抛出业务异常

### 6. Analytics / Infrastructure / Visualization

负责结果分析、数据导出和图表生成。

Analytics:

- `src/analytics/metrics.py`
- `src/analytics/slippage.py`
- `src/analytics/impermanent_loss.py`
- `src/analytics/pnl.py`
- `src/analytics/report.py`
- `src/analytics/record.py`

Infrastructure:

- `src/infrastructure/config_loader.py`
- `src/infrastructure/csv_exporter.py`
- `src/infrastructure/summary_exporter.py`
- `src/infrastructure/logger.py`

Visualization:

- `src/visualization/plotter.py`

职责：

- 计算平均/最大滑点
- 计算无常损失
- 汇总用户收益
- 导出事件日志和摘要
- 生成价格、滑点、收益图表

## 目录结构

```text
amm-exchange-simulator/
├── configs/
│   └── default.yaml
├── src/
│   ├── application/
│   │   ├── __init__.py
│   │   └── simulation_runner.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── impermanent_loss.py
│   │   ├── metrics.py
│   │   ├── pnl.py
│   │   ├── record.py
│   │   ├── report.py
│   │   └── slippage.py
│   ├── amm/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── liquidity_manager.py
│   ├── domain/
│   │   ├── exceptions.py
│   │   ├── lp_position.py
│   │   ├── metrics.py
│   │   ├── pool.py
│   │   └── user.py
│   ├── infrastructure/
│   │   ├── config_loader.py
│   │   ├── csv_exporter.py
│   │   ├── logger.py
│   │   └── summary_exporter.py
│   ├── interface/
│   │   └── cli.py
│   ├── web/
│   │   ├── __init__.py
│   │   └── app_support.py
│   ├── simulator/
│   │   ├── engine.py
│   │   ├── event.py
│   │   ├── event_queue.py
│   │   ├── result.py
│   │   └── scenario_builder.py
│   └── visualization/
│       ├── __init__.py
│       └── plotter.py
├── tests/
│   ├── test_analytics.py
│   ├── test_liquidity.py
│   ├── test_pool.py
│   ├── test_runner.py
│   ├── test_simulator.py
│   ├── test_web_support.py
│   └── test_visualization.py
├── main.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```

## 环境要求

- Python >= 3.10
- 推荐使用 Conda 虚拟环境

你的当前环境：

- 虚拟环境路径：`D:\miniconda3\envs\jrrg`

## 依赖安装

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pip install -r requirements.txt
```

## 配置文件说明

默认配置文件路径：

- `configs/default.yaml`

当前关键配置项：

- `initial_reserve_x`：池子初始 X 储备
- `initial_reserve_y`：池子初始 Y 储备
- `fee_rate`：手续费率
- `log_path`：CSV 事件日志输出路径
- `summary_path`：JSON 摘要输出路径
- `plot_dir`：PNG 图表输出目录
- `users`：初始用户资产
- `events`：仿真事件序列

## 功能说明

### 1. 默认配置仿真

系统读取 `configs/default.yaml`，创建初始资金池、用户资产和事件序列，然后按时间顺序执行仿真。该功能适合快速演示完整链路。

### 2. 交易功能

交易事件支持两种方向：

- `x_to_y`：用户输入 Token X，换出 Token Y。
- `y_to_x`：用户输入 Token Y，换出 Token X。

交易时系统会先扣除手续费得到有效输入 `dx'`，再根据恒定乘积公式计算输出数量。交易完成后，用户余额和池子储备都会更新，并记录成交价格、手续费和滑点。

### 3. 添加流动性

LP 用户可以向池子注入两种资产。首次建池时，系统用几何平均值生成初始 LP 份额；后续加池时，系统按当前池子比例消耗资产，避免破坏池内价格。

### 4. 移除流动性

LP 用户提交要赎回的 LP 份额，系统按该份额占总 LP 份额的比例返还两侧资产，并同步减少池子储备和 LP 总份额。

### 5. 指标分析

系统会统计：

- 滑点：实际成交价格相对理论价格的偏离。
- 手续费：每笔交易输入金额按费率产生的费用。
- 无常损失：LP 相比单纯持有资产时的相对损失。
- 用户收益：用户钱包资产和 LP 仓位折算后的总价值变化。

### 6. 数据导出与可视化

默认仿真结束后会生成：

- CSV 事件日志：用于查看每一步交易或流动性事件。
- JSON 摘要：用于查看总事件数、手续费、滑点、无常损失、用户收益等结果。
- PNG 图表：用于展示池内价格变化、滑点变化和用户收益对比。

## 运行方式

### 1. 启动 CLI

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py
```

### 2. 启动 Streamlit Web 界面

```powershell
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

启动后浏览器会打开一个本地页面，默认地址通常是：

```text
http://localhost:8501
```

### 3. 在 CLI 中执行默认仿真

启动后输入：

```text
1
```

默认仿真会自动执行完整流程：

- 读取 `configs/default.yaml`
- 执行事件流
- 输出指标摘要
- 导出 CSV
- 导出 JSON
- 导出 PNG 图表

### 4. 在 Web 中执行默认仿真

打开页面后：

- 进入“默认配置”页签
- 点击“运行默认配置”

预期会看到：

- 指标卡片
- 事件记录表
- 用户收益表
- CSV / JSON 下载按钮
- 三张图表

### 5. 在 Web 中执行自定义仿真

打开页面后：

- 进入“自定义仿真”页签
- 修改池子参数
- 修改用户表
- 修改事件表
- 点击“运行自定义仿真”

预期会看到和默认仿真相同的结果展示，但数据来自你手工输入的参数

## 输出文件

默认输出目录如下：

- CSV 日志：`data/output/logs/simulation.csv`
- JSON 摘要：`data/output/results/summary.json`
- 价格图：`data/output/results/pool_spot_price.png`
- 滑点图：`data/output/results/swap_slippage.png`
- 用户收益图：`data/output/results/user_total_pnl.png`

## 核心数学模型

### 恒定乘积

```text
x * y = k
```

### 交易

```text
dx' = dx(1 - f)
dy = y - k / (x + dx')
```

### 滑点

```text
slippage = (P_theory - P_actual) / P_theory
```

### 无常损失

```text
IL(r) = 2*sqrt(r)/(1 + r) - 1
```

## 项目测试步骤

下面这组步骤按你当前环境可直接执行。

### 1. 安装依赖

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pip install -r requirements.txt
```

### 2. 运行全部测试

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest -q
```

### 3. 运行单个模块测试

池子核心逻辑：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest tests/test_pool.py -q
```

流动性逻辑：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest tests/test_liquidity.py -q
```

仿真流程：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest tests/test_simulator.py -q
```

分析指标：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest tests/test_analytics.py -q
```

可视化输出：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest tests/test_visualization.py -q
```

整体封装导出：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest tests/test_runner.py -q
```

### 4. 手动验收默认仿真

执行：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py
```

然后在 CLI 中输入：

```text
1
```

你应当检查以下结果：

- 控制台输出事件数、手续费、滑点、IL
- `data/output/logs/simulation.csv` 已生成
- `data/output/results/summary.json` 已生成
- `data/output/results/` 下的三张 PNG 图已生成

### 5. 手动验收 Streamlit 页面

执行：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

你应当检查以下结果：

- 页面能正常打开
- “默认配置”页签点击后能看到指标、表格和图表
- “自定义仿真”页签能编辑用户和事件
- 点击运行后能看到新的结果
- 可以下载 CSV 和 JSON

## 设计原则

- 高内聚、低耦合
- 分层清晰
- 领域逻辑与导出逻辑分离
- 应用流程统一封装
- 便于扩展多场景和多模型

## 项目用途

本项目用于：

- 课程设计
- AMM 机制学习
- 仿真实验分析

不用于任何真实交易或金融建议场景。

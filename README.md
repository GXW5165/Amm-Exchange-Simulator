# AMM Exchange Simulator

本项目是一个本地离线运行的 AMM 交易所仿真系统，面向课程设计、DeFi 机制学习和实验分析。系统以 `construction/` 中的需求分析与概要设计为方向，聚焦单交易对、单资金池、恒定乘积模型 `x * y = k`，完整覆盖交易、LP 流动性操作、手续费、滑点、无常损失、用户收益、日志导出和图表展示。

项目不连接真实区块链节点，不处理真实资产，也不作为任何金融建议。

## 功能完成情况

| 需求 | 状态 | 说明 |
| --- | --- | --- |
| 恒定乘积双向兑换 | 已实现 | 支持 `x_to_y` 和 `y_to_x`，按扣费后的有效输入定价 |
| 交易滑点 | 已实现 | 记录理论价格、成交价格和百分比滑点 |
| LP 添加流动性 | 已实现 | 首次/后续加池自动计算 LP 份额，保持池内比例 |
| LP 移除流动性 | 已实现 | 按 LP 份额比例赎回两侧资产 |
| 手续费累计与 LP 收益 | 已实现 | 手续费留在池内，并在收益分析中折算为 Y 计价 |
| 无常损失 | 已实现 | 输出无常损失率和按当前价值估算的损失金额 |
| 离散事件仿真 | 已实现 | 事件队列按时间戳稳定调度 |
| 参数配置 | 已实现 | 支持 YAML 默认配置和 Web 手动输入 |
| CSV/JSON 导出 | 已实现 | 输出事件日志和结构化摘要 |
| CLI | 已实现 | 支持一键仿真、手动操作和场景实验 |
| 可视化 | 已实现 | 输出价格、储备、滑点、手续费、无常损失、用户收益图 |
| 多用户模拟 | 已实现 | 每个用户独立维护钱包余额和 LP 份额 |
| 极端场景/参数对比 | 已实现 | 支持大额交易冲击、手续费率对比、流动性深度对比 |
| Streamlit Web | 已实现 | 支持参数编辑、事件编辑、结果表格、图表和下载 |

## 架构

```text
Interface Layer
  -> Application Layer
    -> Simulator Layer
      -> AMM Service Layer
        -> Domain Layer
        -> Analytics / Infrastructure / Visualization
```

核心模块如下：

- `src/domain/`：资金池、用户、异常等领域对象。
- `src/amm/`：恒定乘积交易引擎和流动性管理。
- `src/simulator/`：事件、事件队列、仿真调度和仿真结果。
- `src/analytics/`：滑点、无常损失、PnL、汇总报告和事件记录。
- `src/application/`：完整仿真运行、输入校验、实验场景构造。
- `src/infrastructure/`：配置加载、CSV 导出、JSON 导出、日志。
- `src/visualization/`：PNG 图表生成。
- `src/interface/`：CLI 入口。
- `src/web/` 与 `streamlit_app.py`：Streamlit Web 交互。

## 核心模型

交易使用恒定乘积模型：

```text
k = x * y
dx' = dx * (1 - fee_rate)
dy = y - k / (x + dx')
```

注意：定价使用扣费后的 `dx'`，但池子实际增加的是用户输入总额 `dx`，手续费留在池中并由 LP 按份额隐含获得。

滑点：

```text
slippage = abs(P_actual - P_theory) / P_theory * 100
```

无常损失：

```text
IL(r) = 2 * sqrt(r) / (1 + r) - 1
```

## 运行环境

- Python >= 3.10
- 推荐 Conda 环境：`D:\miniconda3\envs\jrrg`

安装依赖：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pip install -r requirements.txt
```

## 运行 CLI

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py
```

CLI 支持：

- 默认配置仿真
- 手动初始化资金池
- 手动执行交易
- 添加/移除流动性
- 查看池状态和用户状态
- 运行实验场景，包括大额冲击、手续费对比、流动性深度对比

## 运行 Web

```powershell
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

默认地址通常为：

```text
http://localhost:8501
```

Web 页面支持：

- 一键运行默认配置
- 编辑初始池参数、用户资产和事件序列
- 输入校验与错误提示
- 查看摘要指标、事件日志、用户收益表
- 下载 CSV 日志和 JSON 摘要
- 查看自动生成的 PNG 图表

## 配置文件

默认配置位于：

```text
configs/default.yaml
```

关键字段：

- `initial_reserve_x`：初始 Token X 储备
- `initial_reserve_y`：初始 Token Y 储备
- `fee_rate`：手续费率，要求 `0 <= fee_rate < 1`
- `users`：用户初始余额与 LP 份额
- `events`：按时间执行的仿真事件
- `log_path`：CSV 日志输出路径
- `summary_path`：JSON 摘要输出路径
- `plot_dir`：图表输出目录

## 输出文件

默认仿真输出：

```text
data/output/logs/simulation.csv
data/output/results/summary.json
data/output/results/pool_spot_price.png
data/output/results/pool_reserves.png
data/output/results/swap_slippage.png
data/output/results/cumulative_fees.png
data/output/results/impermanent_loss.png
data/output/results/user_total_pnl.png
```

实验场景输出：

```text
data/output/scenarios/<scenario_name>/
```

## 日志字段

CSV 事件日志包含可还原仿真过程的核心字段：

- 事件信息：`event_id`、`timestamp`、`user_id`、`event_type`、`direction`
- 交易信息：`amount_in`、`effective_amount_in`、`amount_out`、`fee`
- 价格指标：`spot_price_before`、`spot_price`、`theoretical_price`、`execution_price`、`slippage_pct`
- 池状态：`reserve_x_before`、`reserve_y_before`、`reserve_x_after`、`reserve_y_after`
- 用户状态：`wallet_x_before`、`wallet_y_before`、`wallet_x_after`、`wallet_y_after`
- LP 状态：`lp_shares_before`、`lp_shares_after`、`lp_shares_delta`、`lp_total_shares`
- 一致性指标：`invariant_before`、`invariant_after`

## 测试

运行全部测试：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest -q
```

当前测试覆盖：

- 恒定乘积交易
- LP 添加和移除
- 滑点、无常损失、用户收益
- 默认配置完整运行
- CSV/JSON/PNG 导出
- Web 输入归一化
- 输入校验
- 实验场景构造

## 项目边界

当前版本严格聚焦课程设计核心边界：

- 单交易对
- 单资金池
- 恒定乘积 AMM
- 本地离线仿真
- 不接链上 API
- 不做真实交易

套利、多池路由、历史价格回测、恒定均值模型等功能可以基于现有分层继续扩展，但不作为本版本核心验收目标。

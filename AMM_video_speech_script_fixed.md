# AMM 录屏讲话稿修正版

> 这版修正三个问题：  
> 1. Web 现在已修复，`Fee Rate Values` 可以填写 `0, 0.003, 0.01`。如果你没有重启 Streamlit，旧页面仍可能报错，需要重启服务。  
> 2. 不再建议在 Web 中单独扫 X Reserve 或 Y Reserve 来讲“流动性变深”，因为只改一侧储备会改变初始价格。流动性深度对比改用 CLI 内置场景 `--scenarios`，它会生成 `liquidity_0.5x / 1x / 2x`。
> 3. PDF 下载已改为每次按当前结果重新生成；Parameter Sweep 单场景 PDF 会从 `plots/` 子目录读取图表，不再下载旧版或无图表报告。

---

## 0:00 - 0:20 开场

### 做什么

打开 PowerShell：

```powershell
cd D:\cs-projects\amm-exchange-simulator
dir
```

### 说什么

大家好，我现在展示的是 AMM Exchange Simulator。  
这是一个本地离线运行的恒定乘积 AMM 仿真系统，核心模型是 `x * y = k`。  
系统支持 swap、添加流动性、移除流动性、套利、历史价格回测、参数遍历，并且可以导出 CSV、JSON、Excel、PDF 和图表。

---

## 0:20 - 1:00 完整测试

### 做什么

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest -q
```

### 预期

```text
102 passed
```

### 说什么

我先运行完整测试，确认系统当前状态是可用的。  
测试覆盖 AMM 数学、swap、流动性、套利、事件调度、输入校验、CLI、Web 支撑函数、回测、图表和报告生成。  
这里显示 `102 passed`，说明主要功能都通过了自动化测试。

---

## 1:00 - 1:40 CLI 默认 Demo

### 做什么

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --demo
```

### 预期

```text
[simulation] processed_events=23
[simulation] swap_events=13
[simulation] liquidity_events=7
[simulation] arbitrage_events=3
[simulation] total_fees=4.325209
[simulation] average_slippage_pct=5.345622
```

### 说什么

现在运行默认 demo。  
系统一共处理 23 个事件，其中包括 13 个 swap、7 个流动性事件和 3 个套利事件。  
运行结束后自动生成 CSV 事件日志、JSON 摘要和多张 PNG 图表。

---

## 1:40 - 2:20 CLI 套利配置

### 做什么

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/arbitrage_demo.yaml
```

### 预期

```text
[simulation] processed_events=5
[simulation] swap_events=2
[simulation] arbitrage_events=3
[simulation] total_fees=1.414273
```

### 说什么

这里运行套利演示配置。  
这个配置专门展示当外部市场价格和池内价格出现偏离时，系统如何检测并执行套利。  
可以看到 5 个事件中有 3 个是套利事件。

---

## 2:20 - 3:00 如果一：如果流动性变深，会发生什么

### 做什么

用 CLI 运行内置对比场景：

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml --scenarios
```

### 预期

输出中会出现：

```text
[liquidity_0.5x]
[liquidity_1x]
[liquidity_2x]
```

同时还会出现：

```text
average_slippage_pct=...
max_slippage_pct=...
```

### 说什么

第一个“如果”是：如果流动性变深，会发生什么？

这里我不用 Web 单独改 X 储备或 Y 储备，因为只改一侧会同时改变初始价格。  
我使用 CLI 内置场景，它会按比例生成 `liquidity_0.5x`、`liquidity_1x` 和 `liquidity_2x`，更适合展示池子整体深度变化。

一般来说，池子越深，同样大小的交易造成的价格冲击越小，所以平均滑点和最大滑点会下降。

---

## 3:00 - 3:30 启动 Web 页面

### 做什么

如果刚才 Web 已经开着，先在终端按 `Ctrl+C` 停止旧服务，然后重新启动：

```powershell
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

打开：

```text
http://localhost:8501
```

### 说什么

接下来展示 Web 页面。  
这里重新启动 Streamlit，是为了确保刚才修复的参数解析逻辑已经生效。

---

## 3:30 - 4:10 Web 默认配置

### 做什么

进入：

```text
Default Config
```

点击：

```text
Run Default Config
```

### 说什么

默认配置会读取 `configs/default.yaml` 并运行完整仿真。  
这里可以看到 Summary、Event Records、User PnL、Charts 和 Downloads。  
说明系统可以在 Web 页面中完成运行、分析和结果下载。

---

## 4:10 - 5:00 如果二：如果手续费率变化，会发生什么

### 做什么

进入：

```text
Parameter Sweep
```

设置：

```text
Enable Fee Rate Sweep: 勾选
Fee Rate Values: 0, 0.003, 0.01
Enable X Reserve Sweep: 不勾选
Enable Y Reserve Sweep: 不勾选
Initial LP Owner: protocol
```

点击：

```text
Run Parameter Sweep
```

### 预期

页面不应再出现：

```text
Fee Rate Values values must be positive
```

结果中应能看到三个费率场景：

```text
fee_rate_0
fee_rate_0_003
fee_rate_0_01
```

重点观察：

```text
total_fees
total_fees_in_y
average_slippage_pct
max_slippage_pct
```

### 说什么

第二个“如果”是：如果手续费率变化，会发生什么？

我设置三个手续费率：0、0.003 和 0.01。  
`fee_rate=0` 表示无手续费基准；`0.003` 是常见的 0.3%；`0.01` 是 1%。

从结果可以看到，手续费率为 0 时手续费收入为 0 或接近 0；费率提高后，`total_fees` 和 `total_fees_in_y` 会增加。  
但手续费越高，交易者进入定价公式的有效输入越少，所以交易成本和滑点也会发生变化。

如果录屏现场没有重启 Streamlit，`0` 仍然报错，可以临时改成：

```text
0.001, 0.003, 0.01
```

但修复后的正确演示值是：

```text
0, 0.003, 0.01
```

---

## 5:00 - 5:50 如果三：如果单笔交易规模变大，会发生什么

### 做什么

进入：

```text
Custom Simulation
```

第一次运行，把一个 swap 事件设置为：

```text
timestamp: 50
event_type: swap
user_id: alice
direction: x_to_y
amount_in: 50
```

点击：

```text
Run Custom Simulation
```

然后把同一笔交易改成：

```text
amount_in: 200
```

再次点击：

```text
Run Custom Simulation
```

### 预期

重点观察：

```text
average_slippage_pct
max_slippage_pct
Event Records
Charts
User PnL
```

### 说什么

第三个“如果”是：如果单笔交易规模变大，会发生什么？

AMM 使用恒定乘积模型，交易越大，对池子储备比例的影响越明显。  
所以我先运行一笔 `amount_in=50` 的交易，再把它改成 `amount_in=200`。

对比两次结果可以看到，交易规模变大后，滑点通常会更高，池子价格变化也更明显，用户 PnL 和图表都会发生变化。

---

## 5:50 - 6:50 Backtesting：如果价格波动阈值改变，会触发多少交易

### 做什么

进入：

```text
Backtesting
```

第一次设置：

```text
内置样例: volatile_market.csv
Initial X Reserve: 1000
Initial Y Reserve: 1000
Fee Rate: 0.003
Volatility Threshold: 0.01
Max Trade Size: 100
```

运行一次。

第二次只改：

```text
Volatility Threshold: 0.05
```

再运行一次。

### 预期

```text
阈值 0.01 通常触发更多 swap
阈值 0.05 通常触发更少 swap
```

### 说什么

这里展示历史价格回测。  
系统读取价格 CSV，当相邻价格变化超过阈值时自动生成交易事件。

阈值为 0.01 时，价格变化超过 1% 就会触发交易，所以事件更多。  
阈值为 0.05 时，只有超过 5% 的变化才触发交易，所以事件更少。  
这会进一步影响手续费、滑点和用户收益。

---

## 6:50 - 7:30 结果输出

### 做什么

展示下载按钮：

```text
Download CSV Log
Download JSON Summary
Download Excel Report
Download PDF Report
```

终端展示：

```powershell
dir data\output\logs
dir data\output\results
dir data\output\scenarios
dir data\output\sweeps\web_sweep
```

### 说什么

最后展示结果输出。  
CSV 是事件级日志，JSON 是结构化摘要，Excel 是多 Sheet 分析报告，PDF 是实验报告，PNG 是图表。  
这说明系统不仅能运行仿真，还能完成分析和结果导出。

---

## 7:30 - 7:50 结尾

### 说什么

本系统支持 CLI 和 Web 两种运行方式。  
CLI 适合复现实验和批量场景，Web 适合参数调整、结果查看和文件下载。  
系统能够执行 swap、流动性和套利事件，输出手续费、滑点、无常损失、用户 PnL 和池深度等指标，并导出 CSV、JSON、Excel、PDF 和图表，满足本次验收要求。

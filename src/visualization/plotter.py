from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from src.analytics.impermanent_loss import impermanent_loss_pct
from src.simulator.result import SimulationResult


def _save_figure(path: Path) -> Path:
    """统一保存 Matplotlib 图表并释放当前画布。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    return path


def plot_pool_price(records, output_dir: str | Path) -> Path | None:
    """绘制资金池现货价格随事件时间变化的折线图。"""
    if not records:
        return None

    timestamps = [record.timestamp for record in records]
    spot_prices = [record.spot_price for record in records]

    plt.figure(figsize=(8, 4.5))
    plt.plot(timestamps, spot_prices, color="#0f766e", linewidth=2)
    plt.title("Pool Spot Price")
    plt.xlabel("Timestamp")
    plt.ylabel("Price (Y per X)")
    plt.grid(alpha=0.25)
    return _save_figure(Path(output_dir) / "pool_spot_price.png")


def plot_slippage(records, output_dir: str | Path) -> Path | None:
    """绘制所有交易事件的滑点变化图。"""
    trade_records = [record for record in records if record.slippage_pct is not None]
    if not trade_records:
        return None

    timestamps = [record.timestamp for record in trade_records]
    slippage = [record.slippage_pct for record in trade_records]

    plt.figure(figsize=(8, 4.5))
    plt.plot(timestamps, slippage, marker="o", color="#b45309", linewidth=2)
    plt.title("Trade Slippage")
    plt.xlabel("Timestamp")
    plt.ylabel("Slippage (%)")
    plt.grid(alpha=0.25)
    return _save_figure(Path(output_dir) / "swap_slippage.png")


def plot_pool_reserves(records, output_dir: str | Path) -> Path | None:
    """绘制 Token X 和 Token Y 储备变化图。"""
    if not records:
        return None

    timestamps = [record.timestamp for record in records]
    reserve_x = [record.reserve_x for record in records]
    reserve_y = [record.reserve_y for record in records]

    plt.figure(figsize=(8, 4.5))
    plt.plot(timestamps, reserve_x, color="#2563eb", linewidth=2, label="Token X")
    plt.plot(timestamps, reserve_y, color="#dc2626", linewidth=2, label="Token Y")
    plt.title("Pool Reserves")
    plt.xlabel("Timestamp")
    plt.ylabel("Reserve")
    plt.legend()
    plt.grid(alpha=0.25)
    return _save_figure(Path(output_dir) / "pool_reserves.png")


def plot_cumulative_fees(records, output_dir: str | Path) -> Path | None:
    """绘制累计手续费图，统一折算为 Token Y 计价。"""
    fee_records = [record for record in records if record.event_type in {"swap", "arbitrage"}]
    if not fee_records:
        return None

    timestamps = []
    cumulative = []
    total = 0.0
    for record in fee_records:
        fee = float(record.fee or 0.0)
        if record.direction == "x_to_y":
            total += fee * float(record.spot_price_before or record.spot_price or 0.0)
        else:
            total += fee
        timestamps.append(record.timestamp)
        cumulative.append(total)

    plt.figure(figsize=(8, 4.5))
    plt.plot(timestamps, cumulative, marker="o", color="#7c3aed", linewidth=2)
    plt.title("Cumulative Fees")
    plt.xlabel("Timestamp")
    plt.ylabel("Fees (in Y)")
    plt.grid(alpha=0.25)
    return _save_figure(Path(output_dir) / "cumulative_fees.png")


def plot_impermanent_loss(result: SimulationResult, output_dir: str | Path) -> Path | None:
    """绘制无常损失百分比随事件推进的变化。"""
    if not result.records:
        return None

    initial_price = result.initial_pool.spot_price
    timestamps = []
    values = []
    for record in result.records:
        price = record.spot_price
        if price is None:
            continue
        value = impermanent_loss_pct(initial_price, price)
        if value is None:
            continue
        timestamps.append(record.timestamp)
        values.append(value)

    if not values:
        return None

    plt.figure(figsize=(8, 4.5))
    plt.plot(timestamps, values, color="#be123c", linewidth=2)
    plt.axhline(0, color="#334155", linewidth=1)
    plt.title("Impermanent Loss")
    plt.xlabel("Timestamp")
    plt.ylabel("IL (%)")
    plt.grid(alpha=0.25)
    return _save_figure(Path(output_dir) / "impermanent_loss.png")


def plot_user_pnl(result: SimulationResult, output_dir: str | Path) -> Path | None:
    """绘制各用户最终总 PnL 柱状图。"""
    pnl_summary = result.summary.user_pnl
    if not pnl_summary:
        return None

    user_ids = list(pnl_summary.keys())
    pnl_values = [pnl_summary[user_id].total_pnl_in_y for user_id in user_ids]
    colors = ["#15803d" if value >= 0 else "#b91c1c" for value in pnl_values]

    plt.figure(figsize=(8, 4.5))
    plt.bar(user_ids, pnl_values, color=colors)
    plt.axhline(0, color="#334155", linewidth=1)
    plt.title("User Total PnL")
    plt.xlabel("User")
    plt.ylabel("PnL (in Y)")
    plt.grid(axis="y", alpha=0.25)
    return _save_figure(Path(output_dir) / "user_total_pnl.png")


# ── 新增图表：K 线（蜡烛图） ────────────────────────────────────────────


def _build_ohlc_buckets(records, num_buckets: int = 30) -> list[dict] | None:
    """从事件记录的现货价格中提取 OHLC 分桶数据。

    只使用 swap 事件的 spot_price 构建蜡烛图。若 swap 事件不足 2 个则返回 None。
    """
    swap_prices = [
        (r.timestamp, r.spot_price)
        for r in records
        if r.event_type == "swap" and r.spot_price is not None and r.spot_price > 0
    ]
    if len(swap_prices) < 2:
        return None

    t_min = swap_prices[0][0]
    t_max = swap_prices[-1][0]
    span = t_max - t_min
    if span <= 0:
        # 所有事件同一时间：做一个单独的桶
        span = 1.0
    bucket_width = span / min(num_buckets, len(swap_prices))

    buckets: list[list[float]] = [[] for _ in range(min(num_buckets, len(swap_prices)))]
    for t, price in swap_prices:
        idx = min(int((t - t_min) / bucket_width), len(buckets) - 1)
        buckets[idx].append(price)

    # 只保留非空桶
    ohlc: list[dict] = []
    base_t = t_min
    for i, bucket in enumerate(buckets):
        if not bucket:
            continue
        ohlc.append(
            {
                "time": base_t + (i + 0.5) * bucket_width,
                "open": bucket[0],
                "high": max(bucket),
                "low": min(bucket),
                "close": bucket[-1],
            }
        )
    return ohlc if ohlc else None


def plot_candlestick(
    result: SimulationResult,
    output_dir: str | Path,
    num_buckets: int = 30,
) -> Path | None:
    """绘制 K 线（OHLC 蜡烛图）价格走势。

    将 swap 事件的现货价格按时间窗口聚合为 OHLC 数据，用 matplotlib 的
    Rectangle 和 Line2D 手绘蜡烛实体和影线，不依赖 mplfinance。

    Returns:
        图表文件路径；swap 事件不足 2 个时返回 None。
    """
    ohlc = _build_ohlc_buckets(result.records, num_buckets)
    if not ohlc:
        return None

    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, candle in enumerate(ohlc):
        open_p = candle["open"]
        close_p = candle["close"]
        high_p = candle["high"]
        low_p = candle["low"]

        # 影线（从最低到最高）
        ax.plot(
            [i, i],
            [low_p, high_p],
            color="#334155",
            linewidth=1,
            solid_capstyle="round",
        )

        # 实体（从开盘到收盘）
        body_bottom = min(open_p, close_p)
        body_height = abs(close_p - open_p)
        color = "#26a69a" if close_p >= open_p else "#ef5350"  # 绿涨红跌
        rect = mpatches.Rectangle(
            (i - 0.4, body_bottom),
            0.8,
            max(body_height, 0.001),
            facecolor=color,
            edgecolor=color,
            linewidth=0.5,
        )
        ax.add_patch(rect)

    # x 轴标签用时间戳
    tick_indices = range(0, len(ohlc), max(1, len(ohlc) // 10))
    ax.set_xticks(list(tick_indices))
    ax.set_xticklabels(
        [f"{ohlc[i]['time']:.1f}" for i in tick_indices], rotation=30, ha="right", fontsize=8
    )
    ax.set_title("Price Candlestick (K-Line)")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Price (Y per X)")
    ax.grid(alpha=0.25)

    return _save_figure(Path(output_dir) / "candlestick.png")


# ── 新增图表：滑点-交易量散点图 ──────────────────────────────────────────


def plot_slippage_volume(
    records: list,
    output_dir: str | Path,
) -> Path | None:
    """绘制滑点与交易量关系的散点图。

    x 轴为交易金额（amount_in），y 轴为滑点百分比。按交易方向着色，
    便于观察大额交易与滑点之间的非线性关系。

    Returns:
        图表文件路径；无有效交易事件时返回 None。
    """
    trade_data = [
        (r.amount_in, r.slippage_pct, r.direction)
        for r in records
        if r.event_type in {"swap", "arbitrage"} and r.slippage_pct is not None and r.amount_in is not None
    ]
    if not trade_data:
        return None

    # 按方向分两组
    x_to_y_data = [(amt, slip) for amt, slip, d in trade_data if d == "x_to_y"]
    y_to_x_data = [(amt, slip) for amt, slip, d in trade_data if d == "y_to_x"]

    fig, ax = plt.subplots(figsize=(8, 5))

    if x_to_y_data:
        xs, ys = zip(*x_to_y_data)
        ax.scatter(xs, ys, c="#2563eb", alpha=0.7, edgecolors="white", linewidth=0.5, label="X → Y")

    if y_to_x_data:
        xs, ys = zip(*y_to_x_data)
        ax.scatter(xs, ys, c="#dc2626", alpha=0.7, edgecolors="white", linewidth=0.5, marker="^", label="Y → X")

    ax.set_xlabel("Trade Amount (amount_in)")
    ax.set_ylabel("Slippage (%)")
    ax.set_title("Slippage vs Trade Volume")
    ax.legend()
    ax.grid(alpha=0.25)

    return _save_figure(Path(output_dir) / "slippage_volume.png")


# ── 新增图表：多场景对比分组柱状图 ────────────────────────────────────────


def plot_multi_scenario_comparison(
    scenario_results: dict[str, SimulationResult],
    output_dir: str | Path,
) -> Path | None:
    """绘制多场景关键指标对比的分组柱状图。

    对每个场景提取 avg slippage、impermanent loss、total fees (in Y)、
    final pool value 四个指标，以 2x2 子图展示，避免不同量级挤在同一坐标轴。

    Args:
        scenario_results: 场景名称 → SimulationResult 的映射。
        output_dir: 图表输出目录。

    Returns:
        图表文件路径；场景数不足 2 时返回 None。
    """
    if len(scenario_results) < 2:
        return None

    metric_names = [
        "Avg Slippage (%)",
        "Imp. Loss (%)",
        "Total Fees (Y)",
        "Pool Value (Y)",
    ]
    scenarios = list(scenario_results.keys())
    num_scenarios = len(scenarios)
    colors = plt.cm.Set2(np.linspace(0, 1, max(num_scenarios, 1)))

    data: list[list[float]] = [[], [], [], []]
    for name in scenarios:
        summary = scenario_results[name].summary
        data[0].append(float(summary.average_slippage_pct or 0.0))
        data[1].append(float(summary.impermanent_loss_pct or 0.0))
        data[2].append(float(summary.total_fees_in_y))
        data[3].append(float(summary.final_pool_value_in_y))

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    width = 0.8 / num_scenarios

    for idx, (metric_name, metric_data) in enumerate(zip(metric_names, data)):
        ax = axes[idx]
        x = np.arange(1)

        for scenario_index, name in enumerate(scenarios):
            offset = (scenario_index - (num_scenarios - 1) / 2) * width
            ax.bar(
                x + offset,
                metric_data[scenario_index],
                width,
                label=name,
                color=colors[scenario_index],
                edgecolor="white",
                linewidth=0.5,
            )

        data_min = min(metric_data)
        data_max = max(metric_data)
        if data_max != data_min:
            margin = (data_max - data_min) * 0.12
            ax.set_ylim(data_min - margin, data_max + margin)
        elif data_max > 0:
            ax.set_ylim(0, data_max * 1.15)

        for scenario_index, value in enumerate(metric_data):
            offset = (scenario_index - (num_scenarios - 1) / 2) * width
            ax.text(
                float(x[0] + offset),
                value,
                f"{value:.2f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=8,
            )

        ax.set_xticks(x)
        ax.set_xticklabels([metric_name], fontsize=10)
        ax.set_title(metric_name)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.25)

    return _save_figure(Path(output_dir) / "multi_scenario_comparison.png")


def generate_result_plots(result: SimulationResult, output_dir: str | Path) -> dict[str, Path]:
    """生成全部标准结果图，并过滤掉没有数据的图表。"""
    plots = {
        "pool_spot_price": plot_pool_price(result.records, output_dir),
        "pool_reserves": plot_pool_reserves(result.records, output_dir),
        "swap_slippage": plot_slippage(result.records, output_dir),
        "cumulative_fees": plot_cumulative_fees(result.records, output_dir),
        "impermanent_loss": plot_impermanent_loss(result, output_dir),
        "user_total_pnl": plot_user_pnl(result, output_dir),
        # ── 新增图表 ──
        "candlestick": plot_candlestick(result, output_dir),
        "slippage_volume": plot_slippage_volume(result.records, output_dir),
    }
    return {name: path for name, path in plots.items() if path is not None}

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

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
    """绘制所有 swap 事件的滑点变化图。"""
    swap_records = [record for record in records if record.slippage_pct is not None]
    if not swap_records:
        return None

    timestamps = [record.timestamp for record in swap_records]
    slippage = [record.slippage_pct for record in swap_records]

    plt.figure(figsize=(8, 4.5))
    plt.plot(timestamps, slippage, marker="o", color="#b45309", linewidth=2)
    plt.title("Swap Slippage")
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
    swap_records = [record for record in records if record.event_type == "swap"]
    if not swap_records:
        return None

    timestamps = []
    cumulative = []
    total = 0.0
    for record in swap_records:
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


def generate_result_plots(result: SimulationResult, output_dir: str | Path) -> dict[str, Path]:
    """生成全部标准结果图，并过滤掉没有数据的图表。"""
    plots = {
        "pool_spot_price": plot_pool_price(result.records, output_dir),
        "pool_reserves": plot_pool_reserves(result.records, output_dir),
        "swap_slippage": plot_slippage(result.records, output_dir),
        "cumulative_fees": plot_cumulative_fees(result.records, output_dir),
        "impermanent_loss": plot_impermanent_loss(result, output_dir),
        "user_total_pnl": plot_user_pnl(result, output_dir),
    }
    return {name: path for name, path in plots.items() if path is not None}

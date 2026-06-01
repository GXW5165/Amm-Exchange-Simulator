from __future__ import annotations

from dataclasses import dataclass

from src.domain.pool import Pool
from src.domain.user import User

from .impermanent_loss import impermanent_loss_amount_in_y, impermanent_loss_pct
from .lp_metrics import compute_lp_metrics
from .pnl import UserPnL, summarize_user_pnl
from .pool_depth import compute_max_trade_at_2pct
from .record import EventRecord
from .slippage import average_slippage_pct


@dataclass
class SimulationSummary:
    """仿真摘要指标。

    该对象聚合事件数量、手续费、滑点、无常损失、资金池价值和用户收益，
    是 CLI 输出、JSON 导出和 Web 摘要面板的统一数据来源。
    """

    total_events: int
    swap_events: int
    liquidity_events: int
    total_fees: float
    total_fees_in_y: float
    average_slippage_pct: float | None
    max_slippage_pct: float | None
    impermanent_loss_pct: float | None
    impermanent_loss_amount_in_y: float | None
    final_pool_value_in_y: float
    initial_pool_value_at_final_price_in_y: float
    user_pnl: dict[str, UserPnL]
    # ── 新增分析指标 ──
    lp_annualized_returns: dict[str, float | None] | None = None
    pool_depth_at_2pct: float | None = None
    time_span_days: float = 0.0


def summarize_records(
    records: list[EventRecord],
    initial_pool: Pool,
    current_pool: Pool,
    initial_users: dict[str, User],
    current_users: dict[str, User],
) -> SimulationSummary:
    """根据事件记录和初末状态计算汇总指标。"""
    swap_events = 0
    liquidity_events = 0
    total_fees = 0.0
    total_fees_in_y = 0.0
    slippage_values: list[float | None] = []

    for record in records:
        if record.event_type == "swap":
            swap_events += 1
        elif record.event_type in {"add_liquidity", "remove_liquidity"}:
            liquidity_events += 1

        fee = float(record.fee or 0.0)
        total_fees += fee
        if record.event_type == "swap" and fee:
            # 不同交易方向的 fee 单位不同；汇总时统一折算成 Token Y，便于和总价值/PnL 比较。
            if record.direction == "x_to_y":
                price = record.spot_price_before or record.spot_price or current_pool.spot_price
                total_fees_in_y += fee * price
            else:
                total_fees_in_y += fee
        slippage_values.append(record.slippage_pct)

    filtered_slippage = [value for value in slippage_values if value is not None]
    max_slippage = max(filtered_slippage) if filtered_slippage else None
    current_price = current_pool.spot_price
    initial_price = initial_pool.spot_price
    il_pct = impermanent_loss_pct(initial_price, current_price)
    # 用最终价格重估初始池子，得到”如果不做市而单纯持有”的基准价值。
    initial_pool_value_at_final_price = initial_pool.reserve_x * current_price + initial_pool.reserve_y
    final_pool_value = current_pool.reserve_x * current_price + current_pool.reserve_y

    # ── 新增：仿真时间跨度 ──
    if records:
        timestamps = [r.timestamp for r in records]
        time_span_days = ((max(timestamps) - min(timestamps)) / 24.0) if len(timestamps) >= 2 else 0.0
    else:
        time_span_days = 0.0

    # ── 新增：池深度指标 ──
    pool_depth = compute_max_trade_at_2pct(current_pool)

    # ── 新增：LP 综合指标 ──
    lp_metrics = compute_lp_metrics(
        records=records,
        initial_pool=initial_pool,
        current_pool=current_pool,
        initial_users=initial_users,
        current_users=current_users,
        price_y_per_x=current_price,
        initial_price_y_per_x=initial_price,
        total_fees_in_y=total_fees_in_y,
    )
    lp_annualized = {
        uid: metrics.lp_annualized_return_pct for uid, metrics in lp_metrics.items()
    }
    user_fee_income = {uid: m.fee_income_in_y for uid, m in lp_metrics.items()}
    user_il_loss = {uid: m.il_loss_amount_in_y for uid, m in lp_metrics.items()}

    return SimulationSummary(
        total_events=len(records),
        swap_events=swap_events,
        liquidity_events=liquidity_events,
        total_fees=total_fees,
        total_fees_in_y=total_fees_in_y,
        average_slippage_pct=average_slippage_pct(slippage_values),
        max_slippage_pct=max_slippage,
        impermanent_loss_pct=il_pct,
        impermanent_loss_amount_in_y=impermanent_loss_amount_in_y(initial_pool_value_at_final_price, il_pct),
        final_pool_value_in_y=final_pool_value,
        initial_pool_value_at_final_price_in_y=initial_pool_value_at_final_price,
        # ── 新增指标 ──
        lp_annualized_returns=lp_annualized if any(v is not None for v in lp_annualized.values()) else None,
        pool_depth_at_2pct=pool_depth,
        time_span_days=time_span_days,
        user_pnl=summarize_user_pnl(
            initial_users=initial_users,
            current_users=current_users,
            pool=current_pool,
            price_y_per_x=current_price,
            initial_price_y_per_x=initial_price,
            total_fees_in_y=total_fees_in_y,
            initial_pool=initial_pool,
            user_fee_income=user_fee_income,
            user_il_loss=user_il_loss,
        ),
    )

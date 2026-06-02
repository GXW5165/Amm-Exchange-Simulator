from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from src.analytics.impermanent_loss import impermanent_loss_amount_in_y, impermanent_loss_pct
from src.analytics.pnl import lp_position_value_in_y
from src.analytics.record import EventRecord
from src.domain.pool import Pool
from src.domain.user import User


@dataclass
class LpMetrics:
    """单用户 LP 做市综合指标。

    所有金额统一折算为 Token Y 计价。手续费为 LP 按份额比例获得的 swap 手续费；
    无常损失为按最终价格计算的百分比损失乘以用户 LP 仓位价值。

    fee_vs_il_net_in_y 为正表示手续费收入覆盖了无常损失，为负表示做市净亏损。
    """

    user_id: str
    initial_lp_value_in_y: float
    final_lp_value_in_y: float
    lp_return_pct: float
    lp_annualized_return_pct: float | None
    fee_income_in_y: float
    il_loss_amount_in_y: float | None
    fee_vs_il_net_in_y: float | None
    time_span_days: float


def compute_fee_income_per_user(
    records: list[EventRecord],
    current_users: dict[str, User],
    pool: Pool,
    price_y_per_x: float,
    initial_users: dict[str, User] | None = None,
) -> dict[str, float]:
    """按事件发生时的 LP 份额比例分配每次 swap 事件产生的手续费收入。

    遍历事件记录时维护一份 LP 份额快照。swap 事件使用交易发生前的
    快照分配手续费，add/remove 事件再更新快照，避免后加入的 LP 获得
    加入前的手续费，或已经退出的 LP 丢失退出前的收益。

    Args:
        records: 仿真事件记录列表。
        current_users: 仿真结束时的用户字典，作为缺少初始快照时的兜底。
        pool: 最终资金池状态，保留该参数以兼容旧调用方。
        price_y_per_x: 最终现货价格（用于手续费折算）。
        initial_users: 仿真开始时的用户字典，用于还原历史 LP 份额。

    Returns:
        user_id → 累计手续费收入（Token Y 计价）的映射。
    """
    fee_income: dict[str, float] = {}
    lp_shares_by_user = {
        uid: user.lp_shares
        for uid, user in (initial_users or current_users).items()
        if user.lp_shares > 0.0
    }

    for record in records:
        if record.event_type in {"add_liquidity", "remove_liquidity"}:
            if record.lp_shares_after is not None:
                if record.lp_shares_after > 0.0:
                    lp_shares_by_user[record.user_id] = record.lp_shares_after
                else:
                    lp_shares_by_user.pop(record.user_id, None)
            continue

        if record.event_type != "swap":
            continue
        fee = float(record.fee or 0.0)
        if fee <= 0.0:
            continue

        # 手续费以 input 资产单位收取；统一折算为 Token Y
        if record.direction == "x_to_y":
            price = record.spot_price_before or price_y_per_x
            fee_in_y = fee * (price if isfinite(price) and price > 0 else price_y_per_x)
        else:
            fee_in_y = fee  # y_to_x 的 fee 已经是 Token Y 单位

        total_shares = record.lp_total_shares
        if total_shares <= 0.0:
            continue

        for uid, lp_shares in lp_shares_by_user.items():
            if lp_shares <= 0.0:
                continue
            share_ratio = lp_shares / total_shares
            fee_income[uid] = fee_income.get(uid, 0.0) + fee_in_y * share_ratio

    return fee_income


def compute_lp_metrics(
    records: list[EventRecord],
    initial_pool: Pool,
    current_pool: Pool,
    initial_users: dict[str, User],
    current_users: dict[str, User],
    price_y_per_x: float,
    initial_price_y_per_x: float,
    total_fees_in_y: float,
    time_unit_in_days: float = 1.0 / 24.0,
) -> dict[str, LpMetrics]:
    """为每个持有或曾经持有 LP 的用户生成绩效指标。

    计算流程：
        1. 从事件时间戳推算仿真持续天数。
        2. 按用户 LP 份额比例跟踪手续费收入。
        3. 对每个用户计算 LP 仓位的初值和终值、收益率、年化收益率。
        4. 计算无常损失金额和手续费 vs 无常损失的净收支。

    Args:
        records: 仿真事件记录列表。
        initial_pool: 初始资金池。
        current_pool: 最终资金池。
        initial_users: 初始用户字典。
        current_users: 最终用户字典。
        price_y_per_x: 最终现货价格。
        initial_price_y_per_x: 初始现货价格。
        total_fees_in_y: 累计手续费（已折算为 Token Y），用于交叉校验。
        time_unit_in_days: 时间戳单位到天的转换系数，默认 1/24（时间戳为小时）。

    Returns:
        user_id → LpMetrics 的映射。未持有 LP 份额的用户不会出现在结果中。
    """
    # 计算仿真时间跨度（天）
    if records:
        timestamps = [r.timestamp for r in records]
        time_span = max(timestamps) - min(timestamps)
    else:
        time_span = 0.0
    time_span_days = time_span * time_unit_in_days

    # 按份额比例跟踪手续费
    fee_income = compute_fee_income_per_user(
        records=records,
        current_users=current_users,
        pool=current_pool,
        price_y_per_x=price_y_per_x,
        initial_users=initial_users,
    )

    # 全局无常损失百分比
    il_pct = impermanent_loss_pct(initial_price_y_per_x, price_y_per_x)

    result: dict[str, LpMetrics] = {}

    # 遍历所有曾经或当前持有 LP 份额的用户
    user_ids = set(initial_users) | set(current_users)
    for uid in sorted(user_ids):
        init_user = initial_users.get(uid, User(user_id=uid))
        curr_user = current_users.get(uid, User(user_id=uid))

        # 跳过从未持有 LP 的用户
        if init_user.lp_shares <= 0.0 and curr_user.lp_shares <= 0.0:
            continue

        init_price = (
            initial_price_y_per_x
            if isfinite(initial_price_y_per_x) and initial_price_y_per_x > 0
            else price_y_per_x
        )

        init_lp_val = lp_position_value_in_y(initial_pool, init_user, init_price)
        final_lp_val = lp_position_value_in_y(current_pool, curr_user, price_y_per_x)

        # LP 收益率百分比
        lp_return_pct = ((final_lp_val / init_lp_val) - 1.0) * 100.0 if init_lp_val > 0.0 else 0.0

        # 年化收益率 (APY 公式)
        annualized: float | None = None
        if init_lp_val > 0.0 and time_span_days > 0.0:
            total_return_ratio = final_lp_val / init_lp_val
            if total_return_ratio > 0.0:
                annualized = (total_return_ratio ** (365.0 / time_span_days) - 1.0) * 100.0

        # 用户手续费收入
        user_fee = fee_income.get(uid, 0.0)

        # 用户 LP 仓位的无常损失金额
        il_amount: float | None = None
        if il_pct is not None:
            il_amount = impermanent_loss_amount_in_y(init_lp_val, il_pct)

        # 手续费净收益 vs 无常损失
        fee_vs_il: float | None = None
        if il_amount is not None:
            fee_vs_il = user_fee - il_amount

        result[uid] = LpMetrics(
            user_id=uid,
            initial_lp_value_in_y=init_lp_val,
            final_lp_value_in_y=final_lp_val,
            lp_return_pct=lp_return_pct,
            lp_annualized_return_pct=annualized,
            fee_income_in_y=user_fee,
            il_loss_amount_in_y=il_amount,
            fee_vs_il_net_in_y=fee_vs_il,
            time_span_days=time_span_days,
        )

    return result

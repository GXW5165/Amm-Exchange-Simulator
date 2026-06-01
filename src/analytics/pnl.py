from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from src.domain.pool import Pool
from src.domain.user import User


@dataclass
class UserPnL:
    """用户收益摘要。

    所有价值统一折算为 Token Y 计价，既包含钱包余额，也包含用户当前 LP
    份额对应的池内资产价值，便于横向比较不同用户的总收益。
    """

    user_id: str
    initial_value_in_y: float
    final_wallet_value_in_y: float
    final_total_value_in_y: float
    wallet_pnl_in_y: float
    total_pnl_in_y: float
    lp_position_value_in_y: float
    initial_value_at_initial_price_in_y: float = 0.0
    hold_value_at_final_price_in_y: float = 0.0
    lp_vs_hold_pnl_in_y: float = 0.0
    fee_gain_estimate_in_y: float = 0.0


def portfolio_value_in_y(user: User, price_y_per_x: float) -> float:
    """计算用户钱包资产的 Token Y 计价价值。"""
    # 统一用 Token Y 计价，便于把钱包资产、LP 仓位和手续费收益放在同一张表里比较。
    return user.balance_x * price_y_per_x + user.balance_y


def lp_position_value_in_y(pool: Pool, user: User, price_y_per_x: float) -> float:
    """计算用户 LP 仓位在当前池子和价格下的 Token Y 计价价值。"""
    if pool.total_lp_shares <= 0 or user.lp_shares <= 0:
        return 0.0
    # LP 份额不是单独资产余额，而是对当前池子 reserve_x/reserve_y 的比例索取权。
    share_ratio = user.lp_shares / pool.total_lp_shares
    amount_x = pool.reserve_x * share_ratio
    amount_y = pool.reserve_y * share_ratio
    return amount_x * price_y_per_x + amount_y


def summarize_user_pnl(
    initial_users: dict[str, User],
    current_users: dict[str, User],
    pool: Pool,
    price_y_per_x: float,
    initial_price_y_per_x: float | None = None,
    total_fees_in_y: float = 0.0,
) -> dict[str, UserPnL]:
    """按用户生成收益表。

    initial_users 和 current_users 允许用户集合不完全一致，这样后续扩展动态创建
    用户时也能正常统计；当前项目主要用于比较交易者和 LP 在仿真后的价值变化。
    """
    summary: dict[str, UserPnL] = {}
    initial_price = price_y_per_x if initial_price_y_per_x is None else initial_price_y_per_x
    user_ids = set(initial_users) | set(current_users)
    for user_id in sorted(user_ids):
        initial_user = deepcopy(initial_users.get(user_id, User(user_id=user_id)))
        current_user = deepcopy(current_users.get(user_id, User(user_id=user_id)))
        initial_value = portfolio_value_in_y(initial_user, price_y_per_x)
        initial_value_at_initial_price = portfolio_value_in_y(initial_user, initial_price)
        hold_value_at_final_price = portfolio_value_in_y(initial_user, price_y_per_x)
        final_wallet_value = portfolio_value_in_y(current_user, price_y_per_x)
        lp_value = lp_position_value_in_y(pool, current_user, price_y_per_x)
        final_total_value = final_wallet_value + lp_value
        # 手续费实际沉淀在池子储备里，这里按当前 LP 份额比例给出可解释的收益估算。
        lp_share_ratio = current_user.lp_shares / pool.total_lp_shares if pool.total_lp_shares > 0 else 0.0
        fee_gain_estimate = total_fees_in_y * lp_share_ratio
        summary[user_id] = UserPnL(
            user_id=user_id,
            initial_value_in_y=initial_value,
            final_wallet_value_in_y=final_wallet_value,
            final_total_value_in_y=final_total_value,
            wallet_pnl_in_y=final_wallet_value - initial_value,
            total_pnl_in_y=final_total_value - initial_value,
            lp_position_value_in_y=lp_value,
            initial_value_at_initial_price_in_y=initial_value_at_initial_price,
            hold_value_at_final_price_in_y=hold_value_at_final_price,
            lp_vs_hold_pnl_in_y=final_total_value - hold_value_at_final_price,
            fee_gain_estimate_in_y=fee_gain_estimate,
        )
    return summary

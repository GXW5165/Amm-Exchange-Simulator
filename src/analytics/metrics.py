from __future__ import annotations

from src.domain.pool import Pool
from src.domain.user import User

from .impermanent_loss import impermanent_loss_pct
from .pnl import UserPnL, summarize_user_pnl
from .slippage import calculate_slippage_pct


class MetricsCalculator:
    """指标计算模块：为仿真层提供滑点、无常损失和用户收益的统一入口。"""

    def calc_slippage_pct(self, theoretical_price: float, execution_price: float | None) -> float | None:
        """计算单笔交易滑点百分比。"""
        return calculate_slippage_pct(theoretical_price, execution_price)

    def calc_impermanent_loss_pct(self, initial_price: float, current_price: float) -> float | None:
        """计算从初始价格到当前价格的无常损失百分比。"""
        return impermanent_loss_pct(initial_price, current_price)

    def summarize_user_pnl(
        self,
        initial_users: dict[str, User],
        current_users: dict[str, User],
        pool: Pool,
        price_y_per_x: float,
        initial_price_y_per_x: float | None = None,
        total_fees_in_y: float = 0.0,
    ) -> dict[str, UserPnL]:
        """生成用户收益表。"""
        return summarize_user_pnl(
            initial_users,
            current_users,
            pool,
            price_y_per_x,
            initial_price_y_per_x=initial_price_y_per_x,
            total_fees_in_y=total_fees_in_y,
        )

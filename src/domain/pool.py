from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Pool:
    """资金池状态对象：只保存储备、手续费率和 LP 总份额等核心状态。"""

    reserve_x: float
    reserve_y: float
    fee_rate: float = 0.003
    total_lp_shares: float = 0.0

    @property
    def spot_price(self) -> float:
        if self.reserve_x <= 0:
            return float("inf")
        return self.reserve_y / self.reserve_x

    @property
    def invariant(self) -> float:
        return self.reserve_x * self.reserve_y

    def add_liquidity(self, amount_x: float, amount_y: float) -> tuple[float, float, float]:
        # 兼容旧接口：实际业务逻辑委托给流动性管理模块。
        from src.amm.liquidity_manager import LiquidityManager

        result = LiquidityManager(self).add_liquidity(amount_x, amount_y)
        return result.consumed_x, result.consumed_y, result.minted_shares

    def remove_liquidity(self, lp_share: float) -> tuple[float, float]:
        # 兼容旧接口：实际业务逻辑委托给流动性管理模块。
        from src.amm.liquidity_manager import LiquidityManager

        result = LiquidityManager(self).remove_liquidity(lp_share)
        return result.amount_x, result.amount_y

    def swap(self, direction: str, amount_in: float) -> tuple[float, float]:
        # 兼容旧接口：实际交易逻辑委托给 AMM 核心模块。
        from src.amm.engine import AMMEngine

        result = AMMEngine(self).swap(direction, amount_in)
        return result.amount_out, result.fee

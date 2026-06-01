from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass
class Pool:
    """资金池状态对象：只保存储备、手续费率和 LP 总份额等核心状态。"""

    reserve_x: float
    reserve_y: float
    fee_rate: float = 0.003
    total_lp_shares: float = 0.0

    def __post_init__(self) -> None:
        """校验资金池参数，并在已有双边储备时初始化 LP 总份额。"""
        if self.reserve_x < 0 or self.reserve_y < 0:
            raise ValueError("Pool reserves must be non-negative")
        if not 0 <= self.fee_rate < 1:
            raise ValueError("Fee rate must satisfy 0 <= fee_rate < 1")
        if self.total_lp_shares < 0:
            raise ValueError("Total LP shares must be non-negative")
        if self.reserve_x > 0 and self.reserve_y > 0 and self.total_lp_shares == 0:
            self.total_lp_shares = sqrt(self.reserve_x * self.reserve_y)

    @property
    def spot_price(self) -> float:
        """返回现货价格，单位为 Token Y / Token X。"""
        if self.reserve_x <= 0:
            return float("inf")
        return self.reserve_y / self.reserve_x

    @property
    def spot_price_y_per_x(self) -> float:
        """spot_price 的显式命名别名，便于报告中说明计价单位。"""
        return self.spot_price

    @property
    def invariant(self) -> float:
        """返回恒定乘积指标 k = reserve_x * reserve_y。"""
        return self.reserve_x * self.reserve_y

    def add_liquidity(self, amount_x: float, amount_y: float) -> tuple[float, float, float]:
        """兼容旧接口的添加流动性方法。

        返回实际消耗的 X、Y 和新增 LP 份额；具体规则由 LiquidityManager 实现。
        """
        # 兼容旧接口：实际业务逻辑委托给流动性管理模块。
        from src.amm.liquidity_manager import LiquidityManager

        result = LiquidityManager(self).add_liquidity(amount_x, amount_y)
        return result.consumed_x, result.consumed_y, result.minted_shares

    def remove_liquidity(self, lp_share: float) -> tuple[float, float]:
        """兼容旧接口的移除流动性方法，返回赎回的 X、Y 数量。"""
        # 兼容旧接口：实际业务逻辑委托给流动性管理模块。
        from src.amm.liquidity_manager import LiquidityManager

        result = LiquidityManager(self).remove_liquidity(lp_share)
        return result.amount_x, result.amount_y

    def swap(self, direction: str, amount_in: float) -> tuple[float, float]:
        """兼容旧接口的兑换方法，返回输出数量和手续费。"""
        # 兼容旧接口：实际交易逻辑委托给 AMM 核心模块。
        from src.amm.engine import AMMEngine

        result = AMMEngine(self).swap(direction, amount_in)
        return result.amount_out, result.fee

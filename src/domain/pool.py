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


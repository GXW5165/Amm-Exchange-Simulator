from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import InsufficientBalanceError
from src.domain.pool import Pool


@dataclass(frozen=True)
class SwapQuote:
    """交易报价结果：只描述本次兑换结果，不修改资金池状态。"""

    direction: str
    amount_in: float
    amount_out: float
    fee: float
    execution_price: float


@dataclass(frozen=True)
class SwapResult:
    """交易执行结果：包含成交数据和交易后的资金池快照。"""

    direction: str
    amount_in: float
    amount_out: float
    fee: float
    execution_price: float
    reserve_x: float
    reserve_y: float


class AMMEngine:
    """AMM 核心模块：封装恒定乘积模型下的报价与兑换逻辑。"""

    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    def quote(self, direction: str, amount_in: float) -> SwapQuote:
        if amount_in <= 0:
            raise InsufficientBalanceError("Swap amount must be positive")

        # 概要设计中的交易算法：dx' = dx * (1 - f)，定价只使用扣费后的有效输入。
        fee = amount_in * self.pool.fee_rate
        effective_in = amount_in - fee
        k = self.pool.invariant

        if direction == "x_to_y":
            new_reserve_x = self.pool.reserve_x + effective_in
            amount_out = self.pool.reserve_y - (k / new_reserve_x)
        elif direction == "y_to_x":
            new_reserve_y = self.pool.reserve_y + effective_in
            amount_out = self.pool.reserve_x - (k / new_reserve_y)
        else:
            raise ValueError(f"Unsupported swap direction: {direction}")

        execution_price = amount_out / amount_in
        return SwapQuote(
            direction=direction,
            amount_in=amount_in,
            amount_out=amount_out,
            fee=fee,
            execution_price=execution_price,
        )

    def swap(self, direction: str, amount_in: float) -> SwapResult:
        quote = self.quote(direction, amount_in)

        # 注意：池子实际增加的是用户输入总额 amount_in，手续费仍留在池中。
        if direction == "x_to_y":
            self.pool.reserve_x += amount_in
            self.pool.reserve_y -= quote.amount_out
        elif direction == "y_to_x":
            self.pool.reserve_y += amount_in
            self.pool.reserve_x -= quote.amount_out
        else:
            raise ValueError(f"Unsupported swap direction: {direction}")

        return SwapResult(
            direction=quote.direction,
            amount_in=quote.amount_in,
            amount_out=quote.amount_out,
            fee=quote.fee,
            execution_price=quote.execution_price,
            reserve_x=self.pool.reserve_x,
            reserve_y=self.pool.reserve_y,
        )

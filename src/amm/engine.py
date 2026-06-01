from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import InsufficientBalanceError
from src.domain.pool import Pool


@dataclass(frozen=True)
class SwapQuote:
    """交易报价结果：只描述本次兑换结果，不修改资金池状态。"""

    direction: str
    amount_in: float
    effective_amount_in: float
    amount_out: float
    fee: float
    execution_price: float
    theoretical_price: float
    slippage_pct: float | None
    reserve_x_before: float
    reserve_y_before: float
    reserve_x_after: float
    reserve_y_after: float
    spot_price_before: float
    spot_price_after: float


@dataclass(frozen=True)
class SwapResult:
    """交易执行结果：包含成交数据和交易后的资金池快照。"""

    direction: str
    amount_in: float
    effective_amount_in: float
    amount_out: float
    fee: float
    execution_price: float
    theoretical_price: float
    slippage_pct: float | None
    reserve_x: float
    reserve_y: float
    reserve_x_before: float
    reserve_y_before: float
    spot_price_before: float
    spot_price_after: float


class AMMEngine:
    """AMM 核心模块：封装恒定乘积模型下的报价与兑换逻辑。"""

    def __init__(self, pool: Pool) -> None:
        """绑定一个资金池实例，后续 quote 只读池状态，swap 会修改池状态。"""
        self.pool = pool

    def quote(self, direction: str, amount_in: float) -> SwapQuote:
        """计算兑换报价但不修改资金池。

        direction 为 x_to_y 时，输入 Token X、输出 Token Y；反向同理。
        报价使用扣除手续费后的 effective_in 代入 x*y=k 公式，但返回的
        reserve_*_after 按真实池状态计算，即用户输入总额进入池子。
        """
        if amount_in <= 0:
            raise InsufficientBalanceError("Swap amount must be positive")
        if self.pool.reserve_x <= 0 or self.pool.reserve_y <= 0:
            raise InsufficientBalanceError("Pool reserves must be positive before swapping")

        # AMM 交易有两个输入口径：
        # 1. effective_in 进入恒定乘积公式，用来计算用户能换出多少资产。
        # 2. amount_in 全额进入池子，其中 fee 留在池内，等价于 LP 份额持有人共享手续费收益。
        fee = amount_in * self.pool.fee_rate
        effective_in = amount_in - fee
        k = self.pool.invariant
        reserve_x_before = self.pool.reserve_x
        reserve_y_before = self.pool.reserve_y
        spot_price_before = self.pool.spot_price

        if direction == "x_to_y":
            new_reserve_x = self.pool.reserve_x + effective_in
            amount_out = self.pool.reserve_y - (k / new_reserve_x)
            reserve_x_after = self.pool.reserve_x + amount_in
            reserve_y_after = self.pool.reserve_y - amount_out
            theoretical_price = spot_price_before
        elif direction == "y_to_x":
            new_reserve_y = self.pool.reserve_y + effective_in
            amount_out = self.pool.reserve_x - (k / new_reserve_y)
            reserve_x_after = self.pool.reserve_x - amount_out
            reserve_y_after = self.pool.reserve_y + amount_in
            # y_to_x 的成交价单位是 X per Y，因此理论价格也必须取池内价格的倒数。
            theoretical_price = 1 / spot_price_before if spot_price_before not in (0, float("inf")) else float("inf")
        else:
            raise ValueError(f"Unsupported swap direction: {direction}")

        # execution_price 使用 amount_out / amount_in，表示用户实际每投入 1 单位输入资产换出的输出资产。
        slippage_pct = None
        execution_price = amount_out / amount_in
        if theoretical_price > 0 and theoretical_price != float("inf"):
            slippage_pct = abs(execution_price - theoretical_price) / theoretical_price * 100
        spot_price_after = reserve_y_after / reserve_x_after if reserve_x_after > 0 else float("inf")
        return SwapQuote(
            direction=direction,
            amount_in=amount_in,
            effective_amount_in=effective_in,
            amount_out=amount_out,
            fee=fee,
            execution_price=execution_price,
            theoretical_price=theoretical_price,
            slippage_pct=slippage_pct,
            reserve_x_before=reserve_x_before,
            reserve_y_before=reserve_y_before,
            reserve_x_after=reserve_x_after,
            reserve_y_after=reserve_y_after,
            spot_price_before=spot_price_before,
            spot_price_after=spot_price_after,
        )

    def swap(self, direction: str, amount_in: float) -> SwapResult:
        """执行兑换并更新资金池储备。"""
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
            effective_amount_in=quote.effective_amount_in,
            amount_out=quote.amount_out,
            fee=quote.fee,
            execution_price=quote.execution_price,
            theoretical_price=quote.theoretical_price,
            slippage_pct=quote.slippage_pct,
            reserve_x=self.pool.reserve_x,
            reserve_y=self.pool.reserve_y,
            reserve_x_before=quote.reserve_x_before,
            reserve_y_before=quote.reserve_y_before,
            spot_price_before=quote.spot_price_before,
            spot_price_after=quote.spot_price_after,
        )

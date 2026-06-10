from __future__ import annotations

from dataclasses import dataclass

from src.domain.pool import Pool
from src.domain.pricing import calculate_slippage_pct


@dataclass(frozen=True)
class ArbitrageResult:
    """套利报价或执行结果。"""

    direction: str
    amount_in: float
    amount_out: float
    fee: float
    profit: float
    execution_price: float
    market_price: float
    slippage_pct: float | None
    reserve_x_before: float
    reserve_y_before: float
    reserve_x_after: float
    reserve_y_after: float
    spot_price_before: float
    spot_price_after: float
    arbitrage_executed: bool


class ArbitrageEngine:
    """Detect and execute AMM arbitrage against an external market price."""

    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    def check_arbitrage_opportunity(self, market_price: float) -> tuple[bool, str, float]:
        """Return whether pool/market price deviation is large enough to trade."""
        if self.pool.reserve_x <= 0 or self.pool.reserve_y <= 0:
            return (False, "", 0.0)
        pool_price = self.pool.spot_price
        if market_price <= 0 or pool_price <= 0:
            return (False, "", 0.0)

        price_diff = abs(pool_price - market_price)
        min_profit_threshold = self.pool.fee_rate * market_price
        if price_diff < min_profit_threshold:
            return (False, "", 0.0)

        if pool_price > market_price:
            return (True, "x_to_y", price_diff - min_profit_threshold)
        return (True, "y_to_x", price_diff - min_profit_threshold)

    def calculate_arbitrage_amount(self, market_price: float) -> tuple[str, float, float]:
        """Calculate a bounded arbitrage input amount and expected profit."""
        has_opportunity, direction, _ = self.check_arbitrage_opportunity(market_price)
        if not has_opportunity:
            return ("", 0.0, 0.0)

        pool_price = self.pool.spot_price
        fee_rate = self.pool.fee_rate
        if direction == "x_to_y":
            optimal_amount = self._calculate_sell_amount(pool_price, market_price, fee_rate)
        else:
            optimal_amount = self._calculate_buy_amount(pool_price, market_price, fee_rate)

        expected_profit = self._calculate_expected_profit(direction, optimal_amount, market_price)
        return (direction, optimal_amount, expected_profit)

    def quote(self, market_price: float, max_amount: float | None = None) -> ArbitrageResult:
        """Build a read-only arbitrage quote without mutating the pool."""
        direction, optimal_amount, _ = self.calculate_arbitrage_amount(market_price)
        amount_in = min(optimal_amount, max_amount) if max_amount is not None else optimal_amount
        if not direction or amount_in <= 0:
            return self._empty_result(market_price)

        reserve_x_before = self.pool.reserve_x
        reserve_y_before = self.pool.reserve_y
        spot_price_before = self.pool.spot_price
        fee = amount_in * self.pool.fee_rate
        effective_in = amount_in - fee
        k = self.pool.invariant

        if direction == "x_to_y":
            new_reserve_x = reserve_x_before + effective_in
            amount_out = reserve_y_before - k / new_reserve_x
            reserve_x_after = reserve_x_before + amount_in
            reserve_y_after = reserve_y_before - amount_out
            theoretical_price = spot_price_before
            profit = amount_out - amount_in * market_price
        else:
            new_reserve_y = reserve_y_before + effective_in
            amount_out = reserve_x_before - k / new_reserve_y
            reserve_x_after = reserve_x_before - amount_out
            reserve_y_after = reserve_y_before + amount_in
            theoretical_price = 1 / spot_price_before if spot_price_before not in (0, float("inf")) else float("inf")
            profit = amount_out * market_price - amount_in

        execution_price = amount_out / amount_in
        return ArbitrageResult(
            direction=direction,
            amount_in=amount_in,
            amount_out=amount_out,
            fee=fee,
            profit=max(0.0, profit),
            execution_price=execution_price,
            market_price=market_price,
            slippage_pct=calculate_slippage_pct(theoretical_price, execution_price),
            reserve_x_before=reserve_x_before,
            reserve_y_before=reserve_y_before,
            reserve_x_after=reserve_x_after,
            reserve_y_after=reserve_y_after,
            spot_price_before=spot_price_before,
            spot_price_after=reserve_y_after / reserve_x_after if reserve_x_after > 0 else float("inf"),
            arbitrage_executed=True,
        )

    def execute_arbitrage(self, market_price: float, max_amount: float | None = None) -> ArbitrageResult:
        """Execute arbitrage and update pool reserves."""
        result = self.quote(market_price, max_amount)
        if not result.arbitrage_executed:
            return result
        self.pool.reserve_x = result.reserve_x_after
        self.pool.reserve_y = result.reserve_y_after
        return result

    def _empty_result(self, market_price: float) -> ArbitrageResult:
        return ArbitrageResult(
            direction="",
            amount_in=0.0,
            amount_out=0.0,
            fee=0.0,
            profit=0.0,
            execution_price=0.0,
            market_price=market_price,
            slippage_pct=None,
            reserve_x_before=self.pool.reserve_x,
            reserve_y_before=self.pool.reserve_y,
            reserve_x_after=self.pool.reserve_x,
            reserve_y_after=self.pool.reserve_y,
            spot_price_before=self.pool.spot_price,
            spot_price_after=self.pool.spot_price,
            arbitrage_executed=False,
        )

    def _calculate_sell_amount(self, pool_price: float, market_price: float, fee_rate: float) -> float:
        """Calculate input X amount when X is expensive in the pool."""
        if market_price >= pool_price:
            return 0.0
        gamma = 1 - fee_rate
        k = self.pool.invariant
        a = gamma
        b = self.pool.reserve_x * (1 + gamma)
        c = self.pool.reserve_x**2 - k / market_price
        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            return 0.0
        return max(0.0, (-b + discriminant**0.5) / (2 * a))

    def _calculate_buy_amount(self, pool_price: float, market_price: float, fee_rate: float) -> float:
        """Calculate input Y amount when X is cheap in the pool."""
        if market_price <= pool_price:
            return 0.0
        gamma = 1 - fee_rate
        k = self.pool.invariant
        a = gamma
        b = self.pool.reserve_y * (1 + gamma)
        c = self.pool.reserve_y**2 - market_price * k
        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            return 0.0
        return max(0.0, (-b + discriminant**0.5) / (2 * a))

    def _calculate_expected_profit(self, direction: str, amount_in: float, market_price: float) -> float:
        """Calculate profit using the current pre-trade pool state."""
        if amount_in <= 0:
            return 0.0
        k = self.pool.invariant
        effective_in = amount_in * (1 - self.pool.fee_rate)
        if direction == "x_to_y":
            new_reserve_x = self.pool.reserve_x + effective_in
            amount_out = self.pool.reserve_y - k / new_reserve_x
            return max(0.0, amount_out - amount_in * market_price)
        if direction == "y_to_x":
            new_reserve_y = self.pool.reserve_y + effective_in
            amount_out = self.pool.reserve_x - k / new_reserve_y
            return max(0.0, amount_out * market_price - amount_in)
        return 0.0

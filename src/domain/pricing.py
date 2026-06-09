from __future__ import annotations


def calculate_slippage_pct(theoretical_price: float, execution_price: float | None) -> float | None:
    """Calculate slippage percentage between a reference price and execution price."""
    if execution_price is None:
        return None
    if theoretical_price <= 0 or theoretical_price == float("inf"):
        return None
    return round(abs(execution_price - theoretical_price) / theoretical_price * 100, 12)

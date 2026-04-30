from __future__ import annotations


def calculate_slippage_pct(theoretical_price: float, execution_price: float | None) -> float | None:
    if execution_price is None:
        return None
    if theoretical_price <= 0 or theoretical_price == float("inf"):
        return None
    return round(abs(execution_price - theoretical_price) / theoretical_price * 100, 12)


def average_slippage_pct(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)

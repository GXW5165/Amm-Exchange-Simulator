from __future__ import annotations


def calculate_slippage_pct(theoretical_price: float, execution_price: float | None) -> float | None:
    """计算滑点百分比。

    theoretical_price 是交易前池内现货价格，execution_price 是本次成交均价。
    当价格不可定义时返回 None，避免在汇总统计中引入无意义数值。
    """
    if execution_price is None:
        return None
    if theoretical_price <= 0 or theoretical_price == float("inf"):
        return None
    return round(abs(execution_price - theoretical_price) / theoretical_price * 100, 12)


def average_slippage_pct(values: list[float | None]) -> float | None:
    """计算平均滑点，自动忽略非交易事件产生的 None。"""
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)

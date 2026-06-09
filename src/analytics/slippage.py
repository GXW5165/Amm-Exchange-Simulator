from __future__ import annotations

from src.domain.pricing import calculate_slippage_pct


def average_slippage_pct(values: list[float | None]) -> float | None:
    """计算平均滑点，自动忽略非交易事件产生的 None。"""
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)

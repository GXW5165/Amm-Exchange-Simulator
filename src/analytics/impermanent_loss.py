from __future__ import annotations

from math import isfinite, sqrt


def impermanent_loss_from_price_ratio(price_ratio: float) -> float:
    """根据价格变化比例计算无常损失率。

    返回值是小数形式，例如 -0.01 表示相对单纯持有少 1%。公式来自
    恒定乘积 AMM 中 50/50 双资产池的标准无常损失模型。
    """
    if price_ratio <= 0:
        raise ValueError("price_ratio must be positive")
    return 2 * sqrt(price_ratio) / (1 + price_ratio) - 1


def impermanent_loss_pct(initial_price: float, current_price: float) -> float | None:
    """根据初始价格和当前价格输出百分比形式的无常损失。"""
    if not isfinite(initial_price) or not isfinite(current_price):
        return None
    if initial_price <= 0 or current_price <= 0:
        return None
    ratio = current_price / initial_price
    return impermanent_loss_from_price_ratio(ratio) * 100


def impermanent_loss_amount_in_y(initial_pool_value_in_y: float, impermanent_loss_rate_pct: float | None) -> float | None:
    """把无常损失百分比折算成 Token Y 计价的正数损失金额。"""
    if impermanent_loss_rate_pct is None:
        return None
    return abs(initial_pool_value_in_y * impermanent_loss_rate_pct / 100)

from __future__ import annotations

from dataclasses import dataclass

from src.domain.pool import Pool


@dataclass
class PoolDepthPoint:
    """池深度曲线上的一点。

    记录在指定滑点容忍度下，两个交易方向各能从池中换出的最大资产量。
    所有金额均为输入资产的原生单位（x_to_y 为 Token X，y_to_x 为 Token Y）。
    """

    slippage_tolerance_pct: float
    max_trade_amount_x_to_y: float
    max_trade_amount_y_to_x: float


def _max_trade_amount_for_slippage_in_direction(
    reserve: float,
    fee_rate: float,
    target_slippage_pct: float,
) -> float:
    """根据储备量和手续费率反解指定滑点下的最大可交易量。

    从恒定乘积 AMM 的滑点公式反推：

        S = 1 - R*(1-f) / (R + amount_in*(1-f))
        => amount_in = R * (S - f) / ((1-f) * (1-S))

    其中 S = target_slippage_pct / 100, f = fee_rate。

    当 S ≤ f 时表示目标滑点小于或等于手续费率，返回 0.0，因为即使
    最小交易也会产生至少 fee_rate*100 的基础滑点。
    """
    if target_slippage_pct <= 0.0:
        return 0.0
    if reserve <= 0.0:
        return 0.0

    s = target_slippage_pct / 100.0
    f = fee_rate

    # 手续费天然产生最小滑点；当目标不超过该阈值时视为不可交易
    if s <= f:
        return 0.0

    # 防止 S→100% 导致的除零，上限不变（最大实用滑点 < 100%）
    if s >= 1.0:
        return float("inf")

    numerator = reserve * (s - f)
    denominator = (1.0 - f) * (1.0 - s)
    return numerator / denominator


def compute_max_trade_size_for_slippage(
    pool: Pool,
    direction: str,
    target_slippage_pct: float,
) -> float:
    """计算在指定滑点容忍度下最多可交易的资产量。

    Args:
        pool: 当前资金池状态。
        direction: "x_to_y" 或 "y_to_x"。
        target_slippage_pct: 目标滑点百分比，例如 2.0 表示 2%。

    Returns:
        最大可交易量（按 input 资产原单位）。如果 direction 不合法
        则抛出 ValueError；滑点太小无法交易时返回 0.0。
    """
    if target_slippage_pct <= 0.0:
        return 0.0

    if direction == "x_to_y":
        return _max_trade_amount_for_slippage_in_direction(
            reserve=pool.reserve_x,
            fee_rate=pool.fee_rate,
            target_slippage_pct=target_slippage_pct,
        )
    elif direction == "y_to_x":
        return _max_trade_amount_for_slippage_in_direction(
            reserve=pool.reserve_y,
            fee_rate=pool.fee_rate,
            target_slippage_pct=target_slippage_pct,
        )
    else:
        raise ValueError(f"Unsupported direction: {direction}")


def compute_pool_depth_curve(
    pool: Pool,
    slippage_levels: list[float] | None = None,
) -> list[PoolDepthPoint]:
    """生成池深度曲线：在多个滑点级别下计算两个方向的最大可交易量。

    Args:
        pool: 当前资金池状态。
        slippage_levels: 滑点百分比列表，默认 [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]。

    Returns:
        PoolDepthPoint 列表，按滑点从小到大排列。
    """
    if slippage_levels is None:
        slippage_levels = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

    result: list[PoolDepthPoint] = []
    for level in slippage_levels:
        result.append(
            PoolDepthPoint(
                slippage_tolerance_pct=level,
                max_trade_amount_x_to_y=compute_max_trade_size_for_slippage(
                    pool, "x_to_y", level
                ),
                max_trade_amount_y_to_x=compute_max_trade_size_for_slippage(
                    pool, "y_to_x", level
                ),
            )
        )
    return result


def compute_max_trade_at_2pct(pool: Pool) -> float | None:
    """便捷函数：计算 2% 滑点下两个方向中较大的最大可交易量。

    2% 是专业 DEX 分析中常用的标准深度指标。

    Returns:
        max(可交易 X, 可交易 Y)；池无效时返回 None。
    """
    if pool.reserve_x <= 0.0 or pool.reserve_y <= 0.0:
        return None

    amount_x = compute_max_trade_size_for_slippage(pool, "x_to_y", 2.0)
    amount_y = compute_max_trade_size_for_slippage(pool, "y_to_x", 2.0)

    if amount_x <= 0.0 and amount_y <= 0.0:
        return None

    return max(amount_x, amount_y)

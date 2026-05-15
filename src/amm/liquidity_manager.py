from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from src.domain.exceptions import InsufficientBalanceError, InsufficientLiquidityError
from src.domain.pool import Pool


@dataclass(frozen=True)
class LiquidityAddResult:
    """添加流动性的结果：记录实际消耗资产和新增 LP 份额。"""

    consumed_x: float
    consumed_y: float
    minted_shares: float
    total_lp_shares: float


@dataclass(frozen=True)
class LiquidityRemoveResult:
    """移除流动性的结果：记录赎回资产和销毁 LP 份额。"""

    amount_x: float
    amount_y: float
    burned_shares: float
    total_lp_shares: float


class LiquidityManager:
    """流动性管理模块：负责 LP 份额铸造、销毁和池状态更新。"""

    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    def add_liquidity(self, amount_x: float, amount_y: float) -> LiquidityAddResult:
        if amount_x <= 0 or amount_y <= 0:
            raise InsufficientBalanceError("Liquidity amounts must be positive")

        # 首次建池没有可参考的总份额，sqrt(x*y) 能让 LP 份额与池子规模同阶，
        # 同时避免单边资产数量差异直接放大初始份额。
        if self.pool.reserve_x <= 0 or self.pool.reserve_y <= 0 or self.pool.total_lp_shares <= 0:
            minted_shares = sqrt(amount_x * amount_y)
            self.pool.reserve_x += amount_x
            self.pool.reserve_y += amount_y
            self.pool.total_lp_shares += minted_shares
            return LiquidityAddResult(amount_x, amount_y, minted_shares, self.pool.total_lp_shares)

        # 后续加池按当前储备比例消耗资产：多带入的一侧资产不会被使用，
        # 这样新增 LP 不会通过非比例注入改变现有池内价格。
        share_ratio = min(amount_x / self.pool.reserve_x, amount_y / self.pool.reserve_y)
        if share_ratio <= 0:
            raise InsufficientBalanceError("Invalid liquidity ratio")

        consumed_x = self.pool.reserve_x * share_ratio
        consumed_y = self.pool.reserve_y * share_ratio
        minted_shares = self.pool.total_lp_shares * share_ratio
        self.pool.reserve_x += consumed_x
        self.pool.reserve_y += consumed_y
        self.pool.total_lp_shares += minted_shares
        return LiquidityAddResult(consumed_x, consumed_y, minted_shares, self.pool.total_lp_shares)

    def remove_liquidity(self, lp_share: float) -> LiquidityRemoveResult:
        if lp_share <= 0:
            raise InsufficientLiquidityError("LP share must be positive")
        if self.pool.total_lp_shares <= 0 or lp_share > self.pool.total_lp_shares:
            raise InsufficientLiquidityError("Not enough liquidity")

        # LP 份额代表对池子整体储备的按比例所有权，因此赎回时两侧资产同步按比例减少。
        share_ratio = lp_share / self.pool.total_lp_shares
        amount_x = self.pool.reserve_x * share_ratio
        amount_y = self.pool.reserve_y * share_ratio
        self.pool.reserve_x -= amount_x
        self.pool.reserve_y -= amount_y
        self.pool.total_lp_shares -= lp_share
        return LiquidityRemoveResult(amount_x, amount_y, lp_share, self.pool.total_lp_shares)

from __future__ import annotations

from copy import deepcopy
from math import isclose

from src.domain.pool import Pool
from src.domain.user import User


def assign_initial_lp_owner(
    users: dict[str, User],
    pool: Pool,
    initial_lp_owner: str | None = "protocol",
) -> dict[str, User]:
    """复制用户集合，并把未显式分配的初始 LP 份额归属到指定账户。

    Pool 会根据初始双边储备自动生成总 LP 份额。配置中已经声明的用户
    LP 份额保持不变；剩余份额归给 initial_lp_owner，避免直接使用
    SimulatorEngine 时出现无主 LP，从而让手续费收益和 PnL 统计口径一致。
    """
    prepared_users: dict[str, User] = deepcopy(users)
    if pool.total_lp_shares <= 0:
        return prepared_users

    assigned_shares = sum(user.lp_shares for user in prepared_users.values())
    if assigned_shares > pool.total_lp_shares and not isclose(
        assigned_shares,
        pool.total_lp_shares,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("sum of user LP shares exceeds initial pool total LP shares")

    remainder = pool.total_lp_shares - assigned_shares
    if remainder <= 1e-9:
        return prepared_users

    owner_id = str(initial_lp_owner or "").strip()
    if not owner_id:
        raise ValueError("initial_lp_owner is required when initial LP shares are not fully assigned")

    owner = prepared_users.setdefault(owner_id, User(user_id=owner_id))
    owner.lp_shares += remainder
    return prepared_users

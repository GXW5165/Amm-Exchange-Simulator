from dataclasses import dataclass


@dataclass
class LPPosition:
    """LP 仓位快照。

    该对象用于描述某个用户在某一时刻对应的 LP 份额及其可赎回的
    Token X / Token Y 数量，适合报告或后续扩展仓位展示时复用。
    """

    user_id: str
    shares: float
    amount_x: float
    amount_y: float

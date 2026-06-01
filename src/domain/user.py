from dataclasses import dataclass


@dataclass
class User:
    """仿真用户账户。

    balance_x 和 balance_y 表示用户钱包里的两种 Token 余额；
    lp_shares 表示用户持有的 LP 份额。LP 份额不是钱包资产本身，
    而是用户对资金池储备的比例索取权。
    """

    user_id: str
    balance_x: float = 0.0
    balance_y: float = 0.0
    lp_shares: float = 0.0

    def deposit_x(self, amount: float) -> None:
        """向用户钱包增加 Token X。"""
        self.balance_x += amount

    def deposit_y(self, amount: float) -> None:
        """向用户钱包增加 Token Y。"""
        self.balance_y += amount

    def withdraw_x(self, amount: float) -> None:
        """从用户钱包扣减 Token X。余额校验由上层业务流程负责。"""
        self.balance_x -= amount

    def withdraw_y(self, amount: float) -> None:
        """从用户钱包扣减 Token Y。余额校验由上层业务流程负责。"""
        self.balance_y -= amount

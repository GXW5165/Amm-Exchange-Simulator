class AMMError(Exception):
    """项目内 AMM/仿真相关异常的基类。"""


class PoolNotInitializedError(AMMError):
    """资金池尚未初始化时抛出。"""


class InsufficientBalanceError(AMMError):
    """用户钱包余额或输入金额不足以完成操作时抛出。"""


class InsufficientLiquidityError(AMMError):
    """LP 份额或资金池流动性不足时抛出。"""


class InvalidEventError(AMMError):
    """事件类型、方向或载荷字段非法时抛出。"""

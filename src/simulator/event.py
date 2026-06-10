from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """仿真系统支持的事件类型。"""

    SWAP = "swap"
    ADD_LIQUIDITY = "add_liquidity"
    REMOVE_LIQUIDITY = "remove_liquidity"
    ARBITRAGE = "arbitrage"


@dataclass(order=True)
class Event:
    """离散事件对象。

    timestamp 参与排序；event_id、event_type、user_id 和 payload 不参与排序，
    这样事件队列可以用时间推进仿真，同时保留原始事件信息用于日志记录。
    """

    timestamp: float
    event_id: int = field(compare=False)
    event_type: EventType = field(compare=False)
    user_id: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False, default_factory=dict)

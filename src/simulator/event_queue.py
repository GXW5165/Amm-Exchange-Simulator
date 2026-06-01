from __future__ import annotations

import heapq
from itertools import count
from typing import Optional

from .event import Event


class EventQueue:
    """稳定的离散事件优先队列。

    队列按 timestamp 升序弹出事件；当多个事件时间相同时，使用内部递增序号
    保持入队顺序，避免 heapq 直接比较 Event 对象导致顺序不稳定。
    """

    def __init__(self) -> None:
        """初始化空堆和入队序号生成器。"""
        self._heap: list[tuple[float, int, Event]] = []
        self._sequence = count()

    def push(self, event: Event) -> None:
        """压入单个事件。"""
        heapq.heappush(self._heap, (event.timestamp, next(self._sequence), event))

    def pop(self) -> Optional[Event]:
        """弹出下一个事件；队列为空时返回 None。"""
        if not self._heap:
            return None
        _, _, event = heapq.heappop(self._heap)
        return event

    def extend(self, events: list[Event]) -> None:
        """批量压入事件。"""
        for event in events:
            self.push(event)

    def empty(self) -> bool:
        """判断事件队列是否为空。"""
        return not self._heap

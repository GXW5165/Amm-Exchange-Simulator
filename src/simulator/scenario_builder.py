from __future__ import annotations

from typing import Any

from .event import Event, EventType


def build_events(raw_events: list[dict[str, Any]]) -> list[Event]:
    """把配置中的原始事件字典转换成 Event 列表。

    event_id 按配置顺序从 1 开始分配，payload 只保留具体事件需要的业务字段，
    例如 swap 的 direction/amount_in 或流动性事件的 amount_x/amount_y。
    """
    events: list[Event] = []
    for index, raw_event in enumerate(raw_events, start=1):
        event_type = EventType(raw_event["event_type"])
        payload = {key: value for key, value in raw_event.items() if key not in {"timestamp", "event_type", "user_id"}}
        events.append(
            Event(
                timestamp=float(raw_event.get("timestamp", index)),
                event_id=index,
                event_type=event_type,
                user_id=str(raw_event["user_id"]),
                payload=payload,
            )
        )
    return events

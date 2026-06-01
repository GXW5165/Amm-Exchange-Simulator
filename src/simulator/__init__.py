"""仿真层导出。

集中暴露离散事件、事件队列、仿真引擎和仿真结果对象。
"""

from .engine import SimulatorEngine, build_events
from .event import Event, EventType
from .event_queue import EventQueue
from .result import SimulationResult

__all__ = [
    "SimulationResult",
    "SimulatorEngine",
    "build_events",
    "Event",
    "EventType",
    "EventQueue",
]

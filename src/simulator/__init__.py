"""仿真层导出。

集中暴露离散事件、事件队列、仿真引擎和仿真结果对象。
"""

from .engine import SimulatorEngine
from .event import Event, EventType
from .event_queue import EventQueue
from .result import SimulationResult
from .scenario_builder import build_events

__all__ = [
    "SimulationResult",
    "SimulatorEngine",
    "build_events",
    "Event",
    "EventType",
    "EventQueue",
]

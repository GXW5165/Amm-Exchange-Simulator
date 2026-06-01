from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.application.validation import validate_simulation_input
from src.domain.user import User
from src.simulator.event import Event
from src.simulator.scenario_builder import build_events


@dataclass
class AppConfig:
    """应用级配置对象。

    该对象是 YAML、Web 表单和场景构造之间的统一数据结构。核心字段包括
    初始资金池参数、用户初始余额、待执行事件和输出路径。
    """

    initial_reserve_x: float = 0.0
    initial_reserve_y: float = 0.0
    fee_rate: float = 0.003
    initial_lp_owner: str | None = "protocol"
    log_path: str = "data/output/logs/simulation.csv"
    summary_path: str = "data/output/results/summary.json"
    plot_dir: str = "data/output/results"
    users: dict[str, User] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def build_events(self) -> list[Event]:
        """把原始字典事件转换成仿真引擎可调度的 Event 对象。"""
        return build_events(self.events)


def load_config(path: str | Path) -> AppConfig:
    """读取 YAML 配置并完成基础校验。

    函数会把用户配置转换为 User 对象，并在返回前调用统一校验逻辑，
    因此调用方拿到的 AppConfig 已经满足进入仿真核心的基本条件。
    """
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    users: dict[str, User] = {}
    for user_id, user_data in (data.get("users") or {}).items():
        users[user_id] = User(
            user_id=user_id,
            balance_x=float(user_data.get("balance_x", 0.0)),
            balance_y=float(user_data.get("balance_y", 0.0)),
            lp_shares=float(user_data.get("lp_shares", 0.0)),
        )

    config = AppConfig(
        initial_reserve_x=float(data.get("initial_reserve_x", 0.0)),
        initial_reserve_y=float(data.get("initial_reserve_y", 0.0)),
        fee_rate=float(data.get("fee_rate", 0.003)),
        initial_lp_owner=data.get("initial_lp_owner", "protocol"),
        log_path=str(data.get("log_path", "data/output/logs/simulation.csv")),
        summary_path=str(data.get("summary_path", "data/output/results/summary.json")),
        plot_dir=str(data.get("plot_dir", "data/output/results")),
        users=users,
        events=list(data.get("events") or []),
    )
    validate_simulation_input(
        initial_reserve_x=config.initial_reserve_x,
        initial_reserve_y=config.initial_reserve_y,
        fee_rate=config.fee_rate,
        initial_lp_owner=config.initial_lp_owner,
        users=config.users,
        events=config.events,
    ).raise_for_errors()
    return config

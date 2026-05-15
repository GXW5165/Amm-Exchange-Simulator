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
    initial_reserve_x: float = 0.0
    initial_reserve_y: float = 0.0
    fee_rate: float = 0.003
    seed: int | None = None
    log_path: str = "data/output/logs/simulation.csv"
    summary_path: str = "data/output/results/summary.json"
    plot_dir: str = "data/output/results"
    users: dict[str, User] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def build_events(self) -> list[Event]:
        return build_events(self.events)


def load_config(path: str | Path) -> AppConfig:
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
        seed=data.get("seed"),
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
        users=config.users,
        events=config.events,
    ).raise_for_errors()
    return config

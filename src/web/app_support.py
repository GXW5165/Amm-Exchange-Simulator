from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.domain.user import User
from src.infrastructure.config_loader import AppConfig


def build_default_user_rows(users: dict[str, User]) -> list[dict[str, Any]]:
    if not users:
        return [{"user_id": "alice", "balance_x": 500.0, "balance_y": 500.0, "lp_shares": 0.0}]
    return [
        {
            "user_id": user.user_id,
            "balance_x": user.balance_x,
            "balance_y": user.balance_y,
            "lp_shares": user.lp_shares,
        }
        for user in users.values()
    ]


def build_default_event_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not events:
        return [
            {
                "timestamp": 1.0,
                "event_type": "swap",
                "user_id": "alice",
                "direction": "x_to_y",
                "amount_in": 10.0,
                "amount_x": 0.0,
                "amount_y": 0.0,
                "lp_share": 0.0,
            }
        ]

    rows: list[dict[str, Any]] = []
    for event in events:
        rows.append(
            {
                "timestamp": float(event.get("timestamp", 0.0)),
                "event_type": str(event.get("event_type", "swap")),
                "user_id": str(event.get("user_id", "")),
                "direction": str(event.get("direction", "x_to_y")),
                "amount_in": float(event.get("amount_in", 0.0) or 0.0),
                "amount_x": float(event.get("amount_x", 0.0) or 0.0),
                "amount_y": float(event.get("amount_y", 0.0) or 0.0),
                "lp_share": float(event.get("lp_share", 0.0) or 0.0),
            }
        )
    return rows


def normalize_user_rows(rows: list[dict[str, Any]]) -> dict[str, User]:
    users: dict[str, User] = {}
    for row in rows:
        user_id = str(row.get("user_id", "")).strip()
        if not user_id:
            continue
        users[user_id] = User(
            user_id=user_id,
            balance_x=float(row.get("balance_x", 0.0) or 0.0),
            balance_y=float(row.get("balance_y", 0.0) or 0.0),
            lp_shares=float(row.get("lp_shares", 0.0) or 0.0),
        )
    return users


def normalize_event_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        event_type = str(row.get("event_type", "")).strip()
        user_id = str(row.get("user_id", "")).strip()
        if not event_type or not user_id:
            continue

        event: dict[str, Any] = {
            "timestamp": float(row.get("timestamp", 0.0) or 0.0),
            "event_type": event_type,
            "user_id": user_id,
        }

        if event_type == "swap":
            event["direction"] = str(row.get("direction", "x_to_y") or "x_to_y")
            event["amount_in"] = float(row.get("amount_in", 0.0) or 0.0)
        elif event_type == "add_liquidity":
            event["amount_x"] = float(row.get("amount_x", 0.0) or 0.0)
            event["amount_y"] = float(row.get("amount_y", 0.0) or 0.0)
        elif event_type == "remove_liquidity":
            event["lp_share"] = float(row.get("lp_share", 0.0) or 0.0)
        else:
            continue

        normalized.append(event)

    normalized.sort(key=lambda item: item["timestamp"])
    return normalized


def build_config_from_runtime_input(
    *,
    initial_reserve_x: float,
    initial_reserve_y: float,
    fee_rate: float,
    users: dict[str, User],
    events: list[dict[str, Any]],
    output_root: str = "data/output/web_runs",
) -> AppConfig:
    run_id = uuid4().hex[:12]
    base_dir = Path(output_root) / run_id
    return AppConfig(
        initial_reserve_x=initial_reserve_x,
        initial_reserve_y=initial_reserve_y,
        fee_rate=fee_rate,
        log_path=(base_dir / "simulation.csv").as_posix(),
        summary_path=(base_dir / "summary.json").as_posix(),
        plot_dir=base_dir.as_posix(),
        users=users,
        events=events,
    )


def user_pnl_rows(summary_user_pnl: dict[str, Any]) -> list[dict[str, Any]]:
    return [asdict(item) for item in summary_user_pnl.values()]

import os
from pathlib import Path

from src.web.app_support import (
    build_config_from_runtime_input,
    cleanup_old_web_runs,
    delete_saved_config,
    list_saved_configs,
    load_saved_config,
    normalize_event_rows,
    normalize_user_rows,
    sanitize_saved_config_name,
    save_config_to_yaml,
    validate_runtime_input,
)


def test_normalize_user_rows_builds_user_mapping() -> None:
    users = normalize_user_rows([
        {"user_id": "alice", "balance_x": 10.0, "balance_y": 20.0, "lp_shares": 0.0},
        {"user_id": "", "balance_x": 1.0, "balance_y": 1.0, "lp_shares": 0.0},
    ])

    assert list(users.keys()) == ["alice"]
    assert users["alice"].balance_x == 10.0


def test_normalize_event_rows_filters_and_sorts_events() -> None:
    events = normalize_event_rows([
        {"timestamp": 2, "event_type": "add_liquidity", "user_id": "alice", "amount_x": 5.0, "amount_y": 5.0},
        {"timestamp": 1, "event_type": "swap", "user_id": "alice", "direction": "x_to_y", "amount_in": 2.0},
        {"timestamp": 3, "event_type": "arbitrage", "user_id": "alice", "market_price": 0.95, "max_amount": 50.0},
    ])

    assert events[0]["event_type"] == "swap"
    assert events[1]["event_type"] == "add_liquidity"
    assert events[2]["event_type"] == "arbitrage"
    assert events[2]["market_price"] == 0.95
    assert events[2]["max_amount"] == 50.0


def test_build_config_from_runtime_input_uses_web_run_paths() -> None:
    config = build_config_from_runtime_input(
        initial_reserve_x=1000.0,
        initial_reserve_y=1000.0,
        fee_rate=0.003,
        initial_lp_owner="treasury",
        users=normalize_user_rows([{"user_id": "alice", "balance_x": 10.0, "balance_y": 10.0, "lp_shares": 0.0}]),
        events=normalize_event_rows([{"timestamp": 1, "event_type": "swap", "user_id": "alice", "direction": "x_to_y", "amount_in": 1.0}]),
    )

    assert "data/output/web_runs" in config.log_path
    assert config.summary_path.endswith("summary.json")
    assert config.initial_lp_owner == "treasury"


def test_saved_config_lifecycle_round_trips_yaml(tmp_path: Path) -> None:
    users = normalize_user_rows([
        {"user_id": "alice", "balance_x": 10.0, "balance_y": 20.0, "lp_shares": 0.0},
    ])
    events = normalize_event_rows([
        {"timestamp": 1, "event_type": "swap", "user_id": "alice", "direction": "x_to_y", "amount_in": 2.0},
    ])

    path = save_config_to_yaml(
        name="my config!",
        initial_reserve_x=1000.0,
        initial_reserve_y=1000.0,
        fee_rate=0.003,
        initial_lp_owner="protocol",
        users=users,
        events=events,
        output_dir=tmp_path.as_posix(),
    )

    assert path.name == "myconfig.yaml"
    assert list_saved_configs(tmp_path.as_posix()) == ["myconfig"]
    loaded = load_saved_config("myconfig", tmp_path.as_posix())
    assert loaded is not None
    assert loaded["users"]["alice"]["balance_y"] == 20.0
    assert loaded["events"][0]["amount_in"] == 2.0
    assert delete_saved_config("myconfig", tmp_path.as_posix()) is True
    assert load_saved_config("myconfig", tmp_path.as_posix()) is None


def test_saved_config_names_are_sanitized_for_load_and_delete(tmp_path: Path) -> None:
    outside = tmp_path.parent / "escape.yaml"
    outside.write_text("sentinel: true", encoding="utf-8")

    assert sanitize_saved_config_name("../escape") == "..escape"
    assert load_saved_config("../escape", tmp_path.as_posix()) is None
    assert delete_saved_config("../escape", tmp_path.as_posix()) is False
    assert outside.exists()


def test_cleanup_old_web_runs_keeps_newest_directories(tmp_path: Path) -> None:
    for index in range(4):
        run_dir = tmp_path / f"run_{index}"
        run_dir.mkdir()
        os.utime(run_dir, (1000 + index, 1000 + index))

    removed = cleanup_old_web_runs(tmp_path.as_posix(), keep=2)

    assert removed == 2
    assert sorted(path.name for path in tmp_path.iterdir()) == ["run_2", "run_3"]


def test_validate_runtime_input_rejects_unknown_event_user() -> None:
    users = normalize_user_rows([
        {"user_id": "alice", "balance_x": 10.0, "balance_y": 10.0, "lp_shares": 0.0},
    ])
    events = normalize_event_rows([
        {"timestamp": 1, "event_type": "swap", "user_id": "ghost", "direction": "x_to_y", "amount_in": 1.0},
    ])

    result = validate_runtime_input(
        initial_reserve_x=1000.0,
        initial_reserve_y=1000.0,
        fee_rate=0.003,
        initial_lp_owner="protocol",
        users=users,
        events=events,
    )

    assert not result.ok
    assert any("ghost" in error for error in result.errors)

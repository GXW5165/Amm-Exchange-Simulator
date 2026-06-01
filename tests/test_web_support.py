from src.web.app_support import build_config_from_runtime_input, normalize_event_rows, normalize_user_rows


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
    ])

    assert events[0]["event_type"] == "swap"
    assert events[1]["event_type"] == "add_liquidity"


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

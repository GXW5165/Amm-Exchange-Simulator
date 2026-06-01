from pathlib import Path

import pytest

from src.application.simulation_runner import SimulationRunner
from src.domain.user import User
from src.infrastructure.config_loader import AppConfig, load_config


def test_simulation_runner_exports_all_artifacts(tmp_path: Path) -> None:
    config = load_config(Path("configs/default.yaml"))
    config.log_path = "logs/test_simulation.csv"
    config.summary_path = "results/test_summary.json"
    config.plot_dir = "results/plots"

    runner = SimulationRunner(tmp_path)
    artifacts = runner.run_from_config(config)

    assert artifacts.csv_path.exists()
    assert artifacts.summary_path.exists()
    assert artifacts.plot_paths
    assert artifacts.warnings == []
    assert all(path.exists() for path in artifacts.plot_paths.values())


def test_runner_assigns_unowned_initial_lp_to_protocol(tmp_path: Path) -> None:
    config = AppConfig(
        initial_reserve_x=1000.0,
        initial_reserve_y=1000.0,
        fee_rate=0.003,
        initial_lp_owner="protocol",
        log_path="simulation.csv",
        summary_path="summary.json",
        plot_dir="plots",
        users={"alice": User("alice", balance_x=100.0, balance_y=100.0)},
        events=[
            {
                "timestamp": 1,
                "event_type": "swap",
                "user_id": "alice",
                "direction": "x_to_y",
                "amount_in": 10.0,
            }
        ],
    )

    result = SimulationRunner(tmp_path).run_from_config(config).result

    assert result.initial_users["protocol"].lp_shares == 1000.0
    assert result.users["protocol"].lp_shares == 1000.0
    assert result.summary.user_pnl["protocol"].initial_value_at_initial_price_in_y == 2000.0


def test_runner_rejects_over_assigned_initial_lp(tmp_path: Path) -> None:
    config = AppConfig(
        initial_reserve_x=1000.0,
        initial_reserve_y=1000.0,
        users={"alice": User("alice", lp_shares=1001.0)},
        events=[
            {
                "timestamp": 1,
                "event_type": "swap",
                "user_id": "alice",
                "direction": "x_to_y",
                "amount_in": 1.0,
            }
        ],
    )

    with pytest.raises(ValueError, match="LP shares"):
        SimulationRunner(tmp_path).run_from_config(config)

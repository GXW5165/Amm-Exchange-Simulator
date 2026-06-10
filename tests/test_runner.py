from pathlib import Path

import pytest

from src.application.initialization import assign_initial_lp_owner
from src.application.simulation_runner import SimulationRunner
from src.domain.pool import Pool
from src.domain.user import User
from src.infrastructure.config_loader import AppConfig, load_config
from src.infrastructure.excel_exporter import export_to_excel


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


def test_three_trader_standard_config_runs(tmp_path: Path) -> None:
    config = load_config(Path("configs/three_trader_standard.yaml"))
    config.log_path = "three_trader/simulation.csv"
    config.summary_path = "three_trader/summary.json"
    config.plot_dir = "three_trader/plots"

    artifacts = SimulationRunner(tmp_path).run_from_config(config)
    summary = artifacts.result.summary

    assert set(artifacts.result.initial_users) >= {"alice", "bob", "carol", "protocol"}
    assert summary.total_events == 8
    assert summary.swap_events == 4
    assert summary.liquidity_events == 2
    assert summary.arbitrage_events == 2
    assert artifacts.csv_path.exists()


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


def test_assign_initial_lp_owner_is_public_helper() -> None:
    pool = Pool(1000.0, 1000.0, 0.003)
    users = {"alice": User("alice", lp_shares=100.0)}

    prepared = assign_initial_lp_owner(users, pool, "protocol")

    assert prepared["alice"].lp_shares == 100.0
    assert prepared["protocol"].lp_shares == 900.0
    assert "protocol" not in users


def test_assign_initial_lp_owner_rejects_blank_owner_when_remainder_exists() -> None:
    pool = Pool(1000.0, 1000.0, 0.003)

    with pytest.raises(ValueError, match="initial_lp_owner"):
        assign_initial_lp_owner({}, pool, "")


def test_excel_export_records_chart_embedding_warnings(tmp_path: Path) -> None:
    config = load_config("configs/default.yaml")
    config.log_path = "simulation.csv"
    config.summary_path = "summary.json"
    config.plot_dir = "plots"
    artifacts = SimulationRunner(tmp_path).run_from_config(config)

    bad_image = tmp_path / "bad-image.png"
    bad_image.write_text("not a real png", encoding="utf-8")
    artifacts.plot_paths = {"bad_chart": bad_image}

    xlsx_path = export_to_excel(artifacts, tmp_path / "simulation.xlsx")

    assert xlsx_path.exists()
    assert any("bad_chart" in warning for warning in artifacts.warnings)

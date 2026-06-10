from pathlib import Path

from src.infrastructure.config_loader import load_config
from src.interface.cli import AMMCLI, main


def test_non_interactive_config_demo_runs_and_exports(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "demo.yaml"
    config_path.write_text(
        "\n".join([
            "initial_reserve_x: 1000.0",
            "initial_reserve_y: 1000.0",
            "fee_rate: 0.003",
            f"log_path: '{(tmp_path / 'simulation.csv').as_posix()}'",
            f"summary_path: '{(tmp_path / 'summary.json').as_posix()}'",
            f"plot_dir: '{(tmp_path / 'plots').as_posix()}'",
            "users:",
            "  alice:",
            "    balance_x: 100.0",
            "    balance_y: 100.0",
            "    lp_shares: 0.0",
            "events:",
            "  - timestamp: 1",
            "    event_type: swap",
            "    user_id: alice",
            "    direction: x_to_y",
            "    amount_in: 10.0",
        ]),
        encoding="utf-8",
    )

    exit_code = main(["--config", str(config_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "[simulation] processed_events=1" in output
    assert (tmp_path / "simulation.csv").exists()
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "plots" / "pool_spot_price.png").exists()


def test_runner_does_not_mutate_config_users(tmp_path: Path) -> None:
    from src.application.simulation_runner import SimulationRunner

    config = load_config("configs/default.yaml")
    config.log_path = str(tmp_path / "simulation.csv")
    config.summary_path = str(tmp_path / "summary.json")
    config.plot_dir = str(tmp_path / "plots")

    initial_alice_x = config.users["alice"].balance_x
    initial_bob_lp = config.users["bob"].lp_shares
    runner = SimulationRunner(Path.cwd())

    first = runner.run_from_config(config)
    second = runner.run_from_config(config)

    assert config.users["alice"].balance_x == initial_alice_x
    assert config.users["bob"].lp_shares == initial_bob_lp
    assert first.result.summary.total_events == second.result.summary.total_events
    assert first.result.summary.total_fees == second.result.summary.total_fees


def test_interactive_cli_default_run_keeps_final_state_available() -> None:
    cli = AMMCLI()

    cli.run_default_simulation()

    assert cli.pool is not None
    assert cli.engine.records
    assert len(cli.engine.records) == 9
    assert cli.pool.reserve_x == cli.engine.records[-1].reserve_x_after

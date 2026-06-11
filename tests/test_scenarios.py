from pathlib import Path

import pytest

from src.application import parameter_sweep
from src.application.parameter_sweep import run_parameter_sweep
from src.application.scenarios import build_fee_rate_scenarios, build_large_trade_shock_scenario, build_liquidity_depth_scenarios
from src.application.simulation_runner import SimulationRunner
from src.infrastructure.config_loader import load_config


def test_large_trade_shock_scenario_scales_first_swap() -> None:
    config = load_config("configs/default.yaml")
    original_amount = config.events[0]["amount_in"]
    scenario = build_large_trade_shock_scenario(config, shock_multiplier=3.0)

    assert scenario.events[0]["amount_in"] == original_amount * 3.0
    assert config.events[0]["amount_in"] == original_amount


def test_parameter_scenarios_build_named_configs() -> None:
    config = load_config("configs/default.yaml")

    fee_scenarios = build_fee_rate_scenarios(config, [0.0, 0.003])
    depth_scenarios = build_liquidity_depth_scenarios(config, [2.0])

    assert set(fee_scenarios) == {"fee_0", "fee_0.003"}
    assert fee_scenarios["fee_0"].fee_rate == 0.0
    assert depth_scenarios["liquidity_2x"].initial_reserve_x == config.initial_reserve_x * 2.0


def test_parameter_sweep_keeps_warning_when_comparison_plot_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_config("configs/default.yaml")

    def fail_comparison_plot(*args, **kwargs) -> None:
        raise RuntimeError("comparison plot unavailable")

    monkeypatch.setattr(parameter_sweep, "plot_multi_scenario_comparison", fail_comparison_plot)

    results = run_parameter_sweep(
        base_config=config,
        param_grid=[{"fee_rate": 0.0}],
        runner=SimulationRunner(tmp_path),
        output_root=(tmp_path / "sweeps").as_posix(),
    )

    artifacts = next(iter(results.values()))
    assert any("comparison plot unavailable" in warning for warning in artifacts.warnings)

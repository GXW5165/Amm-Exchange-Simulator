from src.application.scenarios import build_fee_rate_scenarios, build_large_trade_shock_scenario, build_liquidity_depth_scenarios
from src.infrastructure.config_loader import load_config


def test_large_trade_shock_scenario_scales_first_swap() -> None:
    config = load_config("configs/default.yaml")
    scenario = build_large_trade_shock_scenario(config, shock_multiplier=3.0)

    assert scenario.events[0]["amount_in"] == config.events[0]["amount_in"] * 3.0
    assert config.events[0]["amount_in"] == 10.0


def test_parameter_scenarios_build_named_configs() -> None:
    config = load_config("configs/default.yaml")

    fee_scenarios = build_fee_rate_scenarios(config, [0.0, 0.003])
    depth_scenarios = build_liquidity_depth_scenarios(config, [2.0])

    assert set(fee_scenarios) == {"fee_0", "fee_0.003"}
    assert fee_scenarios["fee_0"].fee_rate == 0.0
    assert depth_scenarios["liquidity_2x"].initial_reserve_x == config.initial_reserve_x * 2.0

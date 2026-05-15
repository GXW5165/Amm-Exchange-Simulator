from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from src.infrastructure.config_loader import AppConfig


def build_basic_scenario(config: AppConfig) -> AppConfig:
    return deepcopy(config)


def build_large_trade_shock_scenario(config: AppConfig, *, shock_multiplier: float = 8.0) -> AppConfig:
    # 大额冲击场景只放大第一笔 swap，方便观察同一池深下滑点和价格偏移的变化。
    scenario = deepcopy(config)
    if not scenario.events:
        return scenario

    for event in scenario.events:
        if event.get("event_type") == "swap":
            event["amount_in"] = float(event.get("amount_in", 0.0)) * shock_multiplier
            break
    return scenario


def build_fee_rate_scenarios(config: AppConfig, fee_rates: list[float] | None = None) -> dict[str, AppConfig]:
    # 手续费率对比用于展示“交易成本”和“LP 手续费收益”之间的权衡。
    rates = fee_rates or [0.0, 0.003, 0.01]
    return {f"fee_{rate:g}": replace(deepcopy(config), fee_rate=rate) for rate in rates}


def build_liquidity_depth_scenarios(config: AppConfig, multipliers: list[float] | None = None) -> dict[str, AppConfig]:
    # 初始储备越深，同样规模交易造成的价格冲击和滑点通常越低。
    values = multipliers or [0.5, 1.0, 2.0]
    scenarios: dict[str, AppConfig] = {}
    for multiplier in values:
        scenario = deepcopy(config)
        scenario.initial_reserve_x *= multiplier
        scenario.initial_reserve_y *= multiplier
        scenarios[f"liquidity_{multiplier:g}x"] = scenario
    return scenarios

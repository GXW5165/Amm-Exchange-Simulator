"""应用层导出。

提供配置驱动运行、输入校验和实验场景构造。
"""

from .parameter_sweep import (
    build_comparison_table,
    build_scenario_name,
    export_comparison_table_csv,
    generate_param_grid,
    run_parameter_sweep,
)
from .scenarios import build_fee_rate_scenarios, build_large_trade_shock_scenario, build_liquidity_depth_scenarios
from .simulation_runner import SimulationArtifacts, SimulationRunner
from .validation import ValidationResult, validate_simulation_input

__all__ = [
    "SimulationArtifacts",
    "SimulationRunner",
    "ValidationResult",
    "build_comparison_table",
    "build_fee_rate_scenarios",
    "build_large_trade_shock_scenario",
    "build_liquidity_depth_scenarios",
    "build_scenario_name",
    "export_comparison_table_csv",
    "generate_param_grid",
    "run_parameter_sweep",
    "validate_simulation_input",
]

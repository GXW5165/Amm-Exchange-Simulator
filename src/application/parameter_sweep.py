from __future__ import annotations

"""参数遍历批量仿真模块。

提供参数网格生成、批量运行仿真和对比报表生成功能。与现有的
run_scenarios() 侧重点不同：函数式场景构造侧重手动指定参数变化，
本模块侧重自动生成参数笛卡尔积并批量执行。
"""

import csv
from copy import deepcopy
from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import Any

from src.visualization.plotter import plot_multi_scenario_comparison


# AppConfig 延迟导入以避免基础设施层 <-> 应用层之间的循环依赖。
# AppConfig 类型在函数体内按需导入。


# SimulationArtifacts 在类型注解中延迟导入以避免循环依赖
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.simulation_runner import SimulationArtifacts, SimulationRunner
    from src.infrastructure.config_loader import AppConfig


def generate_param_grid(**kwargs) -> list[dict[str, Any]]:
    """生成参数值的笛卡尔积。

    每个关键字参数的值为一个列表，包含该参数要遍历的所有取值。
    参数名必须对应 AppConfig 的字段名（如 fee_rate、initial_reserve_x 等）。

    Example:
        >>> grid = generate_param_grid(
        ...     fee_rate=[0.0, 0.003, 0.01],
        ...     initial_reserve_x=[500.0, 1000.0],
        ... )
        >>> len(grid)
        6

    Returns:
        参数组合字典列表，每个字典可传给 apply_params 覆盖 AppConfig。
    """
    if not kwargs:
        return []

    keys = list(kwargs.keys())
    values = [kwargs[k] for k in keys]

    result: list[dict[str, Any]] = []
    for combo in product(*values):
        result.append(dict(zip(keys, combo)))
    return result


def build_scenario_name(params: dict[str, Any]) -> str:
    """根据参数覆盖字典生成人类可读的场景名称。

    按 key 排序后拼接 "key_value" 片段，value 中的点号替换为下划线。

    Example:
        >>> build_scenario_name({"fee_rate": 0.003, "initial_reserve_x": 1000})
        'fee_rate_0_003__initial_reserve_x_1000'
    """
    parts: list[str] = []
    for key in sorted(params.keys()):
        val = params[key]
        parts.append(f"{key}_{str(val).replace('.', '_')}")
    name = "__".join(parts)
    # 限制长度，避免文件名过长
    if len(name) > 80:
        name = name[:77] + "..."
    return name


def run_parameter_sweep(
    base_config: AppConfig,
    param_grid: list[dict[str, Any]],
    runner: "SimulationRunner",
    output_root: str = "data/output/sweeps",
) -> dict[str, "SimulationArtifacts"]:
    """按参数网格批量运行仿真。

    每个参数组合：
        1. 深拷贝基础配置
        2. 用 dataclasses.replace() 逐参数覆盖
        3. 设置独立的输出路径
        4. 调用 runner.run_from_config()
        5. 收集 artifacts

    全部运行完成后，额外生成多场景对比图表和对比 CSV。

    Args:
        base_config: 基础 AppConfig（不会被修改）。
        param_grid: generate_param_grid() 的输出。
        runner: 已初始化的 SimulationRunner 实例。
        output_root: 批量仿真的输出根目录。

    Returns:
        场景名 → SimulationArtifacts 的映射。
    """
    if not param_grid:
        return {}

    from src.infrastructure.config_loader import AppConfig  # 延迟导入避免循环

    results: dict[str, SimulationArtifacts] = {}
    for params in param_grid:
        name = build_scenario_name(params)
        config = deepcopy(base_config)

        # 逐参数覆盖（仅覆盖 AppConfig 中存在的字段）
        for key, value in params.items():
            if hasattr(config, key):
                config = replace(config, **{key: value})

        # 每个场景输出到独立子目录
        config.log_path = f"{output_root}/{name}/simulation.csv"
        config.summary_path = f"{output_root}/{name}/summary.json"
        config.plot_dir = f"{output_root}/{name}/plots"

        results[name] = runner.run_from_config(config)

    # ── 生成跨场景对比图表 ──
    try:
        scenario_results: dict[str, SimulationResult] = {
            name: artifacts.result for name, artifacts in results.items()
        }
        plot_multi_scenario_comparison(scenario_results, output_root)
    except Exception as exc:
        _append_warning_to_artifacts(results, f"Multi-scenario comparison plot failed: {exc}")

    # ── 导出对比 CSV ──
    try:
        table = build_comparison_table(results)
        export_comparison_table_csv(table, Path(output_root) / "comparison.csv")
    except Exception as exc:
        _append_warning_to_artifacts(results, f"Parameter sweep comparison CSV failed: {exc}")

    return results


def _append_warning_to_artifacts(results: dict[str, "SimulationArtifacts"], message: str) -> None:
    """把参数遍历附加产物失败信息写回每个场景产物。"""
    for artifacts in results.values():
        artifacts.warnings.append(message)


def build_comparison_table(
    results: dict[str, "SimulationArtifacts"],
) -> list[dict[str, Any]]:
    """从批量仿真结果中提取关键指标生成对比表。

    每行包含一个场景的核心指标，可用于 CSV 导出或 DataFrame 展示。

    Returns:
        字典列表，按场景名称排序。
    """
    rows: list[dict[str, Any]] = []
    for name in sorted(results.keys()):
        artifacts = results[name]
        summary = artifacts.result.summary
        rows.append(
            {
                "scenario": name,
                "total_events": summary.total_events,
                "swap_events": summary.swap_events,
                "liquidity_events": summary.liquidity_events,
                "total_fees": f"{summary.total_fees:.6f}",
                "total_fees_in_y": f"{summary.total_fees_in_y:.6f}",
                "avg_slippage_pct": (
                    f"{summary.average_slippage_pct:.6f}"
                    if summary.average_slippage_pct is not None
                    else "N/A"
                ),
                "max_slippage_pct": (
                    f"{summary.max_slippage_pct:.6f}"
                    if summary.max_slippage_pct is not None
                    else "N/A"
                ),
                "il_pct": (
                    f"{summary.impermanent_loss_pct:.6f}"
                    if summary.impermanent_loss_pct is not None
                    else "N/A"
                ),
                "il_amount_in_y": (
                    f"{summary.impermanent_loss_amount_in_y:.6f}"
                    if summary.impermanent_loss_amount_in_y is not None
                    else "N/A"
                ),
                "final_pool_value_in_y": f"{summary.final_pool_value_in_y:.6f}",
                "pool_depth_at_2pct": (
                    f"{summary.pool_depth_at_2pct:.6f}"
                    if summary.pool_depth_at_2pct is not None
                    else "N/A"
                ),
                "time_span_days": f"{summary.time_span_days:.4f}",
            }
        )
    return rows


def export_comparison_table_csv(
    table: list[dict[str, Any]],
    path: str | Path,
) -> Path:
    """将对比表导出为 CSV 文件。

    Args:
        table: build_comparison_table() 的输出。
        path: CSV 文件路径。

    Returns:
        写入后的文件 Path。
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not table:
        output_path.write_text("", encoding="utf-8")
        return output_path

    fieldnames = list(table[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table)

    return output_path

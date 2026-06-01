from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from src.infrastructure.config_loader import AppConfig
from src.infrastructure.csv_exporter import export_event_records
from src.infrastructure.summary_exporter import export_simulation_summary
from src.simulator.engine import SimulatorEngine
from src.simulator.result import SimulationResult
from src.visualization.plotter import generate_result_plots
from src.domain.pool import Pool
from src.domain.user import User


@dataclass
class SimulationArtifacts:
    """一次仿真运行产生的全部产物。

    result 保存内存中的仿真结果；csv_path、summary_path 和 plot_paths
    指向已经写入磁盘的日志、摘要和图表文件；warnings 用于记录不影响主流程的
    可视化等附加步骤失败信息。
    """

    result: SimulationResult
    csv_path: Path
    summary_path: Path
    plot_paths: dict[str, Path]
    warnings: list[str]


class SimulationRunner:
    """应用层运行器：把配置对象转换为完整的一次仿真和导出流程。"""

    def __init__(self, root_dir: str | Path) -> None:
        """保存项目根目录，后续所有相对输出路径都以它为基准。"""
        self.root_dir = Path(root_dir)

    def run_from_config(self, config: AppConfig) -> SimulationArtifacts:
        """根据配置运行仿真，并导出 CSV、JSON 和 PNG 图表。

        注意这里会深拷贝用户对象和事件配置，避免仿真过程中用户余额、LP 份额
        的变化反向污染原始 AppConfig。这样同一个配置对象可以被多次复用，
        场景对比实验也能保证每次都从同一初始状态开始。
        """
        pool = Pool(config.initial_reserve_x, config.initial_reserve_y, config.fee_rate)
        users: dict[str, User] = deepcopy(config.users)
        engine = SimulatorEngine(pool, users)
        result = engine.run(deepcopy(config).build_events())

        csv_path = export_event_records(result.records, self.root_dir / config.log_path)
        summary_path = export_simulation_summary(result.summary, self.root_dir / config.summary_path)
        plot_paths: dict[str, Path] = {}
        warnings: list[str] = []
        try:
            plot_paths = generate_result_plots(result, self.root_dir / config.plot_dir)
        except Exception as exc:
            warnings.append(f"Plot generation failed: {exc}")

        return SimulationArtifacts(
            result=result,
            csv_path=csv_path,
            summary_path=summary_path,
            plot_paths=plot_paths,
            warnings=warnings,
        )

    def run_scenarios(self, scenarios: dict[str, AppConfig]) -> dict[str, SimulationArtifacts]:
        """批量运行多个参数场景，并把每个场景输出到独立目录。"""
        artifacts: dict[str, SimulationArtifacts] = {}
        for name, config in scenarios.items():
            config.log_path = f"data/output/scenarios/{name}/simulation.csv"
            config.summary_path = f"data/output/scenarios/{name}/summary.json"
            config.plot_dir = f"data/output/scenarios/{name}/plots"
            artifacts[name] = self.run_from_config(config)
        return artifacts

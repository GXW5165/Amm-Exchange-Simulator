from __future__ import annotations

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
    result: SimulationResult
    csv_path: Path
    summary_path: Path
    plot_paths: dict[str, Path]
    warnings: list[str]


class SimulationRunner:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)

    def run_from_config(self, config: AppConfig) -> SimulationArtifacts:
        pool = Pool(config.initial_reserve_x, config.initial_reserve_y, config.fee_rate)
        users: dict[str, User] = config.users
        engine = SimulatorEngine(pool, users)
        result = engine.run(config.build_events())

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
        artifacts: dict[str, SimulationArtifacts] = {}
        for name, config in scenarios.items():
            config.log_path = f"data/output/scenarios/{name}/simulation.csv"
            config.summary_path = f"data/output/scenarios/{name}/summary.json"
            config.plot_dir = f"data/output/scenarios/{name}/plots"
            artifacts[name] = self.run_from_config(config)
        return artifacts

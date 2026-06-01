from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import isclose
from pathlib import Path
from typing import TYPE_CHECKING

from src.application.validation import validate_simulation_input
from src.infrastructure.csv_exporter import export_event_records
from src.infrastructure.summary_exporter import export_simulation_summary
from src.simulator.engine import SimulatorEngine
from src.simulator.result import SimulationResult
from src.visualization.plotter import generate_result_plots
from src.domain.pool import Pool
from src.domain.user import User

if TYPE_CHECKING:
    from src.infrastructure.config_loader import AppConfig


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
        validate_simulation_input(
            initial_reserve_x=config.initial_reserve_x,
            initial_reserve_y=config.initial_reserve_y,
            fee_rate=config.fee_rate,
            initial_lp_owner=config.initial_lp_owner,
            users=config.users,
            events=config.events,
        ).raise_for_errors()
        pool = Pool(config.initial_reserve_x, config.initial_reserve_y, config.fee_rate)
        users = self._prepare_initial_users(config, pool)
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

    def _prepare_initial_users(self, config: AppConfig, pool: Pool) -> dict[str, User]:
        """复制配置用户，并把未显式分配的初始 LP 份额归属到协议账户。

        Pool 会根据初始双边储备自动生成总 LP 份额。配置中已经写明的
        lp_shares 保持不变；剩余份额归给 initial_lp_owner，避免仿真中存在
        无主 LP，从而让手续费收益和 PnL 统计都有明确归属。
        """
        users: dict[str, User] = deepcopy(config.users)
        if pool.total_lp_shares <= 0:
            return users

        assigned_shares = sum(user.lp_shares for user in users.values())
        if assigned_shares > pool.total_lp_shares and not isclose(
            assigned_shares,
            pool.total_lp_shares,
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise ValueError("sum of user LP shares exceeds initial pool total LP shares")

        remainder = pool.total_lp_shares - assigned_shares
        if remainder <= 1e-9:
            return users

        owner_id = str(config.initial_lp_owner or "").strip()
        if not owner_id:
            raise ValueError("initial_lp_owner is required when initial LP shares are not fully assigned")
        owner = users.setdefault(owner_id, User(user_id=owner_id))
        owner.lp_shares += remainder
        return users

    def run_scenarios(self, scenarios: dict[str, AppConfig]) -> dict[str, SimulationArtifacts]:
        """批量运行多个参数场景，并把每个场景输出到独立目录。"""
        artifacts: dict[str, SimulationArtifacts] = {}
        for name, config in scenarios.items():
            config.log_path = f"data/output/scenarios/{name}/simulation.csv"
            config.summary_path = f"data/output/scenarios/{name}/summary.json"
            config.plot_dir = f"data/output/scenarios/{name}/plots"
            artifacts[name] = self.run_from_config(config)
        return artifacts

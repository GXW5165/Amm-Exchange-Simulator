from __future__ import annotations

import argparse
from pathlib import Path

from src.application.scenarios import build_fee_rate_scenarios, build_large_trade_shock_scenario, build_liquidity_depth_scenarios
from src.application.simulation_runner import SimulationRunner
from src.domain.pool import Pool
from src.domain.user import User
from src.infrastructure.config_loader import load_config
from src.infrastructure.logger import get_logger
from src.simulator.engine import SimulatorEngine
from src.simulator.scenario_builder import build_events


class AMMCLI:
    """交互式命令行界面。

    该类保留课程演示时常用的菜单式操作，用户可以逐步初始化资金池、执行交易、
    添加/移除流动性并查看状态。非交互式的一键 Demo 入口放在文件底部的
    run_config_once/main 中，便于助教或脚本直接复现。
    """

    def __init__(self) -> None:
        """初始化 CLI 状态，并尽量加载默认配置作为初始池子和用户。"""
        self.logger = get_logger()
        self.root_dir = Path(__file__).resolve().parents[2]
        self.config_path = self.root_dir / "configs" / "default.yaml"
        self.pool: Pool | None = None
        self.users: dict[str, User] = {}
        self.engine = SimulatorEngine()
        self.runner = SimulationRunner(self.root_dir)
        self._load_default_state()

    def _load_default_state(self) -> None:
        """从默认 YAML 构造交互模式的初始状态。"""
        if self.config_path.exists():
            config = load_config(self.config_path)
            self.pool = Pool(config.initial_reserve_x, config.initial_reserve_y, config.fee_rate)
            self.users = config.users
            self.engine = SimulatorEngine(self.pool, self.users)
        else:
            self.pool = Pool(0.0, 0.0)
            self.users = {}
            self.engine = SimulatorEngine(self.pool, self.users)

    def run(self) -> None:
        """进入菜单循环，直到用户选择退出。"""
        while True:
            self._print_menu()
            choice = input("Select an option: ").strip()
            if choice == "9":
                print("Exit.")
                break

            actions = {
                "1": self.run_default_simulation,
                "2": self.manual_initialize_pool,
                "3": self.execute_swap,
                "4": self.add_liquidity,
                "5": self.remove_liquidity,
                "6": self.view_pool_status,
                "7": self.view_user_status,
                "8": self.run_experiment_scenarios,
            }

            action = actions.get(choice)
            if action is None:
                print("Invalid option.")
                continue

            try:
                action()
            except Exception as exc:
                print(f"Operation failed: {exc}")

    def _print_menu(self) -> None:
        """打印交互模式主菜单。"""
        print("\nAMM Exchange Simulator")
        print("1. Use default config to run simulation")
        print("2. Manually initialize pool")
        print("3. Execute a swap")
        print("4. Add liquidity")
        print("5. Remove liquidity")
        print("6. View pool status")
        print("7. View user status")
        print("8. Run experiment scenarios")
        print("9. Exit")

    def _require_pool(self) -> Pool:
        """取得当前资金池；未初始化时抛出清晰错误。"""
        if self.pool is None:
            raise RuntimeError("Pool is not initialized")
        return self.pool

    def run_default_simulation(self) -> None:
        """按默认配置执行一次完整仿真并打印核心输出路径。"""
        if not self.config_path.exists():
            print("Default config file not found.")
            return

        config = load_config(self.config_path)
        self.pool = Pool(config.initial_reserve_x, config.initial_reserve_y, config.fee_rate)
        self.users = config.users
        self.engine = SimulatorEngine(self.pool, self.users)
        artifacts = self.runner.run_from_config(config)
        result = artifacts.result
        summary = result.summary

        print(f"Processed events: {summary.total_events}")
        print(f"Swap events: {summary.swap_events}")
        print(f"Liquidity events: {summary.liquidity_events}")
        print(f"Total fees: {summary.total_fees:.6f}")
        print(f"Average slippage (%): {summary.average_slippage_pct}")
        print(f"Max slippage (%): {summary.max_slippage_pct}")
        print(f"Impermanent loss (%): {summary.impermanent_loss_pct}")
        print(f"Output CSV: {artifacts.csv_path}")
        print(f"Output Summary: {artifacts.summary_path}")
        for name, path in artifacts.plot_paths.items():
            print(f"Plot {name}: {path}")
        for warning in artifacts.warnings:
            print(f"Warning: {warning}")

    def run_experiment_scenarios(self) -> None:
        """运行内置场景组，用于比较大额冲击、手续费率和流动性深度。"""
        if not self.config_path.exists():
            print("Default config file not found.")
            return

        config = load_config(self.config_path)
        scenarios = {
            "large_trade_shock": build_large_trade_shock_scenario(config),
            **build_fee_rate_scenarios(config),
            **build_liquidity_depth_scenarios(config),
        }
        artifacts_by_name = self.runner.run_scenarios(scenarios)
        for name, artifacts in artifacts_by_name.items():
            summary = artifacts.result.summary
            print(
                f"{name}: events={summary.total_events}, fees_y={summary.total_fees_in_y:.6f}, "
                f"avg_slippage={summary.average_slippage_pct}, il={summary.impermanent_loss_pct}"
            )
            print(f"  summary: {artifacts.summary_path}")

    def manual_initialize_pool(self) -> None:
        """手动输入储备和手续费率，重建当前资金池。"""
        reserve_x = self._prompt_float("Token X reserve: ")
        reserve_y = self._prompt_float("Token Y reserve: ")
        fee_rate = self._prompt_float("Fee rate (e.g. 0.003): ")
        self.pool = Pool(reserve_x, reserve_y, fee_rate)
        self.engine = SimulatorEngine(self.pool, self.users)
        print("Pool initialized.")

    def execute_swap(self) -> None:
        """把用户输入转换为 swap 事件，并通过仿真引擎执行。"""
        try:
            pool = self._require_pool()
        except RuntimeError as exc:
            print(str(exc))
            return

        user_id = input("user_id: ").strip()
        direction = input("direction(x_to_y / y_to_x): ").strip()
        amount_in = self._prompt_float("amount_in: ")
        event = {
            "timestamp": 0,
            "event_type": "swap",
            "user_id": user_id,
            "direction": direction,
            "amount_in": amount_in,
        }
        try:
            self.engine.process_event(build_events([event])[0])
            print(f"Swap executed. Pool spot price: {pool.spot_price:.6f}")
        except Exception as exc:
            print(f"Execution failed: {exc}")

    def add_liquidity(self) -> None:
        """把用户输入转换为添加流动性事件，并执行状态变更。"""
        try:
            self._require_pool()
        except RuntimeError as exc:
            print(str(exc))
            return

        user_id = input("user_id: ").strip()
        amount_x = self._prompt_float("amount_x: ")
        amount_y = self._prompt_float("amount_y: ")
        event = {
            "timestamp": 0,
            "event_type": "add_liquidity",
            "user_id": user_id,
            "amount_x": amount_x,
            "amount_y": amount_y,
        }
        try:
            self.engine.process_event(build_events([event])[0])
            print("Liquidity added.")
        except Exception as exc:
            print(f"Execution failed: {exc}")

    def remove_liquidity(self) -> None:
        """把用户输入转换为移除流动性事件，并执行状态变更。"""
        try:
            self._require_pool()
        except RuntimeError as exc:
            print(str(exc))
            return

        user_id = input("user_id: ").strip()
        lp_share = self._prompt_float("lp_share: ")
        event = {
            "timestamp": 0,
            "event_type": "remove_liquidity",
            "user_id": user_id,
            "lp_share": lp_share,
        }
        try:
            self.engine.process_event(build_events([event])[0])
            print("Liquidity removed.")
        except Exception as exc:
            print(f"Execution failed: {exc}")

    def view_pool_status(self) -> None:
        """打印当前资金池储备、价格和 LP 总份额。"""
        try:
            pool = self._require_pool()
        except RuntimeError as exc:
            print(str(exc))
            return

        print(f"reserve_x: {pool.reserve_x:.6f}")
        print(f"reserve_y: {pool.reserve_y:.6f}")
        print(f"fee_rate: {pool.fee_rate:.6f}")
        print(f"spot_price(y per x): {pool.spot_price:.6f}")
        print(f"lp_total_shares: {pool.total_lp_shares:.6f}")

    def view_user_status(self) -> None:
        """打印所有已加载用户的钱包余额和 LP 份额。"""
        if not self.users:
            print("No users loaded.")
            return

        for user in self.users.values():
            print(
                f"{user.user_id}: balance_x={user.balance_x:.6f}, balance_y={user.balance_y:.6f}, lp_shares={user.lp_shares:.6f}"
            )

    def _prompt_float(self, prompt: str) -> float:
        """循环读取浮点数，直到用户输入合法为止。"""
        while True:
            try:
                return float(input(prompt).strip())
            except ValueError:
                print("Please enter a valid number.")


def _resolve_config_path(path: str | Path, root_dir: Path) -> Path:
    """把用户传入的配置路径解析为绝对路径。

    相对路径默认相对于项目根目录，符合 README 中 `configs/default.yaml`
    这类写法；绝对路径则原样使用，方便测试或外部脚本传入临时配置。
    """
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = root_dir / config_path
    return config_path


def _print_artifact_summary(artifacts, *, label: str = "simulation") -> None:
    """以稳定格式打印一次运行的关键指标和输出文件，供非交互式 Demo 使用。"""
    summary = artifacts.result.summary
    print(f"[{label}] processed_events={summary.total_events}")
    print(f"[{label}] swap_events={summary.swap_events}")
    print(f"[{label}] liquidity_events={summary.liquidity_events}")
    print(f"[{label}] total_fees={summary.total_fees:.6f}")
    print(f"[{label}] total_fees_in_y={summary.total_fees_in_y:.6f}")
    print(f"[{label}] average_slippage_pct={summary.average_slippage_pct}")
    print(f"[{label}] max_slippage_pct={summary.max_slippage_pct}")
    print(f"[{label}] impermanent_loss_pct={summary.impermanent_loss_pct}")
    print(f"[{label}] csv={artifacts.csv_path}")
    print(f"[{label}] summary={artifacts.summary_path}")
    for name, path in artifacts.plot_paths.items():
        print(f"[{label}] plot_{name}={path}")
    for warning in artifacts.warnings:
        print(f"[{label}] warning={warning}")


def run_config_once(config_path: str | Path, *, run_scenarios: bool = False) -> int:
    """非交互式运行入口。

    `python main.py --config configs/default.yaml` 会调用本函数完成一次配置驱动
    仿真；加上 `--scenarios` 时会继续运行内置对比场景。返回值遵循进程退出码：
    成功为 0，配置缺失或运行失败时由异常向上抛出并交给 main 捕获。
    """
    root_dir = Path(__file__).resolve().parents[2]
    resolved_config_path = _resolve_config_path(config_path, root_dir)
    config = load_config(resolved_config_path)
    runner = SimulationRunner(root_dir)

    artifacts = runner.run_from_config(config)
    _print_artifact_summary(artifacts)

    if run_scenarios:
        scenarios = {
            "large_trade_shock": build_large_trade_shock_scenario(config),
            **build_fee_rate_scenarios(config),
            **build_liquidity_depth_scenarios(config),
        }
        for name, scenario_artifacts in runner.run_scenarios(scenarios).items():
            _print_artifact_summary(scenario_artifacts, label=name)

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。

    不传参数时保持原来的交互式菜单；传入 `--config` 或 `--demo` 时进入
    非交互式模式，便于课程验收时一条命令复现完整结果。
    """
    parser = argparse.ArgumentParser(description="AMM Exchange Simulator")
    parser.add_argument(
        "--config",
        default=None,
        help="使用指定 YAML 配置非交互式运行一次仿真，例如 configs/default.yaml。",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="使用 configs/default.yaml 执行一键 Demo。",
    )
    parser.add_argument(
        "--scenarios",
        action="store_true",
        help="在非交互式运行后继续执行内置参数对比场景。",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """程序入口：根据参数选择非交互式 Demo 或交互式菜单。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.demo or args.config or args.scenarios:
        config_path = args.config or "configs/default.yaml"
        return run_config_once(config_path, run_scenarios=args.scenarios)

    AMMCLI().run()
    return 0

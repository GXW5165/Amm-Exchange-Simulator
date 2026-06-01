from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.application.scenarios import build_fee_rate_scenarios, build_large_trade_shock_scenario, build_liquidity_depth_scenarios
from src.application.simulation_runner import SimulationRunner
from src.domain.pool import Pool
from src.domain.user import User
from src.infrastructure.config_loader import load_config
from src.infrastructure.logger import get_logger
from src.simulator.engine import SimulatorEngine
from src.simulator.scenario_builder import build_events

# ── 终端 ANSI 样式 ────────────────────────────────────────────────────
# 在 Windows 10+ 控制台中启用 VT100 虚拟终端序列
os.system("")

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_BLACK = "\033[30m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_MAGENTA = "\033[35m"
_CYAN = "\033[36m"
_WHITE = "\033[37m"

# 常用组合
TITLE = f"{_BOLD}{_CYAN}"
SUBTITLE = f"{_BOLD}{_WHITE}"
HEADER = f"{_BOLD}{_MAGENTA}"
SUCCESS = f"{_GREEN}"
ERROR = f"{_RED}"
WARN = f"{_YELLOW}"
INFO = f"{_BLUE}"
VALUE = f"{_BOLD}{_WHITE}"
LABEL = f"{_DIM}{_WHITE}"
SEP = f"{_DIM}{_MAGENTA}"

SEP_LINE = f"{SEP}{'─' * 56}{_RESET}"
SEP_DOUBLE = f"{SEP}{'═' * 56}{_RESET}"


def _p(value: float | None, fmt: str = ".6f") -> str:
    """安全格式化浮点数，None 时返回 N/A。"""
    if value is None:
        return "N/A"
    return f"{value:{fmt}}"


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

    # ── 工具方法 ──────────────────────────────────────────────────────

    @staticmethod
    def _press_any_key() -> None:
        """等待用户按回车后继续，避免输出一闪而过。"""
        input(f"\n{_DIM}Press Enter to return to menu...{_RESET}")

    def _print_section(self, title: str) -> None:
        """打印带装饰线的段落标题。"""
        print(f"\n{SEP_LINE}")
        print(f"  {HEADER}{title}{_RESET}")
        print(f"{SEP_LINE}")

    def _ok(self, message: str) -> None:
        """打印成功消息。"""
        print(f"\n  {SUCCESS}✓ {message}{_RESET}")

    def _err(self, message: str) -> None:
        """打印错误消息。"""
        print(f"\n  {ERROR}✗ {message}{_RESET}")

    # ── 菜单 ──────────────────────────────────────────────────────────

    def _print_menu(self) -> None:
        """打印带样式的主菜单。"""
        print(f"\n{SEP_DOUBLE}")
        print(f"{SEP_DOUBLE}")
        print(f"  {TITLE} █  AMM Exchange Simulator{_RESET}")
        print(f"  {LABEL}    恒定乘积做市商仿真系统 · 交互式控制台{_RESET}")
        print(f"{SEP_DOUBLE}")
        print(f"{SEP_DOUBLE}")
        print(f"  {SUBTITLE}Simulation{_RESET}")
        print(f"    {_BOLD}1.{_RESET}  Run default simulation")
        print(f"    {_BOLD}8.{_RESET}  Run experiment scenarios")
        print(f"  {SUBTITLE}Manual Operations{_RESET}")
        print(f"    {_BOLD}2.{_RESET}  Initialize pool")
        print(f"    {_BOLD}3.{_RESET}  Execute a swap")
        print(f"    {_BOLD}4.{_RESET}  Add liquidity")
        print(f"    {_BOLD}5.{_RESET}  Remove liquidity")
        print(f"  {SUBTITLE}Inspect{_RESET}")
        print(f"    {_BOLD}6.{_RESET}  View pool status")
        print(f"    {_BOLD}7.{_RESET}  View user status")
        print(f"  {SUBTITLE}System{_RESET}")
        print(f"    {_BOLD}9.{_RESET}  Exit")
        print(f"{SEP_DOUBLE}")

    def run(self) -> None:
        """进入菜单循环，直到用户选择退出。"""
        while True:
            self._print_menu()
            choice = input(f"  {_BOLD}▸ Select an option:{_RESET} ").strip()
            if choice == "9":
                print(f"\n  {_DIM}Goodbye.{_RESET}\n")
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
                print(f"\n  {ERROR}Invalid option — please enter 1–9.{_RESET}")
                self._press_any_key()
                continue

            try:
                action()
            except Exception as exc:
                self._err(f"Operation failed: {exc}")
            self._press_any_key()

    # ── 业务操作 ──────────────────────────────────────────────────────

    def _require_pool(self) -> Pool:
        """取得当前资金池；未初始化时抛出清晰错误。"""
        if self.pool is None:
            raise RuntimeError("Pool is not initialized")
        return self.pool

    def run_default_simulation(self) -> None:
        """按默认配置执行一次完整仿真并打印核心输出路径。"""
        if not self.config_path.exists():
            self._err("Default config file not found.")
            return

        config = load_config(self.config_path)
        self.pool = Pool(config.initial_reserve_x, config.initial_reserve_y, config.fee_rate)
        self.users = config.users
        self.engine = SimulatorEngine(self.pool, self.users)
        artifacts = self.runner.run_from_config(config)
        summary = artifacts.result.summary

        self._print_section("Simulation Result")

        # 事件与费用
        print(f"  {LABEL}Events{_RESET}       {VALUE}{summary.total_events}{_RESET}  "
              f"({INFO}swap{_RESET}: {summary.swap_events},  "
              f"{INFO}liquidity{_RESET}: {summary.liquidity_events})")
        print(f"  {LABEL}Total Fees{_RESET}   {VALUE}{summary.total_fees:.6f}{_RESET}  "
              f"({LABEL}in Y{_RESET}: {VALUE}{summary.total_fees_in_y:.6f}{_RESET})")

        # 滑点
        print(f"  {LABEL}Slippage{_RESET}     "
              f"avg {VALUE}{_p(summary.average_slippage_pct)}{_RESET}%  "
              f"max {VALUE}{_p(summary.max_slippage_pct)}{_RESET}%")

        # 无常损失
        il_str = f"{summary.impermanent_loss_pct:.6f}%" if summary.impermanent_loss_pct is not None else "N/A"
        print(f"  {LABEL}Imp. Loss{_RESET}   {VALUE}{il_str}{_RESET}")

        # 输出文件
        self._print_section("Output Files")
        print(f"  {INFO}CSV{_RESET}      {artifacts.csv_path}")
        print(f"  {INFO}JSON{_RESET}     {artifacts.summary_path}")
        for name, path in artifacts.plot_paths.items():
            print(f"  {INFO}Plot{_RESET}     {name}  →  {path}")
        for warning in artifacts.warnings:
            print(f"  {WARN}Warning{_RESET}  {warning}")

        self._ok("Simulation completed successfully")

    def run_experiment_scenarios(self) -> None:
        """运行内置场景组，用于比较大额冲击、手续费率和流动性深度。"""
        if not self.config_path.exists():
            self._err("Default config file not found.")
            return

        config = load_config(self.config_path)
        scenarios = {
            "large_trade_shock": build_large_trade_shock_scenario(config),
            **build_fee_rate_scenarios(config),
            **build_liquidity_depth_scenarios(config),
        }

        self._print_section("Experiment Scenarios")
        print(f"  {_DIM}Running {len(scenarios)} scenario groups...{_RESET}\n")

        artifacts_by_name = self.runner.run_scenarios(scenarios)
        for name, artifacts in artifacts_by_name.items():
            summary = artifacts.result.summary
            print(
                f"  {SUBTITLE}{name:<22}{_RESET}"
                f"  slippage {VALUE}{_p(summary.average_slippage_pct):>10}{_RESET}%"
                f"  IL {VALUE}{_p(summary.impermanent_loss_pct):>10}{_RESET}%"
                f"  fees_y {VALUE}{summary.total_fees_in_y:.6f}{_RESET}"
            )

        self._ok("All scenarios completed")

    def manual_initialize_pool(self) -> None:
        """手动输入储备和手续费率，重建当前资金池。"""
        self._print_section("Initialize Pool")
        reserve_x = self._prompt_float(f"  {LABEL}Token X reserve{_RESET}: ")
        reserve_y = self._prompt_float(f"  {LABEL}Token Y reserve{_RESET}: ")
        fee_rate = self._prompt_float(f"  {LABEL}Fee rate (e.g. 0.003){_RESET}: ")
        self.pool = Pool(reserve_x, reserve_y, fee_rate)
        self.engine = SimulatorEngine(self.pool, self.users)
        self._ok("Pool initialized")

    def execute_swap(self) -> None:
        """把用户输入转换为 swap 事件，并通过仿真引擎执行。"""
        try:
            pool = self._require_pool()
        except RuntimeError as exc:
            self._err(str(exc))
            return

        self._print_section("Execute Swap")
        user_id = input(f"  {LABEL}User ID{_RESET}: ").strip()
        direction = input(f"  {LABEL}Direction (x_to_y / y_to_x){_RESET}: ").strip()
        amount_in = self._prompt_float(f"  {LABEL}Amount In{_RESET}: ")
        event = {
            "timestamp": 0,
            "event_type": "swap",
            "user_id": user_id,
            "direction": direction,
            "amount_in": amount_in,
        }
        try:
            self.engine.process_event(build_events([event])[0])
            self._ok(f"Swap executed. Spot price: {VALUE}{pool.spot_price:.6f}{_RESET} Y/X")
        except Exception as exc:
            self._err(f"Execution failed: {exc}")

    def add_liquidity(self) -> None:
        """把用户输入转换为添加流动性事件，并执行状态变更。"""
        try:
            self._require_pool()
        except RuntimeError as exc:
            self._err(str(exc))
            return

        self._print_section("Add Liquidity")
        user_id = input(f"  {LABEL}User ID{_RESET}: ").strip()
        amount_x = self._prompt_float(f"  {LABEL}Amount X{_RESET}: ")
        amount_y = self._prompt_float(f"  {LABEL}Amount Y{_RESET}: ")
        event = {
            "timestamp": 0,
            "event_type": "add_liquidity",
            "user_id": user_id,
            "amount_x": amount_x,
            "amount_y": amount_y,
        }
        try:
            self.engine.process_event(build_events([event])[0])
            self._ok("Liquidity added")
        except Exception as exc:
            self._err(f"Execution failed: {exc}")

    def remove_liquidity(self) -> None:
        """把用户输入转换为移除流动性事件，并执行状态变更。"""
        try:
            self._require_pool()
        except RuntimeError as exc:
            self._err(str(exc))
            return

        self._print_section("Remove Liquidity")
        user_id = input(f"  {LABEL}User ID{_RESET}: ").strip()
        lp_share = self._prompt_float(f"  {LABEL}LP Shares to Burn{_RESET}: ")
        event = {
            "timestamp": 0,
            "event_type": "remove_liquidity",
            "user_id": user_id,
            "lp_share": lp_share,
        }
        try:
            self.engine.process_event(build_events([event])[0])
            self._ok("Liquidity removed")
        except Exception as exc:
            self._err(f"Execution failed: {exc}")

    def view_pool_status(self) -> None:
        """打印当前资金池储备、价格和 LP 总份额。"""
        try:
            pool = self._require_pool()
        except RuntimeError as exc:
            self._err(str(exc))
            return

        self._print_section("Pool Status")
        print(f"  {LABEL}Reserve X{_RESET}      {VALUE}{pool.reserve_x:.6f}{_RESET}")
        print(f"  {LABEL}Reserve Y{_RESET}      {VALUE}{pool.reserve_y:.6f}{_RESET}")
        print(f"  {LABEL}Fee Rate{_RESET}       {VALUE}{pool.fee_rate:.6f}{_RESET}")
        print(f"  {LABEL}Spot Price{_RESET}     {VALUE}{pool.spot_price:.6f}{_RESET}  {_DIM}(Y per X){_RESET}")
        print(f"  {LABEL}LP Total Shares{_RESET} {VALUE}{pool.total_lp_shares:.6f}{_RESET}")

    def view_user_status(self) -> None:
        """打印所有已加载用户的钱包余额和 LP 份额。"""
        if not self.users:
            self._err("No users loaded.")
            return

        self._print_section("User Status")
        header = f"  {HEADER}{'ID':<12}{'Balance X':>14}{'Balance Y':>14}{'LP Shares':>14}{_RESET}"
        print(header)
        print(f"  {SEP}{'─' * 54}{_RESET}")
        for user in self.users.values():
            print(
                f"  {VALUE}{user.user_id:<12}{_RESET}"
                f"{user.balance_x:>14.6f}"
                f"{user.balance_y:>14.6f}"
                f"{user.lp_shares:>14.6f}"
            )

    def _prompt_float(self, prompt: str) -> float:
        """循环读取浮点数，直到用户输入合法为止。"""
        while True:
            try:
                return float(input(prompt).strip())
            except ValueError:
                print(f"  {ERROR}Please enter a valid number.{_RESET}")


# ── 非交互式入口 ──────────────────────────────────────────────────────


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

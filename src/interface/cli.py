from __future__ import annotations

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
    def __init__(self) -> None:
        self.logger = get_logger()
        self.root_dir = Path(__file__).resolve().parents[2]
        self.config_path = self.root_dir / "configs" / "default.yaml"
        self.pool: Pool | None = None
        self.users: dict[str, User] = {}
        self.engine = SimulatorEngine()
        self.runner = SimulationRunner(self.root_dir)
        self._load_default_state()

    def _load_default_state(self) -> None:
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
        if self.pool is None:
            raise RuntimeError("Pool is not initialized")
        return self.pool

    def run_default_simulation(self) -> None:
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
        reserve_x = self._prompt_float("Token X reserve: ")
        reserve_y = self._prompt_float("Token Y reserve: ")
        fee_rate = self._prompt_float("Fee rate (e.g. 0.003): ")
        self.pool = Pool(reserve_x, reserve_y, fee_rate)
        self.engine = SimulatorEngine(self.pool, self.users)
        print("Pool initialized.")

    def execute_swap(self) -> None:
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
        if not self.users:
            print("No users loaded.")
            return

        for user in self.users.values():
            print(
                f"{user.user_id}: balance_x={user.balance_x:.6f}, balance_y={user.balance_y:.6f}, lp_shares={user.lp_shares:.6f}"
            )

    def _prompt_float(self, prompt: str) -> float:
        while True:
            try:
                return float(input(prompt).strip())
            except ValueError:
                print("Please enter a valid number.")


def main() -> None:
    AMMCLI().run()

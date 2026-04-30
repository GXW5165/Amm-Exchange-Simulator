from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from src.amm import AMMEngine, LiquidityManager
from src.analytics.metrics import MetricsCalculator
from src.analytics.record import EventRecord
from src.domain.exceptions import InsufficientBalanceError, InsufficientLiquidityError, InvalidEventError, PoolNotInitializedError
from src.domain.pool import Pool
from src.domain.user import User
from src.infrastructure.csv_exporter import export_event_records

from .event import Event, EventType
from .event_queue import EventQueue
from .result import SimulationResult
from .scenario_builder import build_events


class SimulatorEngine:
    """仿真控制模块：按时间顺序调度事件，并协调业务模块与指标模块。"""

    def __init__(self, pool: Pool | None = None, users: dict[str, User] | None = None) -> None:
        self.pool = pool
        self.users = users or {}
        self.event_queue = EventQueue()
        self.records: list[EventRecord] = []
        self.initial_pool = deepcopy(pool) if pool is not None else None
        self.initial_users = deepcopy(self.users)
        self.metrics = MetricsCalculator()

    def ensure_user(self, user_id: str) -> User:
        if user_id not in self.users:
            self.users[user_id] = User(user_id=user_id)
        return self.users[user_id]

    def schedule(self, event: Event) -> None:
        self.event_queue.push(event)

    def run(self, events: list[Event] | None = None) -> SimulationResult:
        if events:
            self.event_queue.extend(events)

        # 离散事件仿真主循环：每次取出队首事件，执行后记录状态快照。
        while not self.event_queue.empty():
            event = self.event_queue.pop()
            if event is None:
                break
            self.records.append(self.process_event(event))

        if self.pool is None:
            raise PoolNotInitializedError("Pool is not initialized")

        initial_pool = deepcopy(self.initial_pool) if self.initial_pool is not None else deepcopy(self.pool)
        return SimulationResult(
            records=self.records,
            pool=self.pool,
            users=self.users,
            initial_pool=initial_pool,
            initial_users=deepcopy(self.initial_users),
        )

    def process_event(self, event: Event) -> EventRecord:
        if self.pool is None:
            raise PoolNotInitializedError("Pool is not initialized")

        user = self.ensure_user(event.user_id)
        if event.event_type == EventType.SWAP:
            return self._process_swap(event, user)
        if event.event_type == EventType.ADD_LIQUIDITY:
            return self._process_add_liquidity(event, user)
        if event.event_type == EventType.REMOVE_LIQUIDITY:
            return self._process_remove_liquidity(event, user)
        raise InvalidEventError(f"Unsupported event type: {event.event_type}")

    def _process_swap(self, event: Event, user: User) -> EventRecord:
        direction = str(event.payload.get("direction", ""))
        amount_in = float(event.payload.get("amount_in", 0.0))
        amm = AMMEngine(self.pool)
        spot_price_before_swap = self.pool.spot_price

        if direction == "x_to_y":
            if user.balance_x < amount_in:
                raise InsufficientBalanceError("User has insufficient Token X")
            swap_result = amm.swap(direction, amount_in)
            user.balance_x -= amount_in
            user.balance_y += swap_result.amount_out
        elif direction == "y_to_x":
            if user.balance_y < amount_in:
                raise InsufficientBalanceError("User has insufficient Token Y")
            swap_result = amm.swap(direction, amount_in)
            user.balance_y -= amount_in
            user.balance_x += swap_result.amount_out
        else:
            raise InvalidEventError("Swap direction must be x_to_y or y_to_x")

        # y_to_x 的成交价格单位与 x_to_y 相反，因此用倒数作为理论价格。
        theoretical_price = spot_price_before_swap
        if direction == "y_to_x" and spot_price_before_swap not in (0, float("inf")):
            theoretical_price = 1 / spot_price_before_swap
        slippage_pct = self.metrics.calc_slippage_pct(theoretical_price, swap_result.execution_price)
        spot_price = self.pool.spot_price

        return self._build_record(
            event=event,
            user_id=user.user_id,
            event_type=event.event_type.value,
            direction=direction,
            amount_in=amount_in,
            amount_out=swap_result.amount_out,
            fee=swap_result.fee,
            spot_price=spot_price,
            execution_price=swap_result.execution_price,
            slippage_pct=slippage_pct,
        )

    def _process_add_liquidity(self, event: Event, user: User) -> EventRecord:
        amount_x = float(event.payload.get("amount_x", 0.0))
        amount_y = float(event.payload.get("amount_y", 0.0))
        if user.balance_x < amount_x or user.balance_y < amount_y:
            raise InsufficientBalanceError("User has insufficient balance for liquidity provision")

        liquidity = LiquidityManager(self.pool).add_liquidity(amount_x, amount_y)
        user.balance_x -= liquidity.consumed_x
        user.balance_y -= liquidity.consumed_y
        user.lp_shares += liquidity.minted_shares

        return self._build_record(
            event=event,
            user_id=user.user_id,
            event_type=event.event_type.value,
            amount_in=liquidity.consumed_x,
            amount_out=liquidity.consumed_y,
            fee=0.0,
            spot_price=self.pool.spot_price,
        )

    def _process_remove_liquidity(self, event: Event, user: User) -> EventRecord:
        lp_share = float(event.payload.get("lp_share", 0.0))
        if user.lp_shares < lp_share:
            raise InsufficientLiquidityError("User does not own enough LP shares")

        liquidity = LiquidityManager(self.pool).remove_liquidity(lp_share)
        user.lp_shares -= liquidity.burned_shares
        user.balance_x += liquidity.amount_x
        user.balance_y += liquidity.amount_y

        return self._build_record(
            event=event,
            user_id=user.user_id,
            event_type=event.event_type.value,
            amount_in=lp_share,
            amount_out=liquidity.amount_x + liquidity.amount_y,
            fee=0.0,
            spot_price=self.pool.spot_price,
        )

    def _build_record(
        self,
        *,
        event: Event,
        user_id: str,
        event_type: str,
        direction: str = "",
        amount_in: float | None = None,
        amount_out: float | None = None,
        fee: float | None = None,
        spot_price: float | None = None,
        execution_price: float | None = None,
        slippage_pct: float | None = None,
    ) -> EventRecord:
        return EventRecord(
            event_id=event.event_id,
            timestamp=event.timestamp,
            user_id=user_id,
            event_type=event_type,
            direction=direction,
            amount_in=amount_in,
            amount_out=amount_out,
            fee=fee,
            reserve_x=self.pool.reserve_x,
            reserve_y=self.pool.reserve_y,
            spot_price=spot_price,
            execution_price=execution_price,
            slippage_pct=slippage_pct,
            lp_total_shares=self.pool.total_lp_shares,
        )

    def export_csv(self, path: str | Path) -> Path:
        return export_event_records(self.records, path)

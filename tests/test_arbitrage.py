import pytest

from src.amm import ArbitrageEngine
from src.domain.exceptions import InsufficientBalanceError
from src.domain.pool import Pool
from src.domain.user import User
from src.simulator.engine import SimulatorEngine
from src.simulator.event import Event, EventType


def test_arbitrage_quote_does_not_mutate_pool() -> None:
    pool = Pool(reserve_x=1000.0, reserve_y=1000.0, fee_rate=0.003)
    engine = ArbitrageEngine(pool)

    quote = engine.quote(market_price=0.9)

    assert quote.arbitrage_executed is True
    assert quote.direction == "x_to_y"
    assert pool.reserve_x == 1000.0
    assert pool.reserve_y == 1000.0


def test_arbitrage_execute_updates_pool_and_reports_profit() -> None:
    pool = Pool(reserve_x=1000.0, reserve_y=1000.0, fee_rate=0.003)
    engine = ArbitrageEngine(pool)

    result = engine.execute_arbitrage(market_price=0.9)
    actual_profit = result.amount_out - result.amount_in * result.market_price

    assert result.arbitrage_executed is True
    assert result.profit == pytest.approx(actual_profit)
    assert pool.reserve_x == pytest.approx(result.reserve_x_after)
    assert pool.reserve_y == pytest.approx(result.reserve_y_after)


def test_arbitrage_event_updates_user_wallet() -> None:
    pool = Pool(reserve_x=1000.0, reserve_y=1000.0, fee_rate=0.003)
    users = {"arb": User(user_id="arb", balance_x=1000.0, balance_y=1000.0)}
    engine = SimulatorEngine(pool, users)

    engine.schedule(
        Event(
            timestamp=1.0,
            event_id=1,
            event_type=EventType.ARBITRAGE,
            user_id="arb",
            payload={"market_price": 0.9},
        )
    )

    result = engine.run()
    record = result.records[0]

    assert record.event_type == "arbitrage"
    assert record.arbitrage_executed is True
    assert record.market_price == 0.9
    assert record.arbitrage_profit is not None
    assert result.users["arb"].balance_x < 1000.0
    assert result.users["arb"].balance_y > 1000.0


def test_arbitrage_insufficient_balance_does_not_mutate_pool() -> None:
    pool = Pool(reserve_x=1000.0, reserve_y=1000.0, fee_rate=0.003)
    users = {"arb": User(user_id="arb", balance_x=0.0, balance_y=0.0)}
    engine = SimulatorEngine(pool, users)

    engine.schedule(
        Event(
            timestamp=1.0,
            event_id=1,
            event_type=EventType.ARBITRAGE,
            user_id="arb",
            payload={"market_price": 0.5},
        )
    )

    with pytest.raises(InsufficientBalanceError):
        engine.run()

    assert pool.reserve_x == 1000.0
    assert pool.reserve_y == 1000.0


def test_arbitrage_fees_are_included_in_summary_and_lp_income() -> None:
    pool = Pool(reserve_x=1000.0, reserve_y=1000.0, fee_rate=0.003)
    users = {
        "protocol": User(user_id="protocol", lp_shares=1000.0),
        "arb": User(user_id="arb", balance_x=1000.0, balance_y=1000.0),
    }
    engine = SimulatorEngine(pool, users)
    engine.schedule(
        Event(
            timestamp=1.0,
            event_id=1,
            event_type=EventType.ARBITRAGE,
            user_id="arb",
            payload={"market_price": 0.9, "max_amount": 100.0},
        )
    )

    result = engine.run()
    summary = result.summary

    assert summary.total_fees > 0.0
    assert summary.total_fees_in_y > 0.0
    assert summary.user_pnl["protocol"].fee_net_income_in_y > 0.0

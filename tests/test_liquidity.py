from src.domain.pool import Pool
from src.domain.user import User
from src.simulator import SimulatorEngine, build_events


def test_engine_processes_liquidity_events() -> None:
    pool = Pool(1000.0, 1000.0, 0.003)
    users = {"alice": User("alice", balance_x=200.0, balance_y=200.0)}
    engine = SimulatorEngine(pool, users)

    events = build_events([
        {
            "timestamp": 1,
            "event_type": "add_liquidity",
            "user_id": "alice",
            "amount_x": 50.0,
            "amount_y": 50.0,
        },
        {
            "timestamp": 2,
            "event_type": "remove_liquidity",
            "user_id": "alice",
            "lp_share": 10.0,
        },
    ])

    result = engine.run(events)

    assert len(result.records) == 2
    assert result.pool.total_lp_shares >= 0
    assert result.summary.liquidity_events == 2

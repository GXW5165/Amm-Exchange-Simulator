from pathlib import Path

from src.infrastructure.config_loader import load_config
from src.simulator import SimulatorEngine, build_events
from src.domain.pool import Pool


def test_default_config_can_be_loaded_and_run() -> None:
    config = load_config(Path("configs/default.yaml"))
    pool = Pool(
        config.initial_reserve_x,
        config.initial_reserve_y,
        config.fee_rate,
    )
    engine = SimulatorEngine(pool, config.users)
    result = engine.run(build_events(config.events))

    assert len(result.records) == len(config.events)
    assert result.pool.total_lp_shares >= 0
    assert result.summary.total_events == len(config.events)
    assert result.summary.total_fees >= 0
    assert result.summary.impermanent_loss_pct is not None
    assert "alice" in result.summary.user_pnl

import matplotlib.image as mpimg

from src.domain.pool import Pool
from src.domain.user import User
from src.simulator import SimulatorEngine, build_events
from src.visualization.plotter import generate_result_plots, plot_multi_scenario_comparison


def test_generate_result_plots_creates_png_files(tmp_path) -> None:
    pool = Pool(1000.0, 1000.0, 0.003)
    users = {
        "alice": User("alice", balance_x=200.0, balance_y=100.0),
        "bob": User("bob", balance_x=100.0, balance_y=200.0),
    }
    engine = SimulatorEngine(pool, users)
    events = build_events([
        {
            "timestamp": 1,
            "event_type": "swap",
            "user_id": "alice",
            "direction": "x_to_y",
            "amount_in": 10.0,
        },
        {
            "timestamp": 2,
            "event_type": "add_liquidity",
            "user_id": "bob",
            "amount_x": 20.0,
            "amount_y": 20.0,
        },
    ])

    result = engine.run(events)
    plot_paths = generate_result_plots(result, tmp_path)

    assert "pool_spot_price" in plot_paths
    assert "swap_slippage" in plot_paths
    assert "user_total_pnl" in plot_paths
    assert all(path.exists() for path in plot_paths.values())

    image_shapes = {mpimg.imread(path).shape[:2] for path in plot_paths.values()}
    assert len(image_shapes) == 1


def test_plot_multi_scenario_comparison_creates_four_metric_panel(tmp_path) -> None:
    def run_sample(amount_in: float):
        pool = Pool(1000.0, 1000.0, 0.003)
        users = {"alice": User("alice", balance_x=500.0, balance_y=500.0)}
        engine = SimulatorEngine(pool, users)
        events = build_events([
            {
                "timestamp": 1,
                "event_type": "swap",
                "user_id": "alice",
                "direction": "x_to_y",
                "amount_in": amount_in,
            }
        ])
        return engine.run(events)

    path = plot_multi_scenario_comparison(
        {
            "small_trade": run_sample(10.0),
            "large_trade": run_sample(100.0),
        },
        tmp_path,
    )

    assert path is not None
    assert path.name == "multi_scenario_comparison.png"
    assert path.exists()

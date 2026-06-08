"""测试历史价格回测模块。"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.application.backtesting import (
    BacktestConfig,
    PriceData,
    build_backtest_scenario,
    build_backtest_scenario_from_prices,
    generate_backtest_events,
    load_price_history,
    load_price_history_from_text,
)


class TestPriceData:
    """测试 PriceData 数据类。"""

    def test_price_data_creation(self) -> None:
        """测试创建价格数据点。"""
        data = PriceData(timestamp=1.0, price_y_per_x=1.5)
        assert data.timestamp == 1.0
        assert data.price_y_per_x == 1.5


class TestLoadPriceHistory:
    """测试加载历史价格数据。"""

    def test_load_valid_csv(self, tmp_path: Path) -> None:
        """测试加载有效的 CSV 文件。"""
        csv_content = "timestamp,price_y_per_x\n0,1.0\n1,1.1\n2,1.2\n"
        csv_file = tmp_path / "prices.csv"
        csv_file.write_text(csv_content)

        data = load_price_history(csv_file)
        assert len(data) == 3
        assert data[0].timestamp == 0.0
        assert data[0].price_y_per_x == 1.0
        assert data[2].price_y_per_x == 1.2

    def test_load_csv_sorted_by_timestamp(self, tmp_path: Path) -> None:
        """测试数据按时间戳排序。"""
        csv_content = "timestamp,price_y_per_x\n5,1.5\n1,1.1\n3,1.3\n"
        csv_file = tmp_path / "prices.csv"
        csv_file.write_text(csv_content)

        data = load_price_history(csv_file)
        assert data[0].timestamp == 1.0
        assert data[1].timestamp == 3.0
        assert data[2].timestamp == 5.0

    def test_load_missing_file_raises_error(self) -> None:
        """测试加载不存在的文件抛出错误。"""
        with pytest.raises(FileNotFoundError):
            load_price_history("nonexistent.csv")

    def test_load_from_text_without_writing_file(self) -> None:
        """测试从内存文本加载 CSV，供 Web 上传入口使用。"""
        data = load_price_history_from_text("timestamp,price_y_per_x\n0,1.0\n1,1.2\n")

        assert len(data) == 2
        assert data[1].timestamp == 1.0
        assert data[1].price_y_per_x == 1.2

    def test_load_rejects_missing_required_columns(self, tmp_path: Path) -> None:
        """测试 CSV 缺少必要列时抛出清晰错误。"""
        csv_file = tmp_path / "prices.csv"
        csv_file.write_text("time,price\n0,1.0\n")

        with pytest.raises(ValueError, match="timestamp and price_y_per_x"):
            load_price_history(csv_file)

    def test_load_rejects_non_numeric_values(self, tmp_path: Path) -> None:
        """测试非数字价格输入会被拒绝。"""
        csv_file = tmp_path / "prices.csv"
        csv_file.write_text("timestamp,price_y_per_x\n0,not-a-number\n")

        with pytest.raises(ValueError, match="Invalid numeric value"):
            load_price_history(csv_file)

    def test_load_rejects_non_positive_prices(self, tmp_path: Path) -> None:
        """测试零价格和负价格不会进入回测计算。"""
        csv_file = tmp_path / "prices.csv"
        csv_file.write_text("timestamp,price_y_per_x\n0,0\n1,1.0\n")

        with pytest.raises(ValueError, match="must be positive"):
            load_price_history(csv_file)


class TestGenerateBacktestEvents:
    """测试生成回测交易事件。"""

    def test_generate_events_with_price_increase(self) -> None:
        """测试价格上涨时生成买入事件。"""
        prices = [
            PriceData(timestamp=0.0, price_y_per_x=1.0),
            PriceData(timestamp=1.0, price_y_per_x=1.1),  # +10%
            PriceData(timestamp=2.0, price_y_per_x=1.2),  # +9%
        ]

        events = generate_backtest_events(
            prices,
            trader_id="test_trader",
            volatility_threshold=0.05,
            max_trade_size=50.0,
        )

        assert len(events) == 2
        assert events[0]["event_type"] == "swap"
        assert events[0]["user_id"] == "test_trader"
        assert events[0]["direction"] == "y_to_x"  # 价格上涨，买入X

    def test_generate_events_with_price_decrease(self) -> None:
        """测试价格下跌时生成卖出事件。"""
        prices = [
            PriceData(timestamp=0.0, price_y_per_x=1.2),
            PriceData(timestamp=1.0, price_y_per_x=1.0),  # -17%
            PriceData(timestamp=2.0, price_y_per_x=0.9),  # -10%
        ]

        events = generate_backtest_events(
            prices,
            trader_id="test_trader",
            volatility_threshold=0.05,
            max_trade_size=50.0,
        )

        assert len(events) == 2
        assert events[0]["direction"] == "x_to_y"  # 价格下跌，卖出X

    def test_generate_no_events_below_threshold(self) -> None:
        """测试价格变化低于阈值时不生成事件。"""
        prices = [
            PriceData(timestamp=0.0, price_y_per_x=1.0),
            PriceData(timestamp=1.0, price_y_per_x=1.001),  # +0.1%
            PriceData(timestamp=2.0, price_y_per_x=1.002),  # +0.1%
        ]

        events = generate_backtest_events(
            prices,
            volatility_threshold=0.01,  # 1% threshold
            max_trade_size=50.0,
        )

        assert len(events) == 0

    def test_generate_events_with_single_price_point(self) -> None:
        """测试只有一个价格点时不生成事件。"""
        prices = [PriceData(timestamp=0.0, price_y_per_x=1.0)]

        events = generate_backtest_events(prices)

        assert len(events) == 0


class TestBuildBacktestScenario:
    """测试构建回测场景。"""

    def test_build_scenario_returns_complete_config(self, tmp_path: Path) -> None:
        """测试构建场景返回完整配置。"""
        csv_content = "timestamp,price_y_per_x\n0,1.0\n1,1.2\n2,1.4\n"
        csv_file = tmp_path / "prices.csv"
        csv_file.write_text(csv_content)

        config = BacktestConfig(
            price_data_path=str(csv_file),
            initial_reserve_x=1000.0,
            initial_reserve_y=1000.0,
            fee_rate=0.003,
            volatility_threshold=0.05,
        )

        scenario = build_backtest_scenario(config)

        assert scenario["initial_reserve_x"] == 1000.0
        assert scenario["initial_reserve_y"] == 1000.0
        assert scenario["fee_rate"] == 0.003
        assert "backtester" in scenario["users"]
        assert len(scenario["events"]) > 0
        assert len(scenario["price_history"]) == 3

    def test_build_scenario_includes_backtester_user(self, tmp_path: Path) -> None:
        """测试场景包含回测用户。"""
        csv_content = "timestamp,price_y_per_x\n0,1.0\n1,1.2\n"
        csv_file = tmp_path / "prices.csv"
        csv_file.write_text(csv_content)

        config = BacktestConfig(price_data_path=str(csv_file))
        scenario = build_backtest_scenario(config)

        assert "backtester" in scenario["users"]
        assert scenario["users"]["backtester"]["balance_x"] == 1000.0
        assert scenario["users"]["backtester"]["balance_y"] == 1000.0

    def test_build_scenario_from_loaded_prices(self) -> None:
        """测试 Web 上传场景可直接用内存价格序列构建。"""
        prices = [
            PriceData(timestamp=0.0, price_y_per_x=1.0),
            PriceData(timestamp=1.0, price_y_per_x=1.2),
        ]

        scenario = build_backtest_scenario_from_prices(
            prices,
            BacktestConfig(price_data_path="", volatility_threshold=0.05),
        )

        assert len(scenario["events"]) == 1
        assert scenario["price_history"][1]["price"] == 1.2


class TestBacktestConfig:
    """测试回测配置类。"""

    def test_default_config_values(self) -> None:
        """测试默认配置值。"""
        config = BacktestConfig(price_data_path="test.csv")

        assert config.initial_reserve_x == 1000.0
        assert config.initial_reserve_y == 1000.0
        assert config.fee_rate == 0.003
        assert config.volatility_threshold == 0.01
        assert config.trader_balance_x == 1000.0
        assert config.trader_balance_y == 1000.0
        assert config.max_trade_size == 100.0

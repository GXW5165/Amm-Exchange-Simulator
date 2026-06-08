"""历史价格回测模块。

支持从CSV文件导入历史价格数据，按时间序列触发交易事件进行AMM仿真回测。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, TextIO

from src.domain.user import User


@dataclass
class PriceData:
    """历史价格数据点。"""
    timestamp: float
    price_y_per_x: float


@dataclass
class BacktestConfig:
    """回测配置。"""
    price_data_path: str
    initial_reserve_x: float = 1000.0
    initial_reserve_y: float = 1000.0
    fee_rate: float = 0.003
    trader_balance_x: float = 1000.0
    trader_balance_y: float = 1000.0
    volatility_threshold: float = 0.01
    max_trade_size: float = 100.0


def _parse_price_history(reader: csv.DictReader) -> list[PriceData]:
    """把 CSV 行解析为价格序列，并拒绝会破坏回测数学假设的输入。"""
    required_columns = {"timestamp", "price_y_per_x"}
    if reader.fieldnames is None or not required_columns.issubset(set(reader.fieldnames)):
        raise ValueError("Price history CSV must contain timestamp and price_y_per_x columns")

    data: list[PriceData] = []
    for line_number, row in enumerate(reader, start=2):
        try:
            timestamp = float(row["timestamp"])
            price_y_per_x = float(row["price_y_per_x"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid numeric value in price history at line {line_number}") from exc

        if price_y_per_x <= 0:
            raise ValueError(f"price_y_per_x must be positive at line {line_number}")

        data.append(PriceData(timestamp=timestamp, price_y_per_x=price_y_per_x))

    data.sort(key=lambda x: x.timestamp)
    return data


def load_price_history_from_text(csv_text: str) -> list[PriceData]:
    """从 CSV 文本加载历史价格数据，供 Web 上传等内存输入复用。"""
    return _parse_price_history(csv.DictReader(StringIO(csv_text)))


def load_price_history_from_file(file_obj: TextIO) -> list[PriceData]:
    """从已打开的文本文件对象加载历史价格数据。"""
    return _parse_price_history(csv.DictReader(file_obj))


def load_price_history(file_path: str | Path) -> list[PriceData]:
    """从CSV文件加载历史价格数据。

    CSV格式要求：
    - 必须包含 'timestamp' 和 'price_y_per_x' 列
    - 按timestamp升序排列

    Args:
        file_path: CSV文件路径

    Returns:
        价格数据列表，按时间戳排序
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Price history file not found: {file_path}")

    with path.open("r", encoding="utf-8") as f:
        return load_price_history_from_file(f)


def generate_backtest_events(
    price_data: list[PriceData],
    trader_id: str = "backtester",
    volatility_threshold: float = 0.01,
    max_trade_size: float = 100.0
) -> list[dict[str, Any]]:
    """根据价格变化生成回测交易事件。

    当价格变化超过阈值时，生成套利交易事件：
    - 价格上涨：买入X（y_to_x）
    - 价格下跌：卖出X（x_to_y）

    Args:
        price_data: 历史价格数据
        trader_id: 交易者ID
        volatility_threshold: 价格波动阈值（超过此值触发交易）
        max_trade_size: 最大交易金额

    Returns:
        事件配置列表
    """
    events: list[dict[str, Any]] = []
    
    if len(price_data) < 2:
        return events

    for i in range(1, len(price_data)):
        current_price = price_data[i].price_y_per_x
        prev_price = price_data[i-1].price_y_per_x
        timestamp = price_data[i].timestamp

        price_change = abs(current_price - prev_price) / prev_price
        
        if price_change >= volatility_threshold:
            # 根据价格变化方向决定交易方向
            if current_price > prev_price:
                # 价格上涨，X相对低估，买入X
                direction = "y_to_x"
                amount_in = min(max_trade_size, max_trade_size * (current_price - prev_price) / prev_price)
            else:
                # 价格下跌，X相对高估，卖出X
                direction = "x_to_y"
                amount_in = min(max_trade_size, max_trade_size * (prev_price - current_price) / prev_price)

            events.append({
                "timestamp": timestamp,
                "event_type": "swap",
                "user_id": trader_id,
                "direction": direction,
                "amount_in": max(amount_in, 1.0)  # 最小交易金额为1
            })

    return events


def build_backtest_scenario_from_prices(price_data: list[PriceData], config: BacktestConfig) -> dict[str, Any]:
    """根据已加载的价格序列构建回测场景，避免 Web 上传必须落盘。"""
    events = generate_backtest_events(
        price_data,
        trader_id="backtester",
        volatility_threshold=config.volatility_threshold,
        max_trade_size=config.max_trade_size
    )

    return {
        "initial_reserve_x": config.initial_reserve_x,
        "initial_reserve_y": config.initial_reserve_y,
        "fee_rate": config.fee_rate,
        "initial_lp_owner": "protocol",
        "users": {
            "backtester": {
                "balance_x": config.trader_balance_x,
                "balance_y": config.trader_balance_y,
                "lp_shares": 0.0
            }
        },
        "events": events,
        "price_history": [{"timestamp": p.timestamp, "price": p.price_y_per_x} for p in price_data]
    }


def build_backtest_scenario(config: BacktestConfig) -> dict[str, Any]:
    """构建完整的回测场景配置。

    Args:
        config: 回测配置

    Returns:
        完整的场景配置字典
    """
    return build_backtest_scenario_from_prices(load_price_history(config.price_data_path), config)


def run_backtest(config: BacktestConfig, runner) -> Any:
    """执行回测并返回结果。

    Args:
        config: 回测配置
        runner: SimulationRunner实例

    Returns:
        仿真结果
    """
    from src.infrastructure.config_loader import AppConfig

    scenario = build_backtest_scenario(config)
    
    users: dict[str, User] = {}
    for uid, data in scenario["users"].items():
        users[uid] = User(
            user_id=uid,
            balance_x=data["balance_x"],
            balance_y=data["balance_y"],
            lp_shares=data["lp_shares"]
        )

    app_config = AppConfig(
        initial_reserve_x=scenario["initial_reserve_x"],
        initial_reserve_y=scenario["initial_reserve_y"],
        fee_rate=scenario["fee_rate"],
        initial_lp_owner=scenario["initial_lp_owner"],
        users=users,
        events=scenario["events"]
    )

    return runner.run_from_config(app_config)

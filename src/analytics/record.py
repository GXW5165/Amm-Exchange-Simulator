from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class EventRecord:
    """事件执行后的完整快照。

    该结构既服务 CSV 导出，也服务图表和摘要统计。字段分为事件信息、交易信息、
    池状态、用户钱包状态、LP 份额状态和一致性指标，方便报告中复盘每一步。

    注意：invariant_before / invariant_after 记录的是 k = reserve_x * reserve_y。
    在含手续费的恒定乘积模型中，k 会因手续费沉淀而增长，并非数学上的不变量。
    这里保留 "invariant" 命名是为了字段可读性，其本质是"池储备乘积"，用于
    审计每一步前后状态的一致性。
    """

    event_id: int
    timestamp: float
    user_id: str
    event_type: str
    direction: str = ""
    amount_in: Optional[float] = None
    amount_out: Optional[float] = None
    fee: Optional[float] = None
    reserve_x: float = 0.0
    reserve_y: float = 0.0
    spot_price: Optional[float] = None
    execution_price: Optional[float] = None
    slippage_pct: Optional[float] = None
    lp_total_shares: float = 0.0
    reserve_x_before: Optional[float] = None
    reserve_y_before: Optional[float] = None
    reserve_x_after: Optional[float] = None
    reserve_y_after: Optional[float] = None
    wallet_x_before: Optional[float] = None
    wallet_y_before: Optional[float] = None
    wallet_x_after: Optional[float] = None
    wallet_y_after: Optional[float] = None
    lp_shares_before: Optional[float] = None
    lp_shares_after: Optional[float] = None
    amount_x_delta: Optional[float] = None
    amount_y_delta: Optional[float] = None
    lp_shares_delta: Optional[float] = None
    effective_amount_in: Optional[float] = None
    theoretical_price: Optional[float] = None
    spot_price_before: Optional[float] = None
    invariant_before: Optional[float] = None
    invariant_after: Optional[float] = None

    def to_csv_row(self) -> dict[str, Any]:
        """转换成稳定字段顺序的字典，供 CSV、Web 表格和测试复用。"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "direction": self.direction,
            "amount_in": self.amount_in,
            "amount_out": self.amount_out,
            "fee": self.fee,
            "reserve_x": self.reserve_x,
            "reserve_y": self.reserve_y,
            "spot_price": self.spot_price,
            "execution_price": self.execution_price,
            "slippage_pct": self.slippage_pct,
            "lp_total_shares": self.lp_total_shares,
            "reserve_x_before": self.reserve_x_before,
            "reserve_y_before": self.reserve_y_before,
            "reserve_x_after": self.reserve_x_after,
            "reserve_y_after": self.reserve_y_after,
            "wallet_x_before": self.wallet_x_before,
            "wallet_y_before": self.wallet_y_before,
            "wallet_x_after": self.wallet_x_after,
            "wallet_y_after": self.wallet_y_after,
            "lp_shares_before": self.lp_shares_before,
            "lp_shares_after": self.lp_shares_after,
            "amount_x_delta": self.amount_x_delta,
            "amount_y_delta": self.amount_y_delta,
            "lp_shares_delta": self.lp_shares_delta,
            "effective_amount_in": self.effective_amount_in,
            "theoretical_price": self.theoretical_price,
            "spot_price_before": self.spot_price_before,
            "invariant_before": self.invariant_before,
            "invariant_after": self.invariant_after,
        }

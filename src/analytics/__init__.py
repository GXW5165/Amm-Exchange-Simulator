"""分析层导出。

集中暴露事件记录、汇总报告、滑点、无常损失和用户收益计算函数。
"""

from .record import EventRecord
from .report import SimulationSummary, summarize_records
from .impermanent_loss import impermanent_loss_from_price_ratio, impermanent_loss_pct
from .pnl import UserPnL, summarize_user_pnl
from .slippage import average_slippage_pct, calculate_slippage_pct

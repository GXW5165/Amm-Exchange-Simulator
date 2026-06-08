"""分析层导出。

集中暴露事件记录、汇总报告、滑点、无常损失、LP 做市指标、池深度、用户收益计算函数和 PDF 报告生成器。
"""

from .impermanent_loss import impermanent_loss_from_price_ratio, impermanent_loss_pct
from .lp_metrics import LpMetrics, compute_lp_metrics
from .pnl import UserPnL, summarize_user_pnl
from .pool_depth import (
    PoolDepthPoint,
    compute_max_trade_at_2pct,
    compute_max_trade_size_for_slippage,
    compute_pool_depth_curve,
)
from .record import EventRecord
from .report import SimulationSummary, summarize_records
from .report_generator import PDFReportGenerator, generate_experiment_report
from .slippage import average_slippage_pct, calculate_slippage_pct

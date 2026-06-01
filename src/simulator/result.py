from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from src.analytics.record import EventRecord
from src.analytics.report import SimulationSummary, summarize_records
from src.domain.pool import Pool
from src.domain.user import User


@dataclass
class SimulationResult:
    """一次仿真完成后的内存结果。

    records 保存每个事件后的快照；pool/users 是最终状态；initial_pool/
    initial_users 保存初始状态，用于计算无常损失、PnL 和持有基准。
    """

    records: list[EventRecord]
    pool: Pool
    users: dict[str, User]
    initial_pool: Pool
    initial_users: dict[str, User]

    @property
    def summary(self) -> SimulationSummary:
        """按需生成汇总指标，避免在每个事件处理时提前耦合统计逻辑。"""
        return summarize_records(
            records=self.records,
            initial_pool=deepcopy(self.initial_pool),
            current_pool=deepcopy(self.pool),
            initial_users=deepcopy(self.initial_users),
            current_users=deepcopy(self.users),
        )

"""领域层兼容导出。

早期版本把 EventRecord 放在 domain.metrics 中；当前实现已经迁移到
analytics.record，这里保留导入别名，避免旧代码引用失效。
"""

from src.analytics.record import EventRecord

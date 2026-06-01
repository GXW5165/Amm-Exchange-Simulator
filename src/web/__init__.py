"""Web 支撑层导出。

包含 Streamlit 页面使用的数据归一化、配置构造和表格转换函数。
"""

from .app_support import (
    build_config_from_runtime_input,
    build_default_event_rows,
    build_default_user_rows,
    normalize_event_rows,
    normalize_user_rows,
)

__all__ = [
    "build_config_from_runtime_input",
    "build_default_event_rows",
    "build_default_user_rows",
    "normalize_event_rows",
    "normalize_user_rows",
]

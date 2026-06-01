from __future__ import annotations

import logging


def get_logger(name: str = "amm") -> logging.Logger:
    """取得项目日志器。

    函数会避免重复添加 handler，防止在测试或多次创建 CLI 时重复打印日志。
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
    return logger

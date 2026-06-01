from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.analytics.report import SimulationSummary


def export_simulation_summary(summary: SimulationSummary, path: str | Path) -> Path:
    """把仿真摘要导出为 JSON，供报告、Web 下载和验收检查使用。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return output_path

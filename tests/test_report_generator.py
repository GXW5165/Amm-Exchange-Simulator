"""测试 PDF 报告生成模块。"""

from __future__ import annotations

import builtins
import importlib
import importlib.util
import base64
from pathlib import Path

import pytest

from src.analytics.report_generator import (
    PDFReportGenerator,
    ReportAnalysis,
    ReportSummary,
    generate_experiment_report,
)

FPDF_AVAILABLE = importlib.util.find_spec("fpdf") is not None


class TestReportSummary:
    """测试报告摘要数据类。"""

    def test_report_summary_creation(self) -> None:
        """测试创建报告摘要。"""
        summary = ReportSummary(
            total_events=10,
            swap_events=8,
            liquidity_events=2,
            arbitrage_events=0,
            total_fees=1.5,
            total_fees_in_y=1.5,
            average_slippage_pct=0.5,
            max_slippage_pct=2.0,
            impermanent_loss_pct=0.1,
            initial_reserve_x=1000.0,
            initial_reserve_y=1000.0,
            fee_rate=0.003,
        )

        assert summary.total_events == 10
        assert summary.swap_events == 8
        assert summary.total_fees == 1.5
        assert summary.fee_rate == 0.003


class TestReportAnalysis:
    """测试报告分析数据类。"""

    def test_report_analysis_creation(self) -> None:
        """测试创建报告分析。"""
        analysis = ReportAnalysis(
            price_stability="Price remained stable",
            liquidity_depth="Deep liquidity",
            arbitrage_effectiveness="No arbitrage opportunities",
            slippage_analysis="Low slippage",
            fee_income="Moderate fee income",
        )

        assert analysis.price_stability == "Price remained stable"
        assert analysis.liquidity_depth == "Deep liquidity"


@pytest.mark.skipif(not FPDF_AVAILABLE, reason="fpdf2 is required for PDF rendering tests")
class TestPDFReportGenerator:
    """测试 PDF 报告生成器。"""

    def test_generator_initialization(self) -> None:
        """测试生成器初始化。"""
        generator = PDFReportGenerator(title="Test Report")
        assert generator.title == "Test Report"

    def test_add_title_page(self, tmp_path: Path) -> None:
        """测试添加标题页。"""
        generator = PDFReportGenerator()
        summary = ReportSummary(
            total_events=10,
            swap_events=8,
            liquidity_events=2,
            arbitrage_events=0,
            total_fees=1.5,
            total_fees_in_y=1.5,
            average_slippage_pct=0.5,
            max_slippage_pct=2.0,
            impermanent_loss_pct=0.1,
            initial_reserve_x=1000.0,
            initial_reserve_y=1000.0,
            fee_rate=0.003,
        )

        generator._add_title_page(summary)

        # 验证 PDF 已创建页面
        assert len(generator.pdf.pages) == 1

    def test_add_summary_section(self, tmp_path: Path) -> None:
        """测试添加摘要部分。"""
        generator = PDFReportGenerator()
        summary = ReportSummary(
            total_events=10,
            swap_events=8,
            liquidity_events=2,
            arbitrage_events=0,
            total_fees=1.5,
            total_fees_in_y=1.5,
            average_slippage_pct=0.5,
            max_slippage_pct=2.0,
            impermanent_loss_pct=0.1,
            initial_reserve_x=1000.0,
            initial_reserve_y=1000.0,
            fee_rate=0.003,
        )

        generator._add_summary_section(summary)

        # 验证 PDF 已创建页面
        assert len(generator.pdf.pages) == 1

    def test_generate_pdf_output(self, tmp_path: Path) -> None:
        """测试生成 PDF 输出文件。"""
        generator = PDFReportGenerator()
        summary = ReportSummary(
            total_events=10,
            swap_events=8,
            liquidity_events=2,
            arbitrage_events=0,
            total_fees=1.5,
            total_fees_in_y=1.5,
            average_slippage_pct=0.5,
            max_slippage_pct=2.0,
            impermanent_loss_pct=0.1,
            initial_reserve_x=1000.0,
            initial_reserve_y=1000.0,
            fee_rate=0.003,
        )
        analysis = ReportAnalysis(
            price_stability="Stable",
            liquidity_depth="Deep",
            arbitrage_effectiveness="None",
            slippage_analysis="Low",
            fee_income="Moderate",
        )

        output_path = tmp_path / "test_report.pdf"

        generator._add_title_page(summary)
        generator._add_summary_section(summary)
        generator._add_analysis_section(analysis)
        generator.pdf.output(str(output_path))

        # 验证 PDF 文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_chart_section_includes_all_known_png_outputs(self, tmp_path: Path) -> None:
        """测试 PDF 图表章节包含新增的诊断图。"""
        generator = PDFReportGenerator()
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )
        for filename in ["pool_spot_price.png", "candlestick.png", "slippage_volume.png"]:
            (tmp_path / filename).write_bytes(png_bytes)

        generator._add_chart_section(str(tmp_path))

        assert len(generator.pdf.pages) == 3


@pytest.mark.skipif(not FPDF_AVAILABLE, reason="fpdf2 is required for PDF rendering tests")
class TestGenerateExperimentReport:
    """测试生成实验报告函数。"""

    def test_generate_report_with_real_simulation(self, tmp_path: Path) -> None:
        """测试使用真实仿真结果生成报告。"""
        from src.application.simulation_runner import SimulationRunner
        from src.infrastructure.config_loader import load_config

        # 使用默认配置运行仿真
        runner = SimulationRunner(Path(__file__).parent.parent)
        config = load_config(Path(__file__).parent.parent / "configs" / "default.yaml")
        artifacts = runner.run_from_config(config)

        # 创建临时输出目录
        plot_dir = tmp_path / "plots"
        plot_dir.mkdir()
        output_path = tmp_path / "report.pdf"

        # 生成报告（使用 artifacts.result）
        generate_experiment_report(
            result=artifacts.result,
            plot_dir=str(plot_dir),
            output_path=str(output_path),
        )

        # 验证报告文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generate_report_creates_output_directory(self, tmp_path: Path) -> None:
        """测试生成报告时创建输出目录。"""
        from src.application.simulation_runner import SimulationRunner
        from src.infrastructure.config_loader import load_config

        # 使用默认配置运行仿真
        runner = SimulationRunner(Path(__file__).parent.parent)
        config = load_config(Path(__file__).parent.parent / "configs" / "default.yaml")
        artifacts = runner.run_from_config(config)

        # 使用不存在的目录
        output_path = tmp_path / "subdir" / "report.pdf"

        generate_experiment_report(
            result=artifacts.result,
            plot_dir=str(tmp_path),
            output_path=str(output_path),
        )

        # 验证目录和文件已创建
        assert output_path.parent.exists()
        assert output_path.exists()


def test_report_generator_import_is_independent_from_fpdf(monkeypatch: pytest.MonkeyPatch) -> None:
    """缺少 fpdf2 时，模块导入应成功，只有 PDF 生成路径报友好错误。"""

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "fpdf" or name.startswith("fpdf."):
            raise ImportError("blocked fpdf import")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    module = importlib.reload(importlib.import_module("src.analytics.report_generator"))

    with pytest.raises(RuntimeError, match="PDF export requires fpdf2"):
        module.PDFReportGenerator()

    monkeypatch.setattr(builtins, "__import__", real_import)
    importlib.reload(module)

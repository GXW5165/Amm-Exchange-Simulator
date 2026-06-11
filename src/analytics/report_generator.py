"""PDF 实验报告生成模块。

自动分析仿真结果并生成格式化的 PDF 报告，包含图表、统计摘要和事件附录。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.analytics.report import summarize_records
from src.simulator.result import SimulationResult


PRIMARY = (28, 63, 96)
ACCENT = (32, 120, 119)
SOFT_BG = (244, 247, 250)
TEXT = (36, 45, 57)
MUTED = (103, 116, 131)
LINE = (218, 226, 235)
WHITE = (255, 255, 255)


def _load_fpdf() -> tuple[type, Any, Any]:
    """按需加载 PDF 依赖，避免缺少 fpdf2 时影响非 PDF 功能。"""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError as exc:
        raise RuntimeError("PDF export requires fpdf2. Install it with: pip install fpdf2") from exc
    return FPDF, XPos, YPos


def _build_report_pdf_class(fpdf_base: type, x_pos: Any, y_pos: Any) -> type:
    """创建带页眉页脚的 PDF 类；仅在真正生成 PDF 时依赖 fpdf2。"""

    class ReportPDF(fpdf_base):
        """带页眉页脚的报告 PDF 基类。"""

        def __init__(self, title: str) -> None:
            super().__init__()
            self.report_title = title

        def header(self) -> None:
            """渲染页眉。"""
            if self.page_no() == 1:
                return
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*MUTED)
            self.cell(0, 8, self.report_title, new_x=x_pos.LMARGIN, new_y=y_pos.NEXT)
            self.set_draw_color(*LINE)
            self.line(10, 18, 200, 18)
            self.ln(6)

        def footer(self) -> None:
            """渲染页脚页码。"""
            self.set_y(-15)
            self.set_draw_color(*LINE)
            self.line(10, self.get_y(), 200, self.get_y())
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*MUTED)
            self.cell(0, 10, f"Page {self.page_no()}", align="R")

    return ReportPDF


@dataclass
class ReportSummary:
    """报告摘要数据。"""

    total_events: int
    swap_events: int
    liquidity_events: int
    arbitrage_events: int
    total_fees: float
    total_fees_in_y: float
    average_slippage_pct: float
    max_slippage_pct: float
    impermanent_loss_pct: float
    initial_reserve_x: float
    initial_reserve_y: float
    fee_rate: float


@dataclass
class ReportAnalysis:
    """报告分析内容。"""

    price_stability: str
    liquidity_depth: str
    arbitrage_effectiveness: str
    slippage_analysis: str
    fee_income: str


class PDFReportGenerator:
    """PDF 报告生成器。"""

    def __init__(self, title: str = "AMM Exchange Simulation Report") -> None:
        fpdf_base, self.XPos, self.YPos = _load_fpdf()
        report_pdf_cls = _build_report_pdf_class(fpdf_base, self.XPos, self.YPos)
        self.title = title
        self.pdf = report_pdf_cls(title)
        self.pdf.set_auto_page_break(auto=True, margin=18)
        self.pdf.set_margins(left=14, top=14, right=14)
        self.pdf.set_font("Helvetica", "", 11)

    def _safe_text(self, value: Any) -> str:
        """把任意值转换成核心字体可渲染的文本。"""
        return str(value).encode("latin-1", errors="replace").decode("latin-1")

    def _next_cell(
        self,
        width: float,
        height: float,
        text: Any = "",
        *,
        border: int | str = 0,
        align: str = "",
        fill: bool = False,
    ) -> None:
        """写入一个单元格并换到下一行，统一使用 fpdf2 新版换行参数。"""
        self.pdf.cell(
            width,
            height,
            self._safe_text(text),
            border=border,
            align=align,
            fill=fill,
            new_x=self.XPos.LMARGIN,
            new_y=self.YPos.NEXT,
        )

    def _inline_cell(
        self,
        width: float,
        height: float,
        text: Any = "",
        *,
        border: int | str = 0,
        align: str = "",
        fill: bool = False,
    ) -> None:
        """写入一个同行单元格。"""
        self.pdf.cell(
            width,
            height,
            self._safe_text(text),
            border=border,
            align=align,
            fill=fill,
            new_x=self.XPos.RIGHT,
            new_y=self.YPos.TOP,
        )

    def _section_title(self, title: str, subtitle: str | None = None) -> None:
        """渲染章节标题。"""
        self.pdf.set_text_color(*PRIMARY)
        self.pdf.set_font("Helvetica", "B", 17)
        self._next_cell(0, 10, title)
        if subtitle:
            self.pdf.set_font("Helvetica", "", 10)
            self.pdf.set_text_color(*MUTED)
            self.pdf.multi_cell(0, 5, self._safe_text(subtitle))
        self.pdf.ln(4)

    def _metric_card(self, x: float, y: float, width: float, title: str, value: str, note: str = "") -> None:
        """渲染一个紧凑指标卡片。"""
        self.pdf.set_xy(x, y)
        self.pdf.set_fill_color(*SOFT_BG)
        self.pdf.set_draw_color(*LINE)
        self.pdf.rect(x, y, width, 24, style="DF")
        self.pdf.set_xy(x + 4, y + 4)
        self.pdf.set_font("Helvetica", "", 8)
        self.pdf.set_text_color(*MUTED)
        self.pdf.cell(width - 8, 4, self._safe_text(title))
        self.pdf.set_xy(x + 4, y + 10)
        self.pdf.set_font("Helvetica", "B", 13)
        self.pdf.set_text_color(*PRIMARY)
        self.pdf.cell(width - 8, 6, self._safe_text(value))
        if note:
            self.pdf.set_xy(x + 4, y + 18)
            self.pdf.set_font("Helvetica", "", 7)
            self.pdf.set_text_color(*MUTED)
            self.pdf.cell(width - 8, 4, self._safe_text(note))

    def _add_title_page(self, summary: ReportSummary) -> None:
        """添加标题页。"""
        self.pdf.add_page()
        self.pdf.set_fill_color(*PRIMARY)
        self.pdf.rect(0, 0, 210, 62, style="F")

        self.pdf.set_xy(14, 18)
        self.pdf.set_text_color(*WHITE)
        self.pdf.set_font("Helvetica", "B", 25)
        self.pdf.multi_cell(160, 10, self._safe_text(self.title))
        self.pdf.set_x(14)
        self.pdf.set_font("Helvetica", "", 11)
        self._next_cell(0, 7, "Constant-product AMM simulation report")

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.pdf.set_xy(14, 78)
        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(*MUTED)
        self._next_cell(0, 7, f"Generated on: {generated_at}")

        card_y = 98
        card_w = 42
        self._metric_card(14, card_y, card_w, "Total Events", f"{summary.total_events}")
        self._metric_card(60, card_y, card_w, "Swap Events", f"{summary.swap_events}")
        self._metric_card(106, card_y, card_w, "Total Fees", f"{summary.total_fees:.4f}")
        self._metric_card(152, card_y, card_w, "Fee Rate", f"{summary.fee_rate * 100:.2f}%")

        self.pdf.set_xy(14, 138)
        self._section_title("Model Setup")
        setup_rows = [
            ("AMM model", "Constant product (x*y=k)"),
            ("Initial reserve X", f"{summary.initial_reserve_x:.2f}"),
            ("Initial reserve Y", f"{summary.initial_reserve_y:.2f}"),
            ("Report scope", "Summary metrics, analysis notes, charts, and event appendix"),
        ]
        self._table(setup_rows, label_width=52)

    def _add_summary_section(self, summary: ReportSummary) -> None:
        """添加摘要部分。"""
        self.pdf.add_page()
        self._section_title(
            "Executive Summary",
            "A compact view of throughput, fee generation, slippage, and LP risk indicators.",
        )

        card_y = self.pdf.get_y()
        card_w = 58
        self._metric_card(14, card_y, card_w, "Total Fees in Y", f"{summary.total_fees_in_y:.4f}")
        self._metric_card(76, card_y, card_w, "Average Slippage", f"{summary.average_slippage_pct:.2f}%")
        self._metric_card(138, card_y, card_w, "Max Slippage", f"{summary.max_slippage_pct:.2f}%")
        self.pdf.set_y(card_y + 34)

        rows = [
            ("Total events", f"{summary.total_events}"),
            ("Swap events", f"{summary.swap_events}"),
            ("Liquidity events", f"{summary.liquidity_events}"),
            ("Arbitrage events", f"{summary.arbitrage_events}"),
            ("Impermanent loss", f"{summary.impermanent_loss_pct:.2f}%"),
        ]
        self._table(rows, label_width=58)

    def _add_analysis_section(self, analysis: ReportAnalysis) -> None:
        """添加分析部分。"""
        self.pdf.add_page()
        self._section_title(
            "Analytical Notes",
            "Automatically generated interpretation of the simulation outcome.",
        )

        analyses = [
            ("Price Stability", analysis.price_stability),
            ("Liquidity Depth", analysis.liquidity_depth),
            ("Arbitrage Effectiveness", analysis.arbitrage_effectiveness),
            ("Slippage", analysis.slippage_analysis),
            ("Fee Income", analysis.fee_income),
        ]

        for title, content in analyses:
            self.pdf.set_fill_color(*SOFT_BG)
            self.pdf.set_draw_color(*LINE)
            x = self.pdf.get_x()
            y = self.pdf.get_y()
            self.pdf.rect(x, y, 182, 10, style="DF")
            self.pdf.set_xy(x + 3, y + 2)
            self.pdf.set_text_color(*PRIMARY)
            self.pdf.set_font("Helvetica", "B", 11)
            self.pdf.cell(176, 5, self._safe_text(title))
            self.pdf.set_xy(x + 3, y + 12)
            self.pdf.set_text_color(*TEXT)
            self.pdf.set_font("Helvetica", "", 10)
            self.pdf.multi_cell(176, 5.4, self._safe_text(content))
            self.pdf.ln(4)

    def _add_chart_section(self, plot_dir: str) -> None:
        """添加图表部分。"""
        plot_dir_path = Path(plot_dir)
        charts = [
            ("Pool Spot Price", "pool_spot_price.png", "Spot price movement across processed events."),
            ("Pool Reserves", "pool_reserves.png", "Token reserve changes caused by swaps and liquidity events."),
            ("Swap Slippage", "swap_slippage.png", "Execution slippage observed for swap events."),
            ("Cumulative Fees", "cumulative_fees.png", "Fee accumulation over the simulation timeline."),
            ("User PnL", "user_total_pnl.png", "Final user-level profit and loss in Token Y terms."),
        ]

        existing = [(title, plot_dir_path / filename, caption) for title, filename, caption in charts if (plot_dir_path / filename).exists()]
        if not existing:
            return

        self.pdf.add_page()
        self._section_title("Charts", "Visual diagnostics generated by the simulator.")

        for index, (title, chart_path, caption) in enumerate(existing):
            if index > 0:
                self.pdf.add_page()
                self._section_title("Charts")
            self.pdf.set_text_color(*PRIMARY)
            self.pdf.set_font("Helvetica", "B", 13)
            self._next_cell(0, 7, title)
            self.pdf.image(str(chart_path), x=16, y=self.pdf.get_y() + 2, w=178)
            self.pdf.set_y(230)
            self.pdf.set_font("Helvetica", "", 9)
            self.pdf.set_text_color(*MUTED)
            self.pdf.multi_cell(0, 5, self._safe_text(caption))

    def _add_event_log_section(self, records: list[dict]) -> None:
        """添加事件日志部分。"""
        self.pdf.add_page()
        self._section_title("Event Appendix", "First 50 processed events with key execution fields.")

        headers = ["Time", "Type", "User", "Direction", "Amount In", "Amount Out", "Fee"]
        col_widths = [20, 29, 26, 28, 29, 29, 21]
        self.pdf.set_font("Helvetica", "B", 8)
        self.pdf.set_fill_color(*PRIMARY)
        self.pdf.set_text_color(*WHITE)
        self.pdf.set_draw_color(*PRIMARY)
        for header, width in zip(headers, col_widths):
            self._inline_cell(width, 8, header, border=1, align="C", fill=True)
        self.pdf.ln(8)

        self.pdf.set_font("Helvetica", "", 7.5)
        self.pdf.set_text_color(*TEXT)
        self.pdf.set_draw_color(*LINE)
        for index, record in enumerate(records[:50]):
            fill = index % 2 == 0
            self.pdf.set_fill_color(*(SOFT_BG if fill else WHITE))
            row = [
                f"{record.get('timestamp', 0):.1f}",
                record.get("event_type", ""),
                record.get("user_id", ""),
                record.get("direction", ""),
                self._format_optional_float(record.get("amount_in"), 2),
                self._format_optional_float(record.get("amount_out"), 2),
                self._format_optional_float(record.get("fee"), 4),
            ]
            for value, width in zip(row, col_widths):
                self._inline_cell(width, 7, value, border=1, align="C", fill=fill)
            self.pdf.ln(7)

        if len(records) > 50:
            self.pdf.ln(3)
            self.pdf.set_text_color(*MUTED)
            self.pdf.set_font("Helvetica", "", 9)
            self._next_cell(0, 6, f"... and {len(records) - 50} more events")

    def _table(self, rows: list[tuple[str, str]], *, label_width: float) -> None:
        """渲染两列表格。"""
        value_width = 182 - label_width
        self.pdf.set_draw_color(*LINE)
        for index, (label, value) in enumerate(rows):
            self.pdf.set_fill_color(*(SOFT_BG if index % 2 == 0 else WHITE))
            self.pdf.set_font("Helvetica", "B", 9)
            self.pdf.set_text_color(*PRIMARY)
            self._inline_cell(label_width, 8, label, border=1, fill=True)
            self.pdf.set_font("Helvetica", "", 9)
            self.pdf.set_text_color(*TEXT)
            self._inline_cell(value_width, 8, value, border=1, fill=True)
            self.pdf.ln(8)
        self.pdf.ln(4)

    def _format_optional_float(self, value: Any, precision: int) -> str:
        """格式化可空数字字段。"""
        if value is None or value == "":
            return "-"
        return f"{float(value):.{precision}f}"

    def generate(self, result: SimulationResult, plot_dir: str, output_path: str) -> str:
        """生成完整的 PDF 报告。

        Args:
            result: 仿真结果
            plot_dir: 图表目录路径
            output_path: 输出 PDF 文件路径

        Returns:
            生成的 PDF 文件路径
        """
        summary_records = summarize_records(
            records=result.records,
            initial_pool=result.initial_pool,
            current_pool=result.pool,
            initial_users=result.initial_users,
            current_users=result.users,
        )

        arbitrage_events = sum(1 for r in result.records if r.event_type == "arbitrage")
        summary = ReportSummary(
            total_events=summary_records.total_events,
            swap_events=summary_records.swap_events,
            liquidity_events=summary_records.liquidity_events,
            arbitrage_events=arbitrage_events,
            total_fees=summary_records.total_fees,
            total_fees_in_y=summary_records.total_fees_in_y,
            average_slippage_pct=summary_records.average_slippage_pct or 0.0,
            max_slippage_pct=summary_records.max_slippage_pct or 0.0,
            impermanent_loss_pct=summary_records.impermanent_loss_pct or 0.0,
            initial_reserve_x=result.initial_pool.reserve_x if result.initial_pool else 0,
            initial_reserve_y=result.initial_pool.reserve_y if result.initial_pool else 0,
            fee_rate=result.pool.fee_rate,
        )

        metrics_dict = {
            "processed_events": summary_records.total_events,
            "swap_events": summary_records.swap_events,
            "liquidity_events": summary_records.liquidity_events,
            "arbitrage_events": arbitrage_events,
            "total_fees": summary_records.total_fees,
            "total_fees_in_y": summary_records.total_fees_in_y,
            "average_slippage_pct": summary_records.average_slippage_pct or 0.0,
            "max_slippage_pct": summary_records.max_slippage_pct or 0.0,
            "impermanent_loss_pct": summary_records.impermanent_loss_pct or 0.0,
        }
        analysis = self._analyze_results(result, metrics_dict)

        self._add_title_page(summary)
        self._add_summary_section(summary)
        self._add_analysis_section(analysis)
        self._add_chart_section(plot_dir)
        self._add_event_log_section([r.to_csv_row() for r in result.records])

        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        self.pdf.output(str(output_path_obj))
        return str(output_path_obj)

    def _analyze_results(self, result: SimulationResult, metrics: dict) -> ReportAnalysis:
        """分析仿真结果并生成分析报告。"""
        price_changes = []
        prev_price = None
        for record in result.records:
            if record.spot_price_before and record.spot_price:
                if prev_price:
                    change = abs(record.spot_price - prev_price) / prev_price * 100
                    price_changes.append(change)
                prev_price = record.spot_price

        avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
        if avg_price_change < 1:
            price_stability = f"High price stability maintained. Average price change per event: {avg_price_change:.2f}%."
        elif avg_price_change < 5:
            price_stability = f"Moderate price stability. Average price change per event: {avg_price_change:.2f}%. Consider increasing liquidity."
        else:
            price_stability = f"High price volatility observed. Average price change per event: {avg_price_change:.2f}%. Significant slippage may occur."

        initial_liquidity = result.initial_pool.reserve_x + result.initial_pool.reserve_y if result.initial_pool else 0
        final_liquidity = result.pool.reserve_x + result.pool.reserve_y
        if initial_liquidity > 0:
            liquidity_change = (final_liquidity - initial_liquidity) / initial_liquidity * 100
            liquidity_depth = f"Initial liquidity: {initial_liquidity:.2f} tokens. "
            liquidity_depth += f"Final liquidity: {final_liquidity:.2f} tokens. "
            liquidity_depth += f"Net change: {liquidity_change:+.2f}%. "
            liquidity_depth += "Liquidity inflow observed during simulation." if liquidity_change > 0 else "Liquidity outflow observed during simulation."
        else:
            liquidity_depth = f"Initial liquidity is zero. Final liquidity: {final_liquidity:.2f} tokens."

        arbitrage_count = sum(1 for r in result.records if r.event_type == "arbitrage")
        if arbitrage_count > 0:
            arbitrage_effectiveness = f"{arbitrage_count} arbitrage event(s) executed. Arbitrage helps maintain price alignment with external markets."
        else:
            arbitrage_effectiveness = "No arbitrage events executed during simulation."

        slippage = metrics["average_slippage_pct"]
        if slippage < 1:
            slippage_analysis = f"Low average slippage: {slippage:.2f}%. Market is efficient with good liquidity."
        elif slippage < 5:
            slippage_analysis = f"Moderate average slippage: {slippage:.2f}%. Acceptable for most trading activities."
        else:
            slippage_analysis = f"High average slippage: {slippage:.2f}%. Consider adding more liquidity or reducing trade sizes."

        fees = metrics["total_fees"]
        fee_rate = result.pool.fee_rate * 100
        fee_income = f"Total fees earned: {fees:.4f} tokens at {fee_rate:.2f}% fee rate. "
        fee_income += f"This represents {metrics['swap_events']} swap transactions generating fee revenue."

        return ReportAnalysis(
            price_stability=price_stability,
            liquidity_depth=liquidity_depth,
            arbitrage_effectiveness=arbitrage_effectiveness,
            slippage_analysis=slippage_analysis,
            fee_income=fee_income,
        )


def generate_experiment_report(result: SimulationResult, plot_dir: str, output_path: str) -> str:
    """生成实验报告的便捷函数。"""
    generator = PDFReportGenerator("AMM Exchange Simulator - Experiment Report")
    return generator.generate(result, plot_dir, output_path)

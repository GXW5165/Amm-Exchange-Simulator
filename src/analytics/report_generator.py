"""PDF 实验报告生成模块。

自动分析仿真结果并生成格式化的 PDF 报告，包含图表和统计分析。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from fpdf2 import FPDF
except ImportError:
    from fpdf import FPDF
from matplotlib import pyplot as plt

from src.analytics.report import summarize_records
from src.simulator.result import SimulationResult


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
        self.title = title
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        # 使用默认字体（避免外部字体文件依赖）
        self.pdf.set_font('Helvetica', '', 12)

    def _add_title_page(self, summary: ReportSummary) -> None:
        """添加标题页。"""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', 'B', 24)
        self.pdf.cell(0, 40, self.title, ln=True, align='C')
        self.pdf.set_font('Helvetica', '', 14)
        self.pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        self.pdf.cell(0, 10, f"AMM Model: Constant Product (x*y=k)", ln=True, align='C')
        self.pdf.cell(0, 10, f"Initial Reserves: X={summary.initial_reserve_x:.2f}, Y={summary.initial_reserve_y:.2f}", ln=True, align='C')
        self.pdf.cell(0, 10, f"Fee Rate: {summary.fee_rate * 100:.2f}%", ln=True, align='C')
        self.pdf.ln(20)

    def _add_summary_section(self, summary: ReportSummary) -> None:
        """添加摘要部分。"""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', '', 18)
        self.pdf.cell(0, 15, "Executive Summary", ln=True)
        self.pdf.set_font('Helvetica', '', 12)
        
        summary_data = [
            ("Total Events", f"{summary.total_events}"),
            ("Swap Events", f"{summary.swap_events}"),
            ("Liquidity Events", f"{summary.liquidity_events}"),
            ("Arbitrage Events", f"{summary.arbitrage_events}"),
            ("Total Fees Earned", f"{summary.total_fees:.4f}"),
            ("Total Fees (in Y)", f"{summary.total_fees_in_y:.4f}"),
            ("Average Slippage", f"{summary.average_slippage_pct:.2f}%"),
            ("Maximum Slippage", f"{summary.max_slippage_pct:.2f}%"),
            ("Impermanent Loss", f"{summary.impermanent_loss_pct:.2f}%"),
        ]
        
        col_width = self.pdf.w / 2 - 10
        for label, value in summary_data:
            self.pdf.cell(col_width, 8, label)
            self.pdf.cell(col_width, 8, value, ln=True)
        self.pdf.ln(10)

    def _add_analysis_section(self, analysis: ReportAnalysis) -> None:
        """添加分析部分。"""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', '', 18)
        self.pdf.cell(0, 15, "Analysis", ln=True)
        self.pdf.set_font('Helvetica', '', 12)
        
        analyses = [
            ("Price Stability", analysis.price_stability),
            ("Liquidity Depth", analysis.liquidity_depth),
            ("Arbitrage Effectiveness", analysis.arbitrage_effectiveness),
            ("Slippage Analysis", analysis.slippage_analysis),
            ("Fee Income", analysis.fee_income),
        ]
        
        for title, content in analyses:
            self.pdf.set_font('Helvetica', '', 14)
            self.pdf.cell(0, 10, f"- {title}", ln=True)
            self.pdf.set_font('Helvetica', '', 12)
            self.pdf.multi_cell(0, 8, content)
            self.pdf.ln(5)

    def _add_chart_section(self, plot_dir: str) -> None:
        """添加图表部分。"""
        plot_dir_path = Path(plot_dir)
        charts = [
            ("Pool Spot Price", "pool_spot_price.png"),
            ("Pool Reserves", "pool_reserves.png"),
            ("Swap Slippage", "swap_slippage.png"),
            ("Cumulative Fees", "cumulative_fees.png"),
            ("User PnL", "user_total_pnl.png"),
        ]
        
        for title, filename in charts:
            chart_path = plot_dir_path / filename
            if chart_path.exists():
                self.pdf.add_page()
                self.pdf.set_font('Helvetica', '', 16)
                self.pdf.cell(0, 10, f"{title}", ln=True)
                self.pdf.image(str(chart_path), x=10, y=30, w=180)

    def _add_event_log_section(self, records: list[dict]) -> None:
        """添加事件日志部分。"""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', '', 18)
        self.pdf.cell(0, 15, "Event Log", ln=True)
        self.pdf.set_font('Helvetica', '', 10)
        
        # 表头
        headers = ["Time", "Type", "User", "Direction", "Amount In", "Amount Out", "Fee"]
        col_widths = [25, 30, 25, 30, 25, 25, 20]
        
        for i, header in enumerate(headers):
            self.pdf.cell(col_widths[i], 8, header, border=1)
        self.pdf.ln()
        
        # 数据行
        for record in records[:50]:  # 最多显示50条记录
            self.pdf.cell(col_widths[0], 8, f"{record['timestamp']:.1f}", border=1)
            self.pdf.cell(col_widths[1], 8, record.get('event_type', ''), border=1)
            self.pdf.cell(col_widths[2], 8, record.get('user_id', ''), border=1)
            self.pdf.cell(col_widths[3], 8, record.get('direction', ''), border=1)
            self.pdf.cell(col_widths[4], 8, f"{record.get('amount_in', 0):.2f}", border=1)
            self.pdf.cell(col_widths[5], 8, f"{record.get('amount_out', 0):.2f}", border=1)
            self.pdf.cell(col_widths[6], 8, f"{record.get('fee', 0):.4f}", border=1)
            self.pdf.ln()
        
        if len(records) > 50:
            self.pdf.cell(0, 8, f"... and {len(records) - 50} more events", ln=True)

    def generate(self, result: SimulationResult, plot_dir: str, output_path: str) -> str:
        """生成完整的 PDF 报告。
        
        Args:
            result: 仿真结果
            plot_dir: 图表目录路径
            output_path: 输出 PDF 文件路径
            
        Returns:
            生成的 PDF 文件路径
        """
        # 计算指标
        summary_records = summarize_records(
            records=result.records,
            initial_pool=result.initial_pool,
            current_pool=result.pool,
            initial_users=result.initial_users,
            current_users=result.users,
        )
        
        # 计算套利事件数量
        arbitrage_events = sum(1 for r in result.records if r.event_type == 'arbitrage')
        
        # 构建摘要
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
        
        # 构建分析
        metrics_dict = {
            'processed_events': summary_records.total_events,
            'swap_events': summary_records.swap_events,
            'liquidity_events': summary_records.liquidity_events,
            'arbitrage_events': arbitrage_events,
            'total_fees': summary_records.total_fees,
            'total_fees_in_y': summary_records.total_fees_in_y,
            'average_slippage_pct': summary_records.average_slippage_pct or 0.0,
            'max_slippage_pct': summary_records.max_slippage_pct or 0.0,
            'impermanent_loss_pct': summary_records.impermanent_loss_pct or 0.0,
        }
        analysis = self._analyze_results(result, metrics_dict)
        
        # 生成 PDF
        self._add_title_page(summary)
        self._add_summary_section(summary)
        self._add_analysis_section(analysis)
        self._add_chart_section(plot_dir)
        
        # 转换记录为字典列表
        records = [r.to_csv_row() for r in result.records]
        self._add_event_log_section(records)
        
        # 确保输出目录存在
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        self.pdf.output(str(output_path_obj))
        return str(output_path_obj)

    def _analyze_results(self, result: SimulationResult, metrics: dict) -> ReportAnalysis:
        """分析仿真结果并生成分析报告。"""
        # 价格稳定性分析
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
        
        # 流动性深度分析
        initial_liquidity = result.initial_pool.reserve_x + result.initial_pool.reserve_y if result.initial_pool else 0
        final_liquidity = result.pool.reserve_x + result.pool.reserve_y
        liquidity_change = (final_liquidity - initial_liquidity) / initial_liquidity * 100
        
        liquidity_depth = f"Initial liquidity: {initial_liquidity:.2f} tokens. "
        liquidity_depth += f"Final liquidity: {final_liquidity:.2f} tokens. "
        liquidity_depth += f"Net change: {liquidity_change:+.2f}%. "
        if liquidity_change > 0:
            liquidity_depth += "Liquidity inflow observed during simulation."
        else:
            liquidity_depth += "Liquidity outflow observed during simulation."
        
        # 套利有效性分析
        arbitrage_count = sum(1 for r in result.records if r.event_type == 'arbitrage')
        if arbitrage_count > 0:
            arbitrage_effectiveness = f"{arbitrage_count} arbitrage event(s) executed. "
            arbitrage_effectiveness += f"Arbitrage helps maintain price alignment with external markets."
        else:
            arbitrage_effectiveness = "No arbitrage events executed during simulation."
        
        # 滑点分析
        slippage = metrics['average_slippage_pct']
        if slippage < 1:
            slippage_analysis = f"Low average slippage: {slippage:.2f}%. Market is efficient with good liquidity."
        elif slippage < 5:
            slippage_analysis = f"Moderate average slippage: {slippage:.2f}%. Acceptable for most trading activities."
        else:
            slippage_analysis = f"High average slippage: {slippage:.2f}%. Consider adding more liquidity or reducing trade sizes."
        
        # 手续费收入分析
        fees = metrics['total_fees']
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
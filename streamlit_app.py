from __future__ import annotations

"""Streamlit Web 入口。

页面提供两个工作流：默认配置一键运行，以及自定义池参数、用户和事件序列后
运行仿真。核心计算仍由 application/simulator/amm 层完成，Web 层只负责输入、
展示和下载。
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.application.simulation_runner import SimulationRunner
from src.infrastructure.config_loader import load_config
from src.web.app_support import (
    build_config_from_runtime_input,
    build_default_event_rows,
    build_default_user_rows,
    normalize_event_rows,
    normalize_user_rows,
    user_pnl_rows,
    validate_runtime_input,
)


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "configs" / "default.yaml"


def _read_bytes(path: Path) -> bytes:
    """读取导出文件字节，用于 Streamlit 下载按钮。"""
    return path.read_bytes()


def _show_result(artifacts, *, section_key: str) -> None:
    """展示一次仿真的摘要、事件表、PnL、下载按钮和图表。"""
    summary = artifacts.result.summary
    st.subheader("Summary")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Total Events", summary.total_events)
    metric_columns[1].metric("Swap Events", summary.swap_events)
    metric_columns[2].metric("Liquidity Events", summary.liquidity_events)
    metric_columns[3].metric("Total Fees", f"{summary.total_fees:.6f}")

    metric_columns = st.columns(4)
    metric_columns[0].metric(
        "Average Slippage (%)",
        "N/A" if summary.average_slippage_pct is None else f"{summary.average_slippage_pct:.6f}",
    )
    metric_columns[1].metric(
        "Max Slippage (%)",
        "N/A" if summary.max_slippage_pct is None else f"{summary.max_slippage_pct:.6f}",
    )
    metric_columns[2].metric(
        "Impermanent Loss (%)",
        "N/A" if summary.impermanent_loss_pct is None else f"{summary.impermanent_loss_pct:.6f}",
    )
    metric_columns[3].metric("Total Fees (Y)", f"{summary.total_fees_in_y:.6f}")

    if artifacts.warnings:
        for warning in artifacts.warnings:
            st.warning(warning)

    st.subheader("Event Records")
    records_df = pd.DataFrame([record.to_csv_row() for record in artifacts.result.records])
    st.dataframe(records_df, width="stretch")

    st.subheader("User PnL")
    pnl_df = pd.DataFrame(user_pnl_rows(summary.user_pnl))
    st.dataframe(pnl_df, width="stretch")

    st.subheader("Downloads")
    download_columns = st.columns(2)
    download_columns[0].download_button(
        "Download CSV Log",
        data=_read_bytes(artifacts.csv_path),
        file_name=artifacts.csv_path.name,
        mime="text/csv",
        key=f"{section_key}_download_csv",
    )
    download_columns[1].download_button(
        "Download JSON Summary",
        data=_read_bytes(artifacts.summary_path),
        file_name=artifacts.summary_path.name,
        mime="application/json",
        key=f"{section_key}_download_json",
    )

    if artifacts.plot_paths:
        st.subheader("Charts")
        for name, path in artifacts.plot_paths.items():
            st.image(str(path), caption=name, width="stretch")

    with st.expander("View Raw JSON Summary"):
        st.code(Path(artifacts.summary_path).read_text(encoding="utf-8"), language="json")


def _run_default_config() -> None:
    """默认配置运行页签。"""
    st.subheader("Default Config Simulation")
    if st.button("Run Default Config", width="stretch"):
        config = load_config(DEFAULT_CONFIG_PATH)
        runner = SimulationRunner(ROOT_DIR)
        st.session_state["default_artifacts"] = runner.run_from_config(config)

    artifacts = st.session_state.get("default_artifacts")
    if artifacts is not None:
        _show_result(artifacts, section_key="default")


def _run_custom_simulation() -> None:
    """自定义参数运行页签。"""
    st.subheader("Custom Simulation")
    default_config = load_config(DEFAULT_CONFIG_PATH)

    left, right = st.columns([1, 1.2])
    with left:
        initial_reserve_x = st.number_input(
            "Initial Token X Reserve",
            min_value=0.0,
            value=float(default_config.initial_reserve_x),
            step=10.0,
        )
        initial_reserve_y = st.number_input(
            "Initial Token Y Reserve",
            min_value=0.0,
            value=float(default_config.initial_reserve_y),
            step=10.0,
        )
        fee_rate = st.number_input(
            "Fee Rate",
            min_value=0.0,
            max_value=1.0,
            value=float(default_config.fee_rate),
            step=0.001,
            format="%.6f",
        )

    with right:
        st.caption("Initial Users")
        user_rows = st.data_editor(
            build_default_user_rows(default_config.users),
            num_rows="dynamic",
            width="stretch",
            key="user_rows_editor",
        )

    st.caption("Event Sequence")
    event_rows = st.data_editor(
        build_default_event_rows(default_config.events),
        num_rows="dynamic",
        width="stretch",
        key="event_rows_editor",
        column_config={
            "event_type": st.column_config.SelectboxColumn(
                "event_type",
                options=["swap", "add_liquidity", "remove_liquidity"],
            ),
            "direction": st.column_config.SelectboxColumn(
                "direction",
                options=["x_to_y", "y_to_x"],
            ),
        },
    )

    if st.button("Run Custom Simulation", type="primary", width="stretch"):
        users = normalize_user_rows(user_rows)
        events = normalize_event_rows(event_rows)
        validation = validate_runtime_input(
            initial_reserve_x=initial_reserve_x,
            initial_reserve_y=initial_reserve_y,
            fee_rate=fee_rate,
            users=users,
            events=events,
        )
        if not validation.ok:
            for error in validation.errors:
                st.error(error)
            return

        config = build_config_from_runtime_input(
            initial_reserve_x=initial_reserve_x,
            initial_reserve_y=initial_reserve_y,
            fee_rate=fee_rate,
            users=users,
            events=events,
        )
        runner = SimulationRunner(ROOT_DIR)
        try:
            artifacts = runner.run_from_config(config)
        except Exception as exc:
            st.exception(exc)
            return
        st.session_state["custom_artifacts"] = artifacts

    artifacts = st.session_state.get("custom_artifacts")
    if artifacts is not None:
        _show_result(artifacts, section_key="custom")


def main() -> None:
    """Streamlit 应用入口。"""
    st.set_page_config(
        page_title="AMM Exchange Simulator",
        page_icon="📈",
        layout="wide",
    )
    st.title("AMM Exchange Simulator")
    st.caption("Streamlit web interface for the existing simulation engine")

    tab_default, tab_custom = st.tabs(["Default Config", "Custom Simulation"])
    with tab_default:
        _run_default_config()
    with tab_custom:
        _run_custom_simulation()


if __name__ == "__main__":
    main()

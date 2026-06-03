from __future__ import annotations

"""Streamlit entry point for the AMM simulator."""

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from src.application.simulation_runner import SimulationRunner
from src.infrastructure.config_loader import load_config
from src.web.app_support import (
    build_config_from_runtime_input,
    build_default_event_rows,
    build_default_user_rows,
    cleanup_old_web_runs,
    delete_saved_config,
    list_saved_configs,
    load_saved_config,
    normalize_event_rows,
    normalize_user_rows,
    save_config_to_yaml,
    user_pnl_rows,
    validate_runtime_input,
)

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "configs" / "default.yaml"


def _read_bytes(path: Path) -> bytes:
    """读取导出文件字节，用于 Streamlit 下载按钮。"""
    return path.read_bytes()


def _show_result(artifacts, *, section_key: str) -> None:
    """展示一次仿真的摘要、事件表、PnL、下载按钮和 2x3 图表网格。"""
    summary = artifacts.result.summary

    # ── 摘要指标 ──
    st.subheader("Summary")
    cols = st.columns(4)
    cols[0].metric("Total Events", summary.total_events)
    cols[1].metric("Swap Events", summary.swap_events)
    cols[2].metric("Liquidity Events", summary.liquidity_events)
    cols[3].metric("Total Fees", f"{summary.total_fees:.6f}")

    cols = st.columns(4)
    cols[0].metric(
        "Avg Slippage (%)",
        "N/A" if summary.average_slippage_pct is None else f"{summary.average_slippage_pct:.6f}",
    )
    cols[1].metric(
        "Max Slippage (%)",
        "N/A" if summary.max_slippage_pct is None else f"{summary.max_slippage_pct:.6f}",
    )
    cols[2].metric(
        "Imp. Loss (%)",
        "N/A" if summary.impermanent_loss_pct is None else f"{summary.impermanent_loss_pct:.6f}",
    )
    cols[3].metric("Fees in Y", f"{summary.total_fees_in_y:.6f}")

    # ── 新增：LP 收益和池深度指标 ──
    cols = st.columns(4)
    # 找到有 LP 的用户中最好的年化收益率
    lp_returns = summary.lp_annualized_returns or {}
    best_lp = max(lp_returns.values(), key=lambda v: v if v is not None else float("-inf"), default=None)
    cols[0].metric(
        "Best LP APY (%)",
        "N/A" if best_lp is None else f"{best_lp:.6f}",
    )
    cols[1].metric(
        "Pool Depth @2%",
        "N/A" if summary.pool_depth_at_2pct is None else f"{summary.pool_depth_at_2pct:.6f}",
    )
    cols[2].metric(
        "IL Amount (Y)",
        "N/A" if summary.impermanent_loss_amount_in_y is None else f"{summary.impermanent_loss_amount_in_y:.6f}",
    )
    cols[3].metric("Time Span (days)", f"{summary.time_span_days:.4f}")

    # ── 事件表 ──
    st.subheader("Event Records")
    records_df = pd.DataFrame([r.to_csv_row() for r in artifacts.result.records])
    st.dataframe(records_df, use_container_width=True, hide_index=True)

    # ── 用户 PnL ──
    st.subheader("User PnL")
    pnl_df = pd.DataFrame(user_pnl_rows(summary.user_pnl))
    st.dataframe(pnl_df, use_container_width=True, hide_index=True)

    # ── 新增：PnL 拆分明细（可展开） ──
    with st.expander("📊 Detailed PnL Breakdown", expanded=False):
        pnl_breakdown_rows = []
        for uid, pnl in summary.user_pnl.items():
            pnl_breakdown_rows.append({
                "User": uid,
                "Wallet PnL (Y)": f"{pnl.wallet_pnl_in_y:.6f}",
                "LP Position PnL (Y)": f"{pnl.lp_position_value_in_y:.6f}",
                "Fee Net Income (Y)": f"{pnl.fee_net_income_in_y:.6f}",
                "IL Loss (Y)": f"{pnl.il_loss_in_y:.6f}",
                "Total PnL (Y)": f"{pnl.total_pnl_in_y:.6f}",
                "LP vs Hold (Y)": f"{pnl.lp_vs_hold_pnl_in_y:.6f}",
            })
        if pnl_breakdown_rows:
            st.dataframe(
                pd.DataFrame(pnl_breakdown_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "**LP Position PnL** = value change of LP shares from price movement alone.  "
                "**Fee Net Income** = LP's pro-rata share of swap fees.  "
                "**IL Loss** = impermanent loss in Token Y.  "
                "**LP vs Hold** = PnL if LP'd vs HODLed since start."
            )

    # ── 下载 ──
    st.subheader("Downloads")
    dl_cols = st.columns(3)
    dl_cols[0].download_button(
        "📥 Download CSV Log",
        data=_read_bytes(artifacts.csv_path),
        file_name=artifacts.csv_path.name,
        mime="text/csv",
        key=f"{section_key}_dl_csv",
    )
    dl_cols[1].download_button(
        "📥 Download JSON Summary",
        data=_read_bytes(artifacts.summary_path),
        file_name=artifacts.summary_path.name,
        mime="application/json",
        key=f"{section_key}_dl_json",
    )
    # ── 新增：Excel 导出 ──
    try:
        from src.infrastructure.excel_exporter import export_to_excel
        xlsx_path = artifacts.csv_path.with_suffix(".xlsx")
        export_to_excel(artifacts, xlsx_path)
        dl_cols[2].download_button(
            "📥 Download Excel Report",
            data=_read_bytes(xlsx_path),
            file_name=xlsx_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{section_key}_dl_xlsx",
        )
    except Exception as exc:
        artifacts.warnings.append(f"Excel export failed: {exc}")
        dl_cols[2].caption("Excel export unavailable")

    if artifacts.warnings:
        for warning in artifacts.warnings:
            st.warning(warning)

    # ── 图表 2×3 网格 ──
    if artifacts.plot_paths:
        st.subheader("Charts")
        names = sorted(artifacts.plot_paths.keys())
        for i in range(0, len(names), 2):
            row_cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx >= len(names):
                    break
                name = names[idx]
                path = artifacts.plot_paths[name]
                row_cols[j].image(str(path), caption=name, use_container_width=True)

    with st.expander("View Raw JSON Summary"):
        st.code(Path(artifacts.summary_path).read_text(encoding="utf-8"), language="json")


# ── 保存/加载配置的 UI 辅助 ──────────────────────────────────────────


def _render_save_load_ui(
    *,
    section_key: str,
    initial_reserve_x: float,
    initial_reserve_y: float,
    fee_rate: float,
    initial_lp_owner: str | None,
    user_rows: list[dict],
    event_rows: list[dict],
) -> None:
    """渲染保存配置和加载/删除已保存配置的 UI 组件。"""
    saved_names = list_saved_configs()

    save_col, load_col, _ = st.columns([1, 1.5, 0.5])

    # ── 保存 ──
    with save_col:
        config_name = st.text_input(
            "Config name to save",
            value="",
            placeholder="e.g. my_scenario",
            key=f"{section_key}_save_name",
            label_visibility="collapsed",
        )
        if st.button("💾 Save Current Config", width="stretch", key=f"{section_key}_save_btn"):
            if not config_name.strip():
                st.error("Please enter a config name.")
            else:
                users = normalize_user_rows(user_rows)
                events = normalize_event_rows(event_rows)
                try:
                    p = save_config_to_yaml(
                        name=config_name.strip(),
                        initial_reserve_x=initial_reserve_x,
                        initial_reserve_y=initial_reserve_y,
                        fee_rate=fee_rate,
                        initial_lp_owner=initial_lp_owner,
                        users=users,
                        events=events,
                    )
                    st.success(f"Saved → {p}")
                except Exception as exc:
                    st.error(f"Save failed: {exc}")

    # ── 加载 / 删除 ──
    with load_col:
        if saved_names:
            sel_name = st.selectbox(
                "Load saved config",
                options=["(select to load)"] + saved_names,
                key=f"{section_key}_load_sel",
                label_visibility="collapsed",
            )
            btn_cols = st.columns([1, 1])
            if btn_cols[0].button("📂 Load", width="stretch", key=f"{section_key}_load_btn"):
                if sel_name and sel_name != "(select to load)":
                    data = load_saved_config(sel_name)
                    if data:
                        st.session_state[f"{section_key}_loaded_config"] = data
                        st.session_state[f"{section_key}_loaded_name"] = sel_name
                        st.session_state[f"{section_key}_editor_version"] = (
                            st.session_state.get(f"{section_key}_editor_version", 0) + 1
                        )
                        st.session_state["active_view"] = "Custom Simulation"
                        st.session_state.pop(f"{section_key}_artifacts", None)
                        st.rerun()
            if btn_cols[1].button("🗑 Delete", width="stretch", key=f"{section_key}_del_btn"):
                if sel_name and sel_name != "(select to load)":
                    delete_saved_config(sel_name)
                    st.rerun()
        else:
            st.caption("No saved configs yet — run & save one above.")


# ── 页面标签 ──────────────────────────────────────────────────────────


def _run_default_config() -> None:
    """默认配置运行页签。"""
    st.subheader("Default Config Simulation")

    if st.button("▶ Run Default Config", width="stretch", type="primary"):
        config = load_config(DEFAULT_CONFIG_PATH)
        runner = SimulationRunner(ROOT_DIR)
        st.session_state["default_artifacts"] = runner.run_from_config(config)

    artifacts = st.session_state.get("default_artifacts")
    if artifacts is not None:
        _show_result(artifacts, section_key="default")


def _run_custom_simulation() -> None:
    """自定义参数运行页签：支持编辑参数、保存/加载配置、运行仿真。"""
    st.subheader("Custom Simulation")

    # ── 池参数 ──
    default_config = load_config(DEFAULT_CONFIG_PATH)
    loaded = st.session_state.pop("custom_loaded_config", None)
    if loaded:
        # Streamlit widget state must be updated before the widgets are created,
        # otherwise loaded configs would only refresh the event/user tables.
        st.session_state["custom_reserve_x"] = float(
            loaded.get("initial_reserve_x", default_config.initial_reserve_x)
        )
        st.session_state["custom_reserve_y"] = float(
            loaded.get("initial_reserve_y", default_config.initial_reserve_y)
        )
        st.session_state["custom_fee_rate"] = float(loaded.get("fee_rate", default_config.fee_rate))
        st.session_state["custom_initial_lp_owner"] = str(loaded.get("initial_lp_owner", "protocol") or "protocol")

    left, right = st.columns([1, 1.2])
    with left:
        initial_reserve_x = st.number_input(
            "Initial Token X Reserve",
            min_value=0.0,
            value=float(default_config.initial_reserve_x),
            step=10.0,
            key="custom_reserve_x",
        )
        initial_reserve_y = st.number_input(
            "Initial Token Y Reserve",
            min_value=0.0,
            value=float(default_config.initial_reserve_y),
            step=10.0,
            key="custom_reserve_y",
        )
        fee_rate = st.number_input(
            "Fee Rate",
            min_value=0.0,
            max_value=1.0,
            value=float(default_config.fee_rate),
            step=0.001,
            format="%.6f",
            key="custom_fee_rate",
        )
        initial_lp_owner = st.text_input(
            "Initial LP Owner",
            value=str(default_config.initial_lp_owner or "protocol"),
            key="custom_initial_lp_owner",
            help="Receives any initial LP shares not explicitly assigned to users.",
        )

    # ── 用户编辑表格 ──
    # 如果从保存配置加载了数据，则以此初始化表格
    if loaded:
        user_rows_default = [
            {
                "user_id": uid,
                "balance_x": float(d.get("balance_x", 0)),
                "balance_y": float(d.get("balance_y", 0)),
                "lp_shares": float(d.get("lp_shares", 0)),
            }
            for uid, d in (loaded.get("users") or {}).items()
        ] or build_default_user_rows(default_config.users)
    else:
        user_rows_default = build_default_user_rows(default_config.users)
    editor_version = st.session_state.get("custom_editor_version", 0)

    with right:
        st.caption("👥 Users  (add rows via bottom blank row)")
        user_rows = st.data_editor(
            user_rows_default,
            num_rows="dynamic",
            use_container_width=True,
            key=f"custom_user_editor_{editor_version}",
        )

    # ── 事件编辑表格 ──
    if loaded:
        event_rows_default = build_default_event_rows(loaded.get("events") or [])
    else:
        event_rows_default = build_default_event_rows(default_config.events)

    st.caption("📋 Events  (sorted by timestamp on run)")
    event_rows = st.data_editor(
        event_rows_default,
        num_rows="dynamic",
        use_container_width=True,
        key=f"custom_event_editor_{editor_version}",
        column_config={
            "event_type": st.column_config.SelectboxColumn(
                "event_type",
                options=["swap", "add_liquidity", "remove_liquidity"],
                width="medium",
            ),
            "direction": st.column_config.SelectboxColumn(
                "direction",
                options=["x_to_y", "y_to_x"],
                width="small",
            ),
        },
    )

    # ── 保存 / 加载配置 ──
    with st.expander("💾 Save / Load Config", expanded=False):
        _render_save_load_ui(
            section_key="custom",
            initial_reserve_x=initial_reserve_x,
            initial_reserve_y=initial_reserve_y,
            fee_rate=fee_rate,
            initial_lp_owner=initial_lp_owner,
            user_rows=user_rows,
            event_rows=event_rows,
        )

    # ── 运行按钮 ──
    if st.button("▶ Run Custom Simulation", type="primary", width="stretch"):
        users = normalize_user_rows(user_rows)
        events = normalize_event_rows(event_rows)
        validation = validate_runtime_input(
            initial_reserve_x=initial_reserve_x,
            initial_reserve_y=initial_reserve_y,
            fee_rate=fee_rate,
            initial_lp_owner=initial_lp_owner,
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
            initial_lp_owner=initial_lp_owner,
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

    # 如果加载了配置，显示名称提示
    loaded_name = st.session_state.pop("custom_loaded_name", None)
    if loaded_name:
        st.success(f"Loaded config: {loaded_name}")

    # ── 结果展示 ──
    artifacts = st.session_state.get("custom_artifacts")
    if artifacts is not None:
        _show_result(artifacts, section_key="custom")


# ── 入口 ──────────────────────────────────────────────────────────────


def main() -> None:
    """Streamlit 应用入口。"""
    st.set_page_config(
        page_title="AMM Exchange Simulator",
        page_icon="📈",
        layout="wide",
    )
    st.title("📈 AMM Exchange Simulator")

    removed = cleanup_old_web_runs(keep=5)
    if removed:
        st.sidebar.caption(f"Cleaned up {removed} old web run(s); only the latest 5 are kept.")

    selected_view = st.radio(
        "Simulation mode",
        ["Default Config", "Custom Simulation"],
        horizontal=True,
        label_visibility="collapsed",
        key="active_view",
    )

    if selected_view == "Default Config":
        _run_default_config()
    else:
        _run_custom_simulation()


if __name__ == "__main__":
    main()

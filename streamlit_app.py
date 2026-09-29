"""System Capacity & Care Load Analytics for Unaccompanied Children (UAC Program)
Unified Mentor Internship Project Dashboard.
Run locally with: streamlit run streamlit_app.py
"""

from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data import read_source, fingerprint
from src.features import derive
from src.analysis import summarize
from src.models import run_experiment

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="System Capacity & Care Load Analytics | UAC Program",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished healthcare dashboard aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .kpi-container {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #3b82f6;
    }
    .stMetric label {
        font-weight: 600;
        color: #1f2937;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Data Ingestion & Caching
# ---------------------------------------------------------
@st.cache_data(show_spinner="Loading and validating source dataset...")
def load_data():
    raw, audit = read_source()
    derived = derive(raw)
    summary_bundle = summarize(raw)
    experiment = run_experiment(raw)
    return raw, derived, audit, summary_bundle, experiment

raw_data, derived_data, audit, summary_bundle, experiment = load_data()


# ---------------------------------------------------------
# Sidebar & User Capabilities
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/US-DeptOfHHS-Seal.svg/240px-US-DeptOfHHS-Seal.svg.png", width=90)
st.sidebar.title("Filter & Granularity Controls")

st.sidebar.markdown("### 📅 Date Range Selector")
min_date = derived_data["date"].min().date()
max_date = derived_data["date"].max().date()

selected_dates = st.sidebar.date_input(
    "Select Reporting Period",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

# Filter DataFrame by selected date range
mask = (derived_data["date"].dt.date >= start_date) & (derived_data["date"].dt.date <= end_date)
df = derived_data.loc[mask].copy().reset_index(drop=True)

st.sidebar.markdown("### ⏱️ Time Granularity Filter")
granularity = st.sidebar.radio(
    "Aggregation & Smoothing",
    ["Daily (Raw)", "7-Day Rolling Average", "14-Day Rolling Average", "Monthly Summary"],
    index=1,
)

st.sidebar.markdown("### 📊 Metric Toggles")
show_cbp = st.sidebar.checkbox("Include CBP Custody", value=True)
show_hhs = st.sidebar.checkbox("Include HHS Care", value=True)
show_net_flow = st.sidebar.checkbox("Include Net Flow Indicator", value=True)
show_growth = st.sidebar.checkbox("Show Day-over-Day Growth Rate", value=False)

st.sidebar.markdown("---")
st.sidebar.info(
    f"**Data Provenance Audit**\n"
    f"- Total Source Rows: {audit['source_rows']:,}\n"
    f"- Blank Records Removed: {audit['blank_rows_removed']}\n"
    f"- Active Valid Dates: {len(df):,} of {len(derived_data):,}\n"
    f"- Fingerprint: `{audit['dataset_fingerprint'][:12]}...`"
)


# ---------------------------------------------------------
# Dashboard Header
# ---------------------------------------------------------
st.markdown('<div class="main-header">🏥 System Capacity & Care Load Analytics</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    '<strong>U.S. Department of Health and Human Services (HHS) & CBP Unaccompanied Children (UAC) Program</strong> — '
    'A central analytical and predictive capacity framework monitoring intake, custody load, transfer dynamics, and sponsor discharges.'
    '</div>',
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No records found in the selected date range. Please widen your date selection.")
    st.stop()


# ---------------------------------------------------------
# Key Performance Indicators (KPI Summary Cards)
# ---------------------------------------------------------
latest_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else latest_row

col1, col2, col3, col4, col5 = st.columns(5)

# 1. Total Children Under Care
total_load_val = int(latest_row["total_load"])
total_load_delta = int(latest_row["total_load"] - prev_row["total_load"])
col1.metric(
    label="Total Children in System",
    value=f"{total_load_val:,}",
    delta=f"{total_load_delta:+,} d/d",
    help="Combined active load across CBP Custody and HHS Care facilities.",
)

# 2. Net Intake Pressure
net_flow_val = int(latest_row["net_flow"])
net_flow_delta = int(latest_row["net_flow"] - prev_row["net_flow"])
col2.metric(
    label="Net Daily Intake",
    value=f"{net_flow_val:+,}",
    delta=f"{net_flow_delta:+,} d/d",
    help="Children Transferred into HHS minus Children Discharged to Sponsors. Positive = backlog accumulating.",
)

# 3. Care Load Volatility Index
volatility_val = latest_row["volatility14"]
vol_str = f"{volatility_val:.2f}%" if pd.notna(volatility_val) else "N/A"
col3.metric(
    label="Care Volatility Index",
    value=vol_str,
    help="14-day rolling standard deviation of load change relative to mean census. Measures system stability.",
)

# 4. Backlog Accumulation Rate
pos_flow_share = (df["net_flow"] > 0).mean() * 100
col4.metric(
    label="Backlog Pressure Share",
    value=f"{pos_flow_share:.1f}%",
    help="Percentage of reported days where inflow (transfers) exceeded outflow (discharges).",
)

# 5. Discharge Offset Ratio
discharges_sum = df["discharges"].sum()
transfers_sum = df["transfers"].sum()
offset_ratio = (discharges_sum / transfers_sum) if transfers_sum > 0 else 0
col5.metric(
    label="Discharge Offset Ratio",
    value=f"{offset_ratio:.2f}",
    help="Total discharges divided by total transfers. Ratio < 1.0 indicates capacity bottleneck.",
)

st.markdown("---")


# ---------------------------------------------------------
# Tabs for Modular Organization
# ---------------------------------------------------------
tab_overview, tab_comparison, tab_flows, tab_forecasting, tab_audit = st.tabs([
    "📈 System Load Overview",
    "⚖️ CBP vs HHS Load Comparison",
    "🔄 Net Intake & Backlog Trends",
    "🔮 7-Day Forecasting Laboratory",
    "📋 Data Quality & Audit Explorer",
])


# =========================================================
# Tab 1: System Load Overview Pane
# =========================================================
with tab_overview:
    st.subheader("System-Wide Care Load Over Time")
    st.caption("Active census tracking total children requiring federal custody, care, and sponsor reunification.")

    fig_overview = go.Figure()

    if granularity == "Daily (Raw)":
        fig_overview.add_trace(go.Scatter(
            x=df["date"], y=df["total_load"],
            mode="lines", name="Total System Load (Daily)",
            line=dict(color="#1e3a8a", width=1.8),
        ))
    elif granularity == "7-Day Rolling Average":
        fig_overview.add_trace(go.Scatter(
            x=df["date"], y=df["total_load"],
            mode="lines", name="Total System Load (Observed)",
            line=dict(color="#93c5fd", width=1), opacity=0.6,
        ))
        fig_overview.add_trace(go.Scatter(
            x=df["date"], y=df["load_mean7"],
            mode="lines", name="7-Observation Rolling Mean",
            line=dict(color="#1e3a8a", width=2.4),
        ))
    elif granularity == "14-Day Rolling Average":
        fig_overview.add_trace(go.Scatter(
            x=df["date"], y=df["total_load"],
            mode="lines", name="Total System Load (Observed)",
            line=dict(color="#93c5fd", width=1), opacity=0.6,
        ))
        fig_overview.add_trace(go.Scatter(
            x=df["date"], y=df["load_mean14"],
            mode="lines", name="14-Observation Rolling Mean",
            line=dict(color="#2563eb", width=2.4),
        ))
    else:  # Monthly
        monthly_df = df.set_index("date").resample("ME")["total_load"].mean().reset_index()
        fig_overview.add_trace(go.Bar(
            x=monthly_df["date"], y=monthly_df["total_load"],
            name="Monthly Mean Total Load",
            marker_color="#3b82f6",
        ))

    # Peak annotation
    peak_row = df.loc[df["total_load"].idxmax()]
    fig_overview.add_annotation(
        x=peak_row["date"], y=peak_row["total_load"],
        text=f"Peak: {int(peak_row['total_load']):,} ({peak_row['date'].strftime('%b %d, %Y')})",
        showarrow=True, arrowhead=2, arrowcolor="#ef4444",
        bordercolor="#ef4444", borderwidth=1, borderpad=4, bgcolor="#fee2e2",
    )

    fig_overview.update_layout(
        height=450, margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Reporting Date", yaxis_title="Number of Children",
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_overview, use_container_width=True)

    # Secondary Growth Rate plot if toggled
    if show_growth:
        st.markdown("#### Day-over-Day Care Load Growth Rate (%)")
        fig_growth = px.bar(
            df, x="date", y="growth_pct",
            color="growth_pct",
            color_continuous_scale="RdBu_r",
            labels={"growth_pct": "Growth Rate (%)", "date": "Reporting Date"},
            title="Percentage Day-over-Day Fluctuation in Total Care Load",
        )
        fig_growth.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_growth, use_container_width=True)


# =========================================================
# Tab 2: CBP vs HHS Load Comparison
# =========================================================
with tab_comparison:
    st.subheader("CBP Custody vs. HHS Care Distribution")
    st.caption("CBP maintains initial temporary custody; HHS provides licensed shelter, screening, and long-term placement.")

    col_comp_1, col_comp_2 = st.columns([2, 1])

    with col_comp_1:
        fig_split = go.Figure()
        if show_hhs:
            fig_split.add_trace(go.Scatter(
                x=df["date"], y=df["hhs_care"],
                mode="lines", name="HHS Care (Shelters/Facilities)",
                stackgroup="one", fillcolor="rgba(37, 99, 235, 0.45)", line=dict(color="#1d4ed8", width=1.5),
            ))
        if show_cbp:
            fig_split.add_trace(go.Scatter(
                x=df["date"], y=df["cbp_custody"],
                mode="lines", name="CBP Custody (Intake Stations)",
                stackgroup="one", fillcolor="rgba(249, 115, 22, 0.45)", line=dict(color="#ea580c", width=1.5),
            ))

        fig_split.update_layout(
            title="Care Load Allocation (Stacked Area View)",
            height=430, margin=dict(l=20, r=20, t=35, b=20),
            xaxis_title="Date", yaxis_title="Children Count",
            hovermode="x unified", legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig_split, use_container_width=True)

    with col_comp_2:
        st.markdown("#### Operational Share Snapshot")
        avg_cbp = df["cbp_custody"].mean()
        avg_hhs = df["hhs_care"].mean()
        fig_pie = px.pie(
            names=["HHS Facilities", "CBP Intake Custody"],
            values=[avg_hhs, avg_cbp],
            color=["HHS Facilities", "CBP Intake Custody"],
            color_discrete_map={"HHS Facilities": "#2563eb", "CBP Intake Custody": "#f97316"},
            hole=0.45,
        )
        fig_pie.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

        st.info(
            f"**Average Balance**:\n"
            f"- **HHS Care Share**: {avg_hhs / (avg_cbp + avg_hhs) * 100:.1f}%\n"
            f"- **CBP Custody Share**: {avg_cbp / (avg_cbp + avg_hhs) * 100:.1f}%"
        )

    # Anomaly Review Flags (Logical Constraints from Brief)
    st.markdown("#### ⚠️ Logical Constraint & Operational Review Logs")
    st.caption("Verification of pipeline rules: Transfers ≤ CBP Custody and Discharges ≤ HHS Care.")

    anom_cbp = df[df["transfer_review"]][["date", "cbp_custody", "transfers"]]
    anom_hhs = df[df["discharge_review"]][["date", "hhs_care", "discharges"]]

    col_flag1, col_flag2 = st.columns(2)
    with col_flag1:
        st.write(f"**Transfers > CBP Custody Dates ({len(anom_cbp)} occurrences)**")
        if not anom_cbp.empty:
            st.dataframe(anom_cbp.head(5), use_container_width=True)
            st.caption("Note: Intra-day turnover allows daily transfer flows to exceed snapshot custody.")
        else:
            st.success("No constraint exceptions found in selected range.")

    with col_flag2:
        st.write(f"**Discharges > HHS Care Dates ({len(anom_hhs)} occurrences)**")
        if not anom_hhs.empty:
            st.dataframe(anom_hhs.head(5), use_container_width=True)
        else:
            st.success("Strict adherence: Discharges never exceeded active care.")


# =========================================================
# Tab 3: Net Intake & Backlog Trends
# =========================================================
with tab_flows:
    st.subheader("Inflow vs Outflow Dynamics & Backlog Accumulation")
    st.caption("Transfers into HHS (inflow) versus Sponsor Discharges (outflow). A sustained positive net flow builds system pressure.")

    fig_flows = go.Figure()
    fig_flows.add_trace(go.Bar(
        x=df["date"], y=df["transfers"],
        name="Transfers into HHS (Inflow)",
        marker_color="#f59e0b", opacity=0.7,
    ))
    fig_flows.add_trace(go.Bar(
        x=df["date"], y=df["discharges"],
        name="Sponsor Discharges (Outflow)",
        marker_color="#10b981", opacity=0.7,
    ))
    fig_flows.add_trace(go.Scatter(
        x=df["date"], y=df["net_mean7"],
        mode="lines", name="7-Obs Net Intake (Mean Inflow - Outflow)",
        line=dict(color="#1e293b", width=2.2),
    ))

    fig_flows.add_hline(y=0, line_dash="dash", line_color="#ef4444", annotation_text="Break-even Net Flow (0)")

    fig_flows.update_layout(
        barmode="group",
        height=430, margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Date", yaxis_title="Daily Flow Count",
        hovermode="x unified", legend=dict(orientation="h", y=1.05),
    )
    st.plotly_chart(fig_flows, use_container_width=True)

    # Pressure indicator callout
    pressure_days = df[df["pressure_4of7"]]
    st.markdown(
        f"**Prolonged Strain Windows**: **{len(pressure_days)}** days met the "
        f"*4-of-7 days positive net intake* pressure rule within the selected timeframe."
    )


# =========================================================
# Tab 4: 7-Day Forecasting Laboratory
# =========================================================
with tab_forecasting:
    st.subheader("🔮 Exact Seven-Day Predictive Forecasting Laboratory")
    st.caption(
        "Chronological time-series evaluation comparing baseline persistence against predictive regressors. "
        "Evaluated on held-out test data with zero future data leakage."
    )

    if experiment.get("available"):
        score_df = pd.json_normalize(experiment["scores"])
        score_df = score_df.rename(columns={
            "model": "Candidate Model",
            "validation.mae": "Val MAE",
            "validation.rmse": "Val RMSE",
            "test.mae": "Test MAE",
            "test.rmse": "Test RMSE",
            "test.bias": "Test Bias",
        })

        col_fc_left, col_fc_right = st.columns([3, 2])

        with col_fc_left:
            st.markdown("#### Test Period Predictions vs. Actual Census")
            test_preds = pd.DataFrame(experiment["test_predictions"])
            test_preds["date"] = pd.to_datetime(test_preds["date"])

            fig_test = go.Figure()
            fig_test.add_trace(go.Scatter(
                x=test_preds["date"], y=test_preds["actual"],
                mode="lines", name="Actual HHS Census",
                line=dict(color="#1e3a8a", width=2.4),
            ))
            fig_test.add_trace(go.Scatter(
                x=test_preds["date"], y=test_preds["selected"],
                mode="lines", name=f"Selected Winner ({experiment['selected_model']})",
                line=dict(color="#f97316", width=2, dash="dot"),
            ))
            fig_test.add_trace(go.Scatter(
                x=test_preds["date"], y=test_preds["persistence"],
                mode="lines", name="Persistence Baseline",
                line=dict(color="#9ca3af", width=1.5, dash="dash"),
            ))
            fig_test.update_layout(
                height=380, margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Target Evaluation Date", yaxis_title="Children Census",
                hovermode="x unified", legend=dict(orientation="h", y=1.05),
            )
            st.plotly_chart(fig_test, use_container_width=True)

        with col_fc_right:
            st.markdown("#### Candidate Model Benchmark")
            st.dataframe(score_df, use_container_width=True, hide_index=True)

            improvement = experiment.get("test_skill_vs_persistence_pct", 0)
            winner = experiment.get("selected_model", "N/A")
            st.success(
                f"🏆 **Selected Model**: **{winner}**\n\n"
                f"- **Validation MAE**: {score_df.loc[score_df['Candidate Model']==winner, 'Val MAE'].values[0]} children\n"
                f"- **Test MAE**: {score_df.loc[score_df['Candidate Model']==winner, 'Test MAE'].values[0]} children\n"
                f"- **Skill Gain**: **{improvement:.2f}% lower error** than naive persistence baseline."
            )

        # Forward projection card
        fc = experiment["forecast"]
        st.markdown("#### 🔭 7-Day Ahead Operational Census Forecast")
        st.info(
            f"**Projection Origin**: {fc['origin']} ➔ **Target Date**: {fc['date']}\n\n"
            f"- **Point Estimate**: **{fc['estimate']:,} children**\n"
            f"- **90% Descriptive Reference Band**: **{fc['error_reference_low']:,} – {fc['error_reference_high']:,} children** (±{fc['error_radius']} margin)"
        )
    else:
        st.warning(f"Forecasting unavailable: {experiment.get('reason')}")


# =========================================================
# Tab 5: Data Quality & Audit Explorer
# =========================================================
with tab_audit:
    st.subheader("Data Quality, Integrity & Provenance Explorer")
    st.caption("Federal data governance: SHA-256 validation, column schema audit, and raw record inspection.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Valid Calendar Records", f"{audit['valid_rows']:,}")
    c2.metric("Blank Records Purged", f"{audit['blank_rows_removed']:,}")
    c3.metric("Observed Calendar Coverage", f"{audit['valid_rows'] / 1074 * 100:.1f}%")

    st.markdown("#### Raw Observation Explorer")
    display_cols = ["date", "cbp_intake", "cbp_custody", "transfers", "hhs_care", "discharges", "total_load", "net_flow"]
    st.dataframe(df[display_cols].sort_values("date", ascending=False), use_container_width=True)

    # Download button for stakeholders
    csv_bytes = df[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_bytes,
        file_name=f"UAC_Filtered_Data_{start_date}_to_{end_date}.csv",
        mime="text/csv",
    )

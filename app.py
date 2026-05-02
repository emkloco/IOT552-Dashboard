import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Global Workload Rerouter Dashboard",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
.main {
    background-color: #F8FAFC;
}

.block-container {
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}

.dashboard-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 0.2rem;
}

.dashboard-subtitle {
    font-size: 1rem;
    color: #475569;
    margin-bottom: 1.5rem;
}

.kpi-card {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    padding: 1.2rem;
    border-radius: 18px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
    color: white;
    min-height: 115px;
}

.kpi-label {
    font-size: 0.82rem;
    color: #CBD5E1;
    margin-bottom: 0.45rem;
}

.kpi-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: white;
}

.kpi-note {
    font-size: 0.75rem;
    color: #94A3B8;
    margin-top: 0.35rem;
}

.section-card {
    background-color: white;
    padding: 1rem;
    border-radius: 18px;
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    margin-bottom: 1rem;
}

.section-heading {
    font-size: 1.25rem;
    font-weight: 750;
    color: #0F172A;
    margin-bottom: 0.5rem;
}

.insight-box {
    background-color: #EFF6FF;
    border-left: 5px solid #2563EB;
    padding: 0.9rem;
    border-radius: 10px;
    color: #1E3A8A;
    margin-bottom: 1rem;
}

.warning-box {
    background-color: #FFF7ED;
    border-left: 5px solid #F97316;
    padding: 0.9rem;
    border-radius: 10px;
    color: #7C2D12;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    routing_df = pd.read_csv("dashboard_routing_fact.csv")
    energy_df = pd.read_csv("energy_rate.csv")

    # Clean column names
    routing_df.columns = (
        routing_df.columns
        .str.strip()
        .str.lower()
        .str.replace("\\", "", regex=False)
        .str.replace(" ", "_", regex=False)
        .str.replace("\ufeff", "", regex=False)
    )

    energy_df.columns = (
        energy_df.columns
        .str.strip()
        .str.lower()
        .str.replace("\\", "", regex=False)
        .str.replace(" ", "_", regex=False)
        .str.replace("\ufeff", "", regex=False)
    )

    # Date conversions
    for col in ["routedat", "submittedat", "deadlineat", "ratetimestamp"]:
        if col in routing_df.columns:
            routing_df[col] = pd.to_datetime(routing_df[col], errors="coerce")

    if "ratetimestamp" in energy_df.columns:
        energy_df["ratetimestamp"] = pd.to_datetime(energy_df["ratetimestamp"], errors="coerce")

    # Numeric conversions
    routing_numeric_cols = [
        "logid_pk",
        "estimatedcost_usd",
        "estimatedlatency_ms",
        "queuetime_minutes",
        "jobid_pk",
        "computehoursrequired",
        "estimatedruntime_minutes",
        "clientid_pk",
        "clusterid_pk",
        "powercapacity_kw",
        "availablegpucount",
        "regionid_pk",
        "rateid_pk",
        "costper_kwh_usd"
    ]

    for col in routing_numeric_cols:
        if col in routing_df.columns:
            routing_df[col] = pd.to_numeric(routing_df[col], errors="coerce")

    for col in ["rateid_pk", "regionid_fk", "costper_kwh_usd"]:
        if col in energy_df.columns:
            energy_df[col] = pd.to_numeric(energy_df[col], errors="coerce")

    # Crisis labels
    def crisis_label(value):
        value = str(value).strip().lower()
        if value in ["t", "true", "1", "yes"]:
            return "Crisis"
        if value in ["f", "false", "0", "no"]:
            return "Stable"
        return "Unknown"

    routing_df["crisis_status"] = routing_df["crisisflag"].apply(crisis_label)
    energy_df["crisis_status"] = energy_df["crisisflag"].apply(crisis_label)

    return routing_df, energy_df

routing_df, energy_df = load_data()

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="dashboard-title">Global Workload Rerouter Dashboard</div>
<div class="dashboard-subtitle">
Synthetic AI infrastructure dashboard showing energy-cost exposure, workload-routing decisions and service-impact metrics.
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.title("Dashboard Filters")
st.sidebar.caption("Use these controls to analyse routing cost, service impact and crisis exposure.")

selected_regions = st.sidebar.multiselect(
    "Region",
    options=sorted(routing_df["cityname"].dropna().unique()),
    default=sorted(routing_df["cityname"].dropna().unique())
)

selected_sla = st.sidebar.multiselect(
    "SLA Tier",
    options=sorted(routing_df["sla_tier"].dropna().unique()),
    default=sorted(routing_df["sla_tier"].dropna().unique())
)

selected_priority = st.sidebar.multiselect(
    "Job Priority",
    options=sorted(routing_df["prioritylevel"].dropna().unique()),
    default=sorted(routing_df["prioritylevel"].dropna().unique())
)

selected_status = st.sidebar.multiselect(
    "Routing Status",
    options=sorted(routing_df["routingstatus"].dropna().unique()),
    default=sorted(routing_df["routingstatus"].dropna().unique())
)

selected_crisis = st.sidebar.multiselect(
    "Crisis Status",
    options=sorted(routing_df["crisis_status"].dropna().unique()),
    default=sorted(routing_df["crisis_status"].dropna().unique())
)

# ============================================================
# FILTER DATA
# ============================================================

filtered = routing_df[
    routing_df["cityname"].isin(selected_regions) &
    routing_df["sla_tier"].isin(selected_sla) &
    routing_df["prioritylevel"].isin(selected_priority) &
    routing_df["routingstatus"].isin(selected_status) &
    routing_df["crisis_status"].isin(selected_crisis)
].copy()

filtered_energy = energy_df[
    energy_df["cityname"].isin(selected_regions) &
    energy_df["crisis_status"].isin(selected_crisis)
].copy()

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ============================================================
# KPI CALCULATIONS
# ============================================================

total_cost = filtered["estimatedcost_usd"].sum()
total_jobs = filtered["logid_pk"].count()
reallocated_jobs = (filtered["routingstatus"] == "Reallocated").sum()
delayed_jobs = (filtered["routingstatus"] == "Delayed").sum()
crisis_jobs = (filtered["crisis_status"] == "Crisis").sum()
avg_latency = filtered["estimatedlatency_ms"].mean()
avg_queue = filtered["queuetime_minutes"].mean()
avg_energy_rate = filtered["costper_kwh_usd"].mean()

# ============================================================
# KPI CARDS
# ============================================================

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Estimated Routing Cost</div>
        <div class="kpi-value">${total_cost:,.2f}</div>
        <div class="kpi-note">Synthetic workload cost exposure</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Routed Jobs</div>
        <div class="kpi-value">{total_jobs}</div>
        <div class="kpi-note">Logged routing decisions</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Reallocated Jobs</div>
        <div class="kpi-value">{reallocated_jobs}</div>
        <div class="kpi-note">Workloads moved for cost/risk reasons</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Crisis-Affected Jobs</div>
        <div class="kpi-value">{crisis_jobs}</div>
        <div class="kpi-note">Jobs linked to crisis-rate records</div>
    </div>
    """, unsafe_allow_html=True)

kpi_cols_2 = st.columns(4)

with kpi_cols_2[0]:
    st.metric("Average Latency", f"{avg_latency:.1f} ms")

with kpi_cols_2[1]:
    st.metric("Average Queue Time", f"{avg_queue:.1f} min")

with kpi_cols_2[2]:
    st.metric("Average Energy Rate", f"${avg_energy_rate:.4f}/kWh")

with kpi_cols_2[3]:
    st.metric("Delayed Jobs", f"{delayed_jobs}")

st.markdown("---")

# ============================================================
# EXECUTIVE INSIGHT SUMMARY
# ============================================================

highest_region = (
    filtered.groupby("cityname")["estimatedcost_usd"]
    .sum()
    .sort_values(ascending=False)
    .index[0]
)

highest_region_cost = (
    filtered.groupby("cityname")["estimatedcost_usd"]
    .sum()
    .sort_values(ascending=False)
    .iloc[0]
)

st.markdown(f"""
<div class="insight-box">
<strong>Executive insight:</strong> The highest estimated routing cost is currently associated with 
<strong>{highest_region}</strong>, with an estimated cost of <strong>${highest_region_cost:,.2f}</strong> under the selected filters.
This helps leadership identify where cost exposure is concentrated.
</div>
""", unsafe_allow_html=True)

# ============================================================
# MAIN VISUALS
# ============================================================

left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.markdown('<div class="section-heading">Energy Price Over Time by Region</div>', unsafe_allow_html=True)

    fig_energy = px.line(
        filtered_energy,
        x="ratetimestamp",
        y="costper_kwh_usd",
        color="cityname",
        markers=True,
        title=None,
        labels={
            "ratetimestamp": "Timestamp",
            "costper_kwh_usd": "Cost per kWh (USD)",
            "cityname": "Region"
        },
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig_energy.update_layout(
        template="plotly_white",
        height=430,
        margin=dict(l=20, r=20, t=40, b=20),
        legend_title_text="Region"
    )

    st.plotly_chart(fig_energy, use_container_width=True)

with right_col:
    st.markdown('<div class="section-heading">Routing Decision Breakdown</div>', unsafe_allow_html=True)

    status_breakdown = (
        filtered.groupby("routingstatus", as_index=False)["logid_pk"]
        .count()
        .rename(columns={"logid_pk": "jobs"})
    )

    fig_status = px.pie(
        status_breakdown,
        names="routingstatus",
        values="jobs",
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_status.update_layout(
        template="plotly_white",
        height=430,
        margin=dict(l=20, r=20, t=40, b=20),
        legend_title_text="Routing Status"
    )

    st.plotly_chart(fig_status, use_container_width=True)

# ============================================================
# SECOND ROW VISUALS
# ============================================================

left_col2, right_col2 = st.columns(2)

with left_col2:
    st.markdown('<div class="section-heading">Estimated Routing Cost by Region and Crisis Status</div>', unsafe_allow_html=True)

    region_cost = (
        filtered.groupby(["cityname", "crisis_status"], as_index=False)["estimatedcost_usd"]
        .sum()
    )

    fig_region_cost = px.bar(
        region_cost,
        x="cityname",
        y="estimatedcost_usd",
        color="crisis_status",
        barmode="group",
        labels={
            "cityname": "Region",
            "estimatedcost_usd": "Estimated Cost (USD)",
            "crisis_status": "Crisis Status"
        },
        color_discrete_map={
            "Crisis": "#EF4444",
            "Stable": "#10B981",
            "Unknown": "#64748B"
        }
    )

    fig_region_cost.update_layout(
        template="plotly_white",
        height=430,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig_region_cost, use_container_width=True)

with right_col2:
    st.markdown('<div class="section-heading">Workload Handling by Priority and Routing Status</div>', unsafe_allow_html=True)

    priority_status = (
        filtered.groupby(["prioritylevel", "routingstatus"], as_index=False)["logid_pk"]
        .count()
        .rename(columns={"logid_pk": "jobs"})
    )

    fig_priority = px.bar(
        priority_status,
        x="prioritylevel",
        y="jobs",
        color="routingstatus",
        barmode="stack",
        labels={
            "prioritylevel": "Priority Level",
            "jobs": "Number of Jobs",
            "routingstatus": "Routing Status"
        },
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig_priority.update_layout(
        template="plotly_white",
        height=430,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig_priority, use_container_width=True)

# ============================================================
# CLIENT SUMMARY TABLE
# ============================================================

st.markdown('<div class="section-heading">Client Cost and Service Impact Summary</div>', unsafe_allow_html=True)

client_summary = (
    filtered.groupby(["companyname", "sla_tier"], as_index=False)
    .agg(
        jobs=("jobid_pk", "count"),
        total_estimated_cost_usd=("estimatedcost_usd", "sum"),
        average_latency_ms=("estimatedlatency_ms", "mean"),
        average_queue_time_minutes=("queuetime_minutes", "mean"),
        total_compute_hours=("computehoursrequired", "sum")
    )
    .sort_values("total_estimated_cost_usd", ascending=False)
)

client_summary["total_estimated_cost_usd"] = client_summary["total_estimated_cost_usd"].round(2)
client_summary["average_latency_ms"] = client_summary["average_latency_ms"].round(1)
client_summary["average_queue_time_minutes"] = client_summary["average_queue_time_minutes"].round(1)

st.dataframe(
    client_summary,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# RAW DATA EXPANDER
# ============================================================

with st.expander("View filtered routing records"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

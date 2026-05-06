import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go



st.set_page_config(
    page_title="Global Workload Rerouter Dashboard",
    page_icon="⚡",
    layout="wide"
)



st.markdown("""
<style>
.block-container {
    padding-top: 2.3rem;
    padding-bottom: 2rem;
}

.dashboard-title {
    font-size: 2.55rem;
    font-weight: 850;
    color: #0F172A;
    margin-bottom: 0.1rem;
}

.dashboard-subtitle {
    font-size: 1rem;
    color: #475569;
    margin-bottom: 1.2rem;
}

.hero-box {
    background: linear-gradient(135deg, #0F172A, #1E3A8A);
    padding: 1.4rem;
    border-radius: 22px;
    color: white;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.18);
    margin-bottom: 1rem;
}

.hero-title {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.hero-text {
    font-size: 0.95rem;
    color: #DBEAFE;
}

.kpi-card {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    padding: 1.05rem;
    border-radius: 18px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
    color: white;
    min-height: 112px;
}

.kpi-card-blue {
    background: linear-gradient(135deg, #1D4ED8, #2563EB);
    padding: 1.05rem;
    border-radius: 18px;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
    color: white;
    min-height: 112px;
}

.kpi-card-green {
    background: linear-gradient(135deg, #047857, #10B981);
    padding: 1.05rem;
    border-radius: 18px;
    box-shadow: 0 8px 20px rgba(16, 185, 129, 0.25);
    color: white;
    min-height: 112px;
}

.kpi-card-orange {
    background: linear-gradient(135deg, #C2410C, #F97316);
    padding: 1.05rem;
    border-radius: 18px;
    box-shadow: 0 8px 20px rgba(249, 115, 22, 0.25);
    color: white;
    min-height: 112px;
}

.kpi-label {
    font-size: 0.78rem;
    color: #E5E7EB;
    margin-bottom: 0.45rem;
}

.kpi-value {
    font-size: 1.52rem;
    font-weight: 850;
    color: white;
}

.kpi-note {
    font-size: 0.72rem;
    color: #CBD5E1;
    margin-top: 0.3rem;
}

.section-heading {
    font-size: 1.22rem;
    font-weight: 800;
    color: #0F172A;
    margin-top: 0.8rem;
    margin-bottom: 0.4rem;
}

.insight-box {
    background-color: #EFF6FF;
    border-left: 6px solid #2563EB;
    padding: 1rem;
    border-radius: 12px;
    color: #1E3A8A;
    margin-bottom: 1rem;
    font-size: 0.96rem;
}

.recommendation-box {
    background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
    border-left: 6px solid #10B981;
    padding: 1rem;
    border-radius: 12px;
    color: #064E3B;
    margin-bottom: 1rem;
    font-size: 0.96rem;
}

.warning-box {
    background-color: #FFF7ED;
    border-left: 6px solid #F97316;
    padding: 1rem;
    border-radius: 12px;
    color: #7C2D12;
    margin-bottom: 1rem;
    font-size: 0.96rem;
}

.small-caption {
    color: #64748B;
    font-size: 0.78rem;
    margin-top: -0.3rem;
    margin-bottom: 0.7rem;
}
</style>
""", unsafe_allow_html=True)



@st.cache_data
def load_data():
    routing_df = pd.read_csv("dashboard_routing.csv")
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

    # Add synthetic coordinates for dashboard map
    coordinates = {
        "London": {"lat": 51.5072, "lon": -0.1276},
        "Reykjavik": {"lat": 64.1466, "lon": -21.9426},
        "Dublin": {"lat": 53.3498, "lon": -6.2603},
        "Frankfurt": {"lat": 50.1109, "lon": 8.6821},
        "Virginia": {"lat": 37.4316, "lon": -78.6569}
    }

    routing_df["lat"] = routing_df["cityname"].map(lambda x: coordinates.get(x, {}).get("lat"))
    routing_df["lon"] = routing_df["cityname"].map(lambda x: coordinates.get(x, {}).get("lon"))
    energy_df["lat"] = energy_df["cityname"].map(lambda x: coordinates.get(x, {}).get("lat"))
    energy_df["lon"] = energy_df["cityname"].map(lambda x: coordinates.get(x, {}).get("lon"))

    return routing_df, energy_df


routing_df, energy_df = load_data()



st.markdown("""
<div class="dashboard-title">Global Workload Rerouter Dashboard</div>
<div class="dashboard-subtitle">
Synthetic AI infrastructure dashboard for energy-aware compute routing, cost avoidance and service-impact decision-making.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-box">
    <div class="hero-title">Decision objective</div>
    <div class="hero-text">
        Identify when AI workloads should be rerouted away from high-cost or crisis-affected regions while maintaining acceptable latency and queue-time performance.
    </div>
</div>
""", unsafe_allow_html=True)



st.sidebar.title("Dashboard Controls")
st.sidebar.caption("Filter the synthetic workload-routing dataset.")

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

latency_threshold = st.sidebar.slider(
    "Acceptable latency threshold ms",
    min_value=40,
    max_value=150,
    value=60,
    step=5
)



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



# Simulated baseline:
# Assumption: without routing optimisation, workloads are exposed to the highest energy rate
# available at the matching timestamp in the synthetic energy-rate dataset.
baseline_rates = (
    energy_df.groupby("ratetimestamp")["costper_kwh_usd"]
    .max()
    .reset_index()
    .rename(columns={"costper_kwh_usd": "baseline_costper_kwh_usd"})
)

filtered = filtered.merge(
    baseline_rates,
    on="ratetimestamp",
    how="left"
)

filtered["estimated_cost_without_rerouting"] = (
    filtered["computehoursrequired"] *
    filtered["powercapacity_kw"] *
    filtered["baseline_costper_kwh_usd"]
)

filtered["estimated_cost_saved"] = (
    filtered["estimated_cost_without_rerouting"] - filtered["estimatedcost_usd"]
)

filtered["estimated_cost_saved"] = filtered["estimated_cost_saved"].clip(lower=0)

total_actual_cost = filtered["estimatedcost_usd"].sum()
total_baseline_cost = filtered["estimated_cost_without_rerouting"].sum()
total_saved = filtered["estimated_cost_saved"].sum()

saving_pct = 0
if total_baseline_cost > 0:
    saving_pct = (total_saved / total_baseline_cost) * 100



region_summary = (
    filtered.groupby(["cityname", "country"], as_index=False)
    .agg(
        avg_energy_rate=("costper_kwh_usd", "mean"),
        avg_latency_ms=("estimatedlatency_ms", "mean"),
        avg_queue_time=("queuetime_minutes", "mean"),
        routed_jobs=("logid_pk", "count"),
        total_cost=("estimatedcost_usd", "sum"),
        lat=("lat", "first"),
        lon=("lon", "first")
    )
)

eligible_regions = region_summary[
    region_summary["avg_latency_ms"] <= latency_threshold
].copy()

if not eligible_regions.empty:
    recommended_row = eligible_regions.sort_values(
        ["avg_energy_rate", "avg_latency_ms"],
        ascending=[True, True]
    ).iloc[0]
else:
    recommended_row = region_summary.sort_values(
        ["avg_energy_rate", "avg_latency_ms"],
        ascending=[True, True]
    ).iloc[0]

recommended_region = recommended_row["cityname"]
recommended_country = recommended_row["country"]
recommended_rate = recommended_row["avg_energy_rate"]
recommended_latency = recommended_row["avg_latency_ms"]

# Crisis comparison for executive insight
crisis_rows = filtered[filtered["crisis_status"] == "Crisis"]
stable_rows = filtered[filtered["crisis_status"] == "Stable"]

highest_cost_region = (
    filtered.groupby("cityname")["estimatedcost_usd"]
    .sum()
    .sort_values(ascending=False)
    .index[0]
)

highest_cost_value = (
    filtered.groupby("cityname")["estimatedcost_usd"]
    .sum()
    .sort_values(ascending=False)
    .iloc[0]
)



kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.markdown(f"""
    <div class="kpi-card-blue">
        <div class="kpi-label">Estimated Cost Without Rerouting</div>
        <div class="kpi-value">${total_baseline_cost:,.2f}</div>
        <div class="kpi-note">Simulated baseline exposure</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown(f"""
    <div class="kpi-card-green">
        <div class="kpi-label">Estimated Cost Saved</div>
        <div class="kpi-value">${total_saved:,.2f}</div>
        <div class="kpi-note">{saving_pct:.1f}% reduction vs baseline</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Actual Estimated Routing Cost</div>
        <div class="kpi-value">${total_actual_cost:,.2f}</div>
        <div class="kpi-note">Observed routed workload cost</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown(f"""
    <div class="kpi-card-orange">
        <div class="kpi-label">Recommended Region</div>
        <div class="kpi-value">{recommended_region}</div>
        <div class="kpi-note">${recommended_rate:.4f}/kWh | {recommended_latency:.1f} ms avg latency</div>
    </div>
    """, unsafe_allow_html=True)

kpi_cols_2 = st.columns(4)

with kpi_cols_2[0]:
    st.metric("Total Routed Jobs", f"{filtered['logid_pk'].count()}")

with kpi_cols_2[1]:
    st.metric("Reallocated Jobs", f"{(filtered['routingstatus'] == 'Reallocated').sum()}")

with kpi_cols_2[2]:
    st.metric("Average Queue Time", f"{filtered['queuetime_minutes'].mean():.1f} min")

with kpi_cols_2[3]:
    st.metric("Crisis-Affected Jobs", f"{(filtered['crisis_status'] == 'Crisis').sum()}")

st.markdown("---")



st.markdown(f"""
<div class="insight-box">
<strong>Executive insight:</strong> Under the selected filters, the routing model estimates 
<strong>${total_saved:,.2f}</strong> of avoided cost compared with a simulated no-rerouting baseline, representing an estimated 
<strong>{saving_pct:.1f}%</strong> reduction in energy-cost exposure. The recommended region is 
<strong>{recommended_region}, {recommended_country}</strong>, based on the lowest average energy rate while remaining within the selected acceptable latency threshold.
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="recommendation-box">
<strong>Best region recommendation:</strong> Route eligible low-priority or flexible workloads towards 
<strong>{recommended_region}</strong> when latency tolerance allows. This region currently combines an average energy rate of 
<strong>${recommended_rate:.4f}/kWh</strong> with average latency of <strong>{recommended_latency:.1f} ms</strong> in the synthetic dataset.
</div>
""", unsafe_allow_html=True)



map_col, line_col = st.columns([1.05, 1.25])

with map_col:
    st.markdown('<div class="section-heading">Global Compute Region Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-caption">Synthetic data-centre regions coloured by average energy rate. Recommended region is highlighted in gold.</div>', unsafe_allow_html=True)

    map_data = region_summary.copy()
    map_data["is_recommended"] = map_data["cityname"].apply(
        lambda x: "Recommended" if x == recommended_region else "Other"
    )

    fig_map = px.scatter_geo(
        map_data,
        lat="lat",
        lon="lon",
        color="avg_energy_rate",
        size="routed_jobs",
        hover_name="cityname",
        hover_data={
            "country": True,
            "avg_energy_rate": ":.4f",
            "avg_latency_ms": ":.1f",
            "avg_queue_time": ":.1f",
            "routed_jobs": True,
            "lat": False,
            "lon": False
        },
        color_continuous_scale=["#10B981", "#FBBF24", "#EF4444"],
        projection="natural earth"
    )

    rec = map_data[map_data["cityname"] == recommended_region]
    if not rec.empty:
        fig_map.add_trace(go.Scattergeo(
            lat=rec["lat"],
            lon=rec["lon"],
            mode="markers+text",
            text=["★ Recommended"],
            textposition="top center",
            marker=dict(
                size=22,
                color="#FACC15",
                line=dict(width=2, color="#111827"),
                symbol="star"
            ),
            name="Recommended Region"
        ))

    fig_map.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=20, b=0),
        geo=dict(
            showland=True,
            landcolor="#F1F5F9",
            showocean=True,
            oceancolor="#DBEAFE",
            showcountries=True,
            countrycolor="#CBD5E1"
        ),
        coloraxis_colorbar=dict(title="Avg $/kWh")
    )

    st.plotly_chart(fig_map, use_container_width=True)

with line_col:
    st.markdown('<div class="section-heading">Energy Price Over Time by Region</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-caption">Tracks regional energy-rate volatility across the synthetic data-centre footprint.</div>', unsafe_allow_html=True)

    fig_energy = px.line(
        filtered_energy,
        x="ratetimestamp",
        y="costper_kwh_usd",
        color="cityname",
        markers=True,
        labels={
            "ratetimestamp": "Timestamp",
            "costper_kwh_usd": "Cost per kWh (USD)",
            "cityname": "Region"
        },
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig_energy.update_layout(
        template="plotly_white",
        height=500,
        margin=dict(l=20, r=20, t=20, b=20),
        legend_title_text="Region"
    )

    st.plotly_chart(fig_energy, use_container_width=True)



scatter_col, bar_col = st.columns(2)

with scatter_col:
    st.markdown('<div class="section-heading">Cost vs Latency Trade-off</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-caption">Shows whether lower-cost routing decisions create unacceptable latency trade-offs.</div>', unsafe_allow_html=True)

    scatter_data = (
        filtered.groupby(["cityname", "crisis_status"], as_index=False)
        .agg(
            avg_cost=("estimatedcost_usd", "mean"),
            avg_latency=("estimatedlatency_ms", "mean"),
            jobs=("logid_pk", "count"),
            avg_energy_rate=("costper_kwh_usd", "mean")
        )
    )

    fig_tradeoff = px.scatter(
        scatter_data,
        x="avg_cost",
        y="avg_latency",
        size="jobs",
        color="crisis_status",
        text="cityname",
        labels={
            "avg_cost": "Average Estimated Cost (USD)",
            "avg_latency": "Average Latency (ms)",
            "jobs": "Jobs",
            "crisis_status": "Crisis Status"
        },
        color_discrete_map={
            "Crisis": "#EF4444",
            "Stable": "#10B981",
            "Unknown": "#64748B"
        }
    )

    fig_tradeoff.add_hline(
        y=latency_threshold,
        line_dash="dash",
        line_color="#2563EB",
        annotation_text=f"Latency threshold: {latency_threshold} ms",
        annotation_position="top left"
    )

    fig_tradeoff.update_traces(textposition="top center")
    fig_tradeoff.update_layout(
        template="plotly_white",
        height=470,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig_tradeoff, use_container_width=True)

with bar_col:
    st.markdown('<div class="section-heading">Estimated Routing Cost by Region and Crisis Status</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-caption">Highlights regional cost exposure and whether it is linked to crisis-rate records.</div>', unsafe_allow_html=True)

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
        height=470,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig_region_cost, use_container_width=True)



workload_col, status_col = st.columns(2)

with workload_col:
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
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig_priority, use_container_width=True)

with status_col:
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
        margin=dict(l=20, r=20, t=20, b=20),
        legend_title_text="Routing Status"
    )

    st.plotly_chart(fig_status, use_container_width=True)



st.markdown('<div class="section-heading">Client Cost and Service Impact Summary</div>', unsafe_allow_html=True)

client_summary = (
    filtered.groupby(["companyname", "sla_tier"], as_index=False)
    .agg(
        jobs=("jobid_pk", "count"),
        total_actual_cost_usd=("estimatedcost_usd", "sum"),
        estimated_cost_saved_usd=("estimated_cost_saved", "sum"),
        average_latency_ms=("estimatedlatency_ms", "mean"),
        average_queue_time_minutes=("queuetime_minutes", "mean"),
        total_compute_hours=("computehoursrequired", "sum")
    )
    .sort_values("total_actual_cost_usd", ascending=False)
)

client_summary["total_actual_cost_usd"] = client_summary["total_actual_cost_usd"].round(2)
client_summary["estimated_cost_saved_usd"] = client_summary["estimated_cost_saved_usd"].round(2)
client_summary["average_latency_ms"] = client_summary["average_latency_ms"].round(1)
client_summary["average_queue_time_minutes"] = client_summary["average_queue_time_minutes"].round(1)

st.dataframe(
    client_summary,
    use_container_width=True,
    hide_index=True
)



with st.expander("View filtered routing records"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

st.caption(
    "Note: Cost avoided is calculated using a simulated no-rerouting baseline based on the highest synthetic energy rate available at each timestamp. "
    "This is for prototype decision-support demonstration only."
)

"""
SIF-Precursor Intelligence Dashboard (Streamlit).

Run:
    streamlit run dashboard/app.py

Shows:
- KPI summary (total reports, % SIF-potential, top LSR)
- SIF-precursor density ranking by site & activity (bar + table)
- Heatmap: Site x Life-Saving Rule (SIF-flagged count)
- Recurring precursor patterns (activity + barrier failure combos)
- Drill-down report explorer with raw text
"""
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

st.set_page_config(page_title="SIF Precursor Dashboard", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROCESSED_PATH = os.path.join(DATA_DIR, "processed_reports.csv")
RANK_PATH = os.path.join(DATA_DIR, "site_activity_rank.csv")


@st.cache_data
def load_data():
    if not os.path.exists(PROCESSED_PATH):
        st.error(
            "Processed data not found. Run `python data/generate_synthetic_data.py` "
            "then `python src/pipeline.py` first."
        )
        st.stop()
    df = pd.read_csv(PROCESSED_PATH)
    rank = pd.read_csv(RANK_PATH)
    return df, rank


df, rank = load_data()

st.title("🛡️ SIF-Precursor Intelligence Dashboard")
st.caption(
    "Auto-classifies UA/UC, near-miss & incident reports for Serious Injury/Fatality (SIF) "
    "potential, maps them to IOGP Life-Saving Rules, and ranks sites/activities by precursor density."
)

# ---- Sidebar filters ----
st.sidebar.header("Filters")
sites = st.sidebar.multiselect("Site", sorted(df["site"].unique()), default=sorted(df["site"].unique()))
rules = st.sidebar.multiselect("Life-Saving Rule", sorted(df["life_saving_rule"].unique()), default=sorted(df["life_saving_rule"].unique()))
report_types = st.sidebar.multiselect("Report Type", sorted(df["report_type"].unique()), default=sorted(df["report_type"].unique()))

f = df[
    df["site"].isin(sites) & df["life_saving_rule"].isin(rules) & df["report_type"].isin(report_types)
]

# ---- KPIs ----
total = len(f)
sif_count = int(f["sif_predicted"].sum())
sif_pct = round(sif_count / total * 100, 1) if total else 0
top_rule = f.loc[f["sif_predicted"] == 1, "life_saving_rule"].mode()
top_rule = top_rule.iloc[0] if not top_rule.empty else "N/A"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Reports", total)
c2.metric("SIF-Potential Flagged", sif_count, f"{sif_pct}% of total")
c3.metric("Top SIF Life-Saving Rule", top_rule)
c4.metric("Sites Covered", f["site"].nunique())

st.divider()

# ---- Site x Activity SIF density ranking ----
st.subheader("📊 SIF-Precursor Density Ranking — Site x Activity")
rank_f = rank[rank["site"].isin(sites)].head(15)
fig_rank = px.bar(
    rank_f, x="sif_density_pct", y=rank_f["site"] + " | " + rank_f["activity_category"],
    orientation="h", color="sif_density_pct", color_continuous_scale="Reds",
    labels={"y": "Site | Activity", "sif_density_pct": "SIF Density (%)"},
    title="Top 15 highest fatal-potential precursor combinations",
)
fig_rank.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
st.plotly_chart(fig_rank, use_container_width=True)
st.dataframe(rank_f, use_container_width=True, hide_index=True)

st.divider()

# ---- Heatmap: Site x Life-Saving Rule ----
st.subheader("🔥 Heatmap — Site x IOGP Life-Saving Rule (SIF-flagged reports)")
heat = (
    f[f["sif_predicted"] == 1]
    .groupby(["site", "life_saving_rule"])
    .size()
    .reset_index(name="count")
)
if not heat.empty:
    pivot = heat.pivot(index="site", columns="life_saving_rule", values="count").fillna(0)
    fig_heat = px.imshow(pivot, text_auto=True, color_continuous_scale="Reds", aspect="auto")
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No SIF-flagged reports match current filters.")

st.divider()

# ---- Recurring precursor patterns ----
st.subheader("🔁 Recurring Precursor Patterns (Activity + Barrier Failure)")
patterns = (
    f[f["sif_predicted"] == 1]
    .groupby(["activity_category", "barrier_failure"])
    .size()
    .reset_index(name="occurrences")
    .sort_values("occurrences", ascending=False)
    .head(10)
)
st.dataframe(patterns, use_container_width=True, hide_index=True)

st.divider()

# ---- Report explorer ----
st.subheader("🔍 Report Explorer")
show_sif_only = st.checkbox("Show SIF-potential flagged only", value=True)
explorer_df = f[f["sif_predicted"] == 1] if show_sif_only else f
st.dataframe(
    explorer_df[[
        "report_id", "date", "site", "report_type", "life_saving_rule",
        "activity_category", "barrier_failure", "sif_probability", "description",
    ]].sort_values("sif_probability", ascending=False),
    use_container_width=True, hide_index=True, height=400,
)

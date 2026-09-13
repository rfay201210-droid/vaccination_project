"""
Vaccination Data Analysis & Visualization
Streamlit Dashboard – Deployable to Streamlit Community Cloud / GitHub
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sqlite3

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Global Vaccination Insights",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Paths & data loading (cached)
# -----------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
CLEAN = BASE / "data" / "cleaned"
DB_PATH = BASE / "sql" / "vaccination.db"


@st.cache_data(ttl=3600)
def load_csvs():
    required = [
        "coverage_cleaned.csv",
        "incidence_cleaned.csv",
        "cases_cleaned.csv",
        "introduction_cleaned.csv",
        "schedule_cleaned.csv",
    ]
    missing = [f for f in required if not (CLEAN / f).exists()]
    if missing:
        st.error(
            f"Missing cleaned data files: {missing}. "
            "Run `python python/01_data_cleaning.py` locally or ensure data/cleaned/ is in the repo."
        )
        st.stop()
    coverage = pd.read_csv(CLEAN / "coverage_cleaned.csv")
    incidence = pd.read_csv(CLEAN / "incidence_cleaned.csv")
    cases = pd.read_csv(CLEAN / "cases_cleaned.csv")
    introduction = pd.read_csv(CLEAN / "introduction_cleaned.csv")
    schedule = pd.read_csv(CLEAN / "schedule_cleaned.csv")
    return coverage, incidence, cases, introduction, schedule


@st.cache_resource
def get_db_connection():
    if DB_PATH.exists():
        return sqlite3.connect(str(DB_PATH), check_same_thread=False)
    return None


coverage, incidence, cases, introduction, schedule = load_csvs()

# Attach WHO region
region_map = introduction[["ISO_3_Code", "WHO_Region"]].drop_duplicates()
region_map.columns = ["Code", "WHO_Region"]
coverage = coverage.merge(region_map, on="Code", how="left")
incidence = incidence.merge(region_map, on="Code", how="left")
cases = cases.merge(region_map, on="Code", how="left")

# -----------------------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------------------
st.sidebar.title("💉 Filters")
st.sidebar.markdown("---")

years = sorted(coverage["Year"].unique())
year_range = st.sidebar.slider(
    "Year range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years))),
)

regions = ["All"] + sorted(coverage["WHO_Region"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("WHO Region", regions)

antigens = sorted(coverage["Antigen"].unique().tolist())
selected_antigens = st.sidebar.multiselect(
    "Antigens",
    antigens,
    default=["DTPCV3", "MCV1", "POL3", "HEPB3"],
)

diseases = sorted(incidence["Disease"].unique().tolist())
selected_diseases = st.sidebar.multiselect(
    "Diseases",
    diseases,
    default=["MEASLES", "PERTUSSIS", "POLIO"],
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Data: WHO-style sample covering 20 countries, 2010–2024. "
    "Replace with official extracts from immunizationdata.who.int for production."
)

# Apply filters
cov_f = coverage[
    (coverage["Year"] >= year_range[0])
    & (coverage["Year"] <= year_range[1])
    & (coverage["Antigen"].isin(selected_antigens))
]
if selected_region != "All":
    cov_f = cov_f[cov_f["WHO_Region"] == selected_region]

inc_f = incidence[
    (incidence["Year"] >= year_range[0])
    & (incidence["Year"] <= year_range[1])
    & (incidence["Disease"].isin(selected_diseases))
]
if selected_region != "All":
    inc_f = inc_f[inc_f["WHO_Region"] == selected_region]

cases_f = cases[
    (cases["Year"] >= year_range[0])
    & (cases["Year"] <= year_range[1])
    & (cases["Disease"].isin(selected_diseases))
]
if selected_region != "All":
    cases_f = cases_f[cases_f["WHO_Region"] == selected_region]

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("Global Vaccination Data Analysis & Visualization")
st.markdown(
    "Interactive dashboard answering key public-health questions on coverage, "
    "disease incidence, vaccine introduction and resource prioritization."
)

# -----------------------------------------------------------------------------
# KPI row
# -----------------------------------------------------------------------------
latest_year = int(coverage["Year"].max())
latest_cov = coverage[coverage["Year"] == latest_year]

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    avg_mcv1 = latest_cov[latest_cov["Antigen"] == "MCV1"]["Coverage"].mean()
    st.metric("Avg MCV1 Coverage (latest)", f"{avg_mcv1:.1f}%")
with kpi2:
    avg_dtp3 = latest_cov[latest_cov["Antigen"] == "DTPCV3"]["Coverage"].mean()
    st.metric("Avg DTPCV3 Coverage (latest)", f"{avg_dtp3:.1f}%")
with kpi3:
    measles_cases = cases[cases["Disease"] == "MEASLES"]["Cases"].sum()
    st.metric("Total Measles Cases (all years)", f"{measles_cases:,.0f}")
with kpi4:
    at_95 = latest_cov[
        (latest_cov["Antigen"] == "MCV1") & (latest_cov["Coverage"] >= 95)
    ]["Code"].nunique()
    total_c = latest_cov[latest_cov["Antigen"] == "MCV1"]["Code"].nunique()
    st.metric("Countries ≥ 95% MCV1", f"{at_95} / {total_c}")

st.markdown("---")

# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Coverage Trends",
    "🔗 Coverage vs Incidence",
    "🌍 Regional & Drop-off",
    "🚀 Introduction & Scenarios",
    "📋 Data Explorer",
])

# ===== Tab 1: Coverage Trends =====
with tab1:
    st.subheader("Vaccination Coverage Trends Over Time")
    trend = (
        cov_f.groupby(["Year", "Antigen"])["Coverage"]
        .mean()
        .reset_index()
    )
    fig = px.line(
        trend,
        x="Year",
        y="Coverage",
        color="Antigen",
        markers=True,
        title="Average Coverage by Antigen",
    )
    fig.update_layout(yaxis_title="Coverage (%)", yaxis_range=[0, 100], height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Coverage by Country (latest year in range)")
    latest_in_range = cov_f[cov_f["Year"] == cov_f["Year"].max()]
    country_avg = (
        latest_in_range.groupby(["Name", "Antigen"])["Coverage"]
        .mean()
        .reset_index()
    )
    fig2 = px.bar(
        country_avg,
        x="Name",
        y="Coverage",
        color="Antigen",
        barmode="group",
        title="Coverage by Country",
    )
    fig2.update_layout(xaxis_tickangle=-45, height=450, yaxis_range=[0, 100])
    st.plotly_chart(fig2, use_container_width=True)

# ===== Tab 2: Coverage vs Incidence =====
with tab2:
    st.subheader("How do vaccination rates correlate with disease incidence?")
    st.markdown(
        "Scatter of **MCV1 coverage** vs **Measles incidence**. "
        "A negative relationship is expected (higher coverage → lower incidence)."
    )

    mcv = coverage[coverage["Antigen"] == "MCV1"][["Code", "Name", "Year", "Coverage", "WHO_Region"]]
    measles = incidence[incidence["Disease"] == "MEASLES"][
        ["Code", "Year", "Incidence_rate"]
    ]
    merged = mcv.merge(measles, on=["Code", "Year"], how="inner")
    merged = merged[
        (merged["Year"] >= year_range[0]) & (merged["Year"] <= year_range[1])
    ]
    if selected_region != "All":
        merged = merged[merged["WHO_Region"] == selected_region]

    corr = merged["Coverage"].corr(merged["Incidence_rate"])
    st.metric("Pearson correlation (MCV1 vs Measles incidence)", f"{corr:.3f}")

    fig = px.scatter(
        merged,
        x="Coverage",
        y="Incidence_rate",
        color="WHO_Region",
        hover_data=["Name", "Year"],
        trendline="ols",
        title="MCV1 Coverage vs Measles Incidence Rate",
    )
    fig.update_layout(height=500, xaxis_title="MCV1 Coverage (%)", yaxis_title="Incidence Rate")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("High coverage (≥80%) yet elevated incidence (outliers)")
    high = (
        merged.groupby(["Code", "Name", "WHO_Region"])
        .agg(avg_cov=("Coverage", "mean"), avg_inc=("Incidence_rate", "mean"))
        .reset_index()
    )
    outliers = high[high["avg_cov"] >= 80].nlargest(10, "avg_inc")
    st.dataframe(
        outliers.rename(columns={"avg_cov": "Avg MCV1 %", "avg_inc": "Avg Incidence"}),
        use_container_width=True,
        hide_index=True,
    )

# ===== Tab 3: Regional & Drop-off =====
with tab3:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Average Coverage by WHO Region")
        reg = (
            cov_f.groupby(["WHO_Region", "Antigen"])["Coverage"]
            .mean()
            .reset_index()
        )
        fig = px.bar(
            reg,
            x="WHO_Region",
            y="Coverage",
            color="Antigen",
            barmode="group",
            title="Regional Coverage Comparison",
        )
        fig.update_layout(yaxis_range=[0, 100], height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Dose Drop-off (1st → subsequent)")
        dtp1 = coverage[coverage["Antigen"] == "DTPCV1"].groupby("Year")["Coverage"].mean()
        dtp3 = coverage[coverage["Antigen"] == "DTPCV3"].groupby("Year")["Coverage"].mean()
        mcv1 = coverage[coverage["Antigen"] == "MCV1"].groupby("Year")["Coverage"].mean()
        mcv2 = coverage[coverage["Antigen"] == "MCV2"].groupby("Year")["Coverage"].mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dtp1.index, y=dtp1.values, name="DTPCV1", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=dtp3.index, y=dtp3.values, name="DTPCV3", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=mcv1.index, y=mcv1.values, name="MCV1", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=mcv2.index, y=mcv2.values, name="MCV2", mode="lines+markers"))
        fig.update_layout(
            title="1st vs Final Dose Coverage",
            yaxis_title="Coverage (%)",
            yaxis_range=[0, 100],
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        drop_dtp = ((dtp1 - dtp3) / dtp1 * 100).mean()
        drop_mcv = ((mcv1 - mcv2) / mcv1 * 100).mean()
        st.write(f"**Avg drop-off DTPCV1 → DTPCV3:** {drop_dtp:.1f}%")
        st.write(f"**Avg drop-off MCV1 → MCV2:** {drop_mcv:.1f}%")

# ===== Tab 4: Introduction & Scenarios =====
with tab4:
    st.subheader("Vaccine Introduction Timelines")
    intro_yes = introduction[introduction["Intro"] == "Yes"]
    first_intro = (
        intro_yes.groupby(["ISO_3_Code", "Country_Name", "WHO_Region", "Description"])["Year"]
        .min()
        .reset_index()
        .rename(columns={"Year": "First_Intro_Year"})
    )
    fig = px.box(
        first_intro,
        x="WHO_Region",
        y="First_Intro_Year",
        color="Description",
        title="Year of First Introduction by WHO Region",
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Scenario 1 – Low Coverage Areas for Resource Allocation")
    st.markdown(
        "Lowest-coverage country/antigen combinations in the latest year of the selected range "
        "(prioritize for targeted interventions). Threshold adjustable below."
    )
    threshold = st.slider("Show coverage below (%)", 40, 95, 80, key="low_cov_threshold")
    latest = cov_f[cov_f["Year"] == cov_f["Year"].max()]
    low = (
        latest[latest["Coverage"] < threshold][
            ["WHO_Region", "Name", "Antigen", "Coverage", "Target_number", "Doses"]
        ]
        .sort_values("Coverage")
        .head(30)
    )
    if low.empty:
        st.success(f"No areas below {threshold}% coverage in the current filter selection. "
                   "Try raising the threshold or expanding the year/region filters.")
    else:
        st.dataframe(low, use_container_width=True, hide_index=True)
        st.caption(f"Showing up to 30 rows with Coverage < {threshold}%")

    st.subheader("Scenario 6 – Progress toward 95% Measles (MCV1) Coverage")
    mcv_prog = (
        coverage[coverage["Antigen"] == "MCV1"]
        .groupby("Year")
        .agg(
            avg_coverage=("Coverage", "mean"),
            countries_at_95=("Coverage", lambda x: (x >= 95).sum()),
            total_countries=("Code", "nunique"),
        )
        .reset_index()
    )
    mcv_prog["pct_at_target"] = (
        mcv_prog["countries_at_95"] / mcv_prog["total_countries"] * 100
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=mcv_prog["Year"],
            y=mcv_prog["avg_coverage"],
            name="Global Avg MCV1 %",
            mode="lines+markers",
        )
    )
    fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="95% target")
    fig.update_layout(
        title="Progress toward 95% MCV1 Coverage by 2030",
        yaxis_title="Coverage (%)",
        yaxis_range=[0, 100],
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(mcv_prog.round(1), use_container_width=True, hide_index=True)

# ===== Tab 5: Data Explorer =====
with tab5:
    st.subheader("Explore Raw / Cleaned Tables")
    table_choice = st.selectbox(
        "Select table",
        ["Coverage", "Incidence", "Reported Cases", "Vaccine Introduction", "Vaccine Schedule"],
    )
    if table_choice == "Coverage":
        st.dataframe(cov_f.head(500), use_container_width=True)
    elif table_choice == "Incidence":
        st.dataframe(inc_f.head(500), use_container_width=True)
    elif table_choice == "Reported Cases":
        st.dataframe(cases_f.head(500), use_container_width=True)
    elif table_choice == "Vaccine Introduction":
        st.dataframe(introduction.head(500), use_container_width=True)
    else:
        st.dataframe(schedule.head(500), use_container_width=True)

    st.download_button(
        "Download filtered coverage CSV",
        cov_f.to_csv(index=False).encode("utf-8"),
        file_name="filtered_coverage.csv",
        mime="text/csv",
    )

# -----------------------------------------------------------------------------
# About / Help
# -----------------------------------------------------------------------------
with st.expander("ℹ️ About this app & how to use real WHO data"):
    st.markdown("""
**What this dashboard answers**
- Correlation between vaccination coverage and disease incidence
- Drop-off between 1st and subsequent doses
- Regional disparities and low-coverage areas for resource allocation
- Vaccine introduction timelines
- Progress toward the 95% measles (MCV1) coverage target by 2030

**Data source**  
Sample data matches the column schemas of the WHO Immunization Data Portal  
(https://immunizationdata.who.int/). For production analysis:

1. Download official Coverage, Incidence, Reported Cases, Introduction and Schedule extracts.
2. Place CSVs in `data/raw/` (keep column names consistent with the sample files).
3. Run `python python/01_data_cleaning.py` then `python python/03_load_to_sqlite.py`.
4. Re-deploy or refresh the Streamlit app.

**Tech stack**  
Streamlit + Plotly • pandas • SQLite star-schema • optional Power BI guide in `/powerbi`
""")

st.markdown("---")
st.caption(
    "Vaccination Data Analysis Project • Python + SQL + Streamlit • "
    "Sample data aligned with WHO Immunization Data Portal schemas • "
    "For educational / portfolio use"
)

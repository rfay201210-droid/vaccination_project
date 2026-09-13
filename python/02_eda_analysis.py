"""
Vaccination Data Analysis Project
=================================
Script 02: Exploratory Data Analysis (EDA)

Answers key questions from the project brief and produces
summary tables + charts saved to reports/.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
CLEAN = BASE / "data" / "cleaned"
REPORTS = BASE / "reports"
REPORTS.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.figsize"] = (12, 6)


def load_cleaned():
    return {
        "coverage": pd.read_csv(CLEAN / "coverage_cleaned.csv"),
        "incidence": pd.read_csv(CLEAN / "incidence_cleaned.csv"),
        "cases": pd.read_csv(CLEAN / "cases_cleaned.csv"),
        "introduction": pd.read_csv(CLEAN / "introduction_cleaned.csv"),
        "schedule": pd.read_csv(CLEAN / "schedule_cleaned.csv"),
    }


def q1_correlation_coverage_incidence(dfs):
    """How do vaccination rates correlate with a decrease in disease incidence?"""
    cov = dfs["coverage"]
    inc = dfs["incidence"]

    # Focus on Measles + MCV1 (most comparable)
    mcv = cov[cov["Antigen"] == "MCV1"][["Code", "Year", "Coverage"]].copy()
    measles = inc[inc["Disease"] == "MEASLES"][["Code", "Year", "Incidence_rate"]].copy()

    merged = mcv.merge(measles, on=["Code", "Year"], how="inner")
    corr = merged["Coverage"].corr(merged["Incidence_rate"])

    fig, ax = plt.subplots()
    sns.scatterplot(data=merged, x="Coverage", y="Incidence_rate", alpha=0.5, ax=ax)
    ax.set_title(f"MCV1 Coverage vs Measles Incidence (corr = {corr:.3f})")
    ax.set_xlabel("MCV1 Coverage (%)")
    ax.set_ylabel("Measles Incidence Rate")
    fig.savefig(REPORTS / "q1_coverage_vs_incidence.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"\n[Q1] Correlation (MCV1 coverage vs Measles incidence): {corr:.3f}")
    print("     Negative correlation expected → higher coverage linked to lower incidence.")
    return corr


def q2_dropoff_first_to_subsequent(dfs):
    """What is the drop-off rate between 1st dose and subsequent doses?"""
    cov = dfs["coverage"]
    # DTPCV1 vs DTPCV3 and MCV1 vs MCV2
    d1 = cov[cov["Antigen"] == "DTPCV1"].groupby("Year")["Coverage"].mean()
    d3 = cov[cov["Antigen"] == "DTPCV3"].groupby("Year")["Coverage"].mean()
    m1 = cov[cov["Antigen"] == "MCV1"].groupby("Year")["Coverage"].mean()
    m2 = cov[cov["Antigen"] == "MCV2"].groupby("Year")["Coverage"].mean()

    drop_dtp = ((d1 - d3) / d1 * 100).mean()
    drop_mcv = ((m1 - m2) / m1 * 100).mean()

    fig, ax = plt.subplots()
    ax.plot(d1.index, d1.values, label="DTPCV1", marker="o")
    ax.plot(d3.index, d3.values, label="DTPCV3", marker="o")
    ax.plot(m1.index, m1.values, label="MCV1", marker="s")
    ax.plot(m2.index, m2.values, label="MCV2", marker="s")
    ax.set_title("Dose Drop-off: 1st vs Final Dose Coverage")
    ax.set_ylabel("Average Coverage (%)")
    ax.legend()
    fig.savefig(REPORTS / "q2_dose_dropoff.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"\n[Q2] Average drop-off DTPCV1→DTPCV3: {drop_dtp:.1f}%")
    print(f"     Average drop-off MCV1→MCV2  : {drop_mcv:.1f}%")
    return drop_dtp, drop_mcv


def q3_regional_disparities(dfs):
    """Regional differences in coverage (proxy for many easy questions)."""
    cov = dfs["coverage"]
    intro = dfs["introduction"][["ISO_3_Code", "WHO_Region"]].drop_duplicates()
    merged = cov.merge(intro, left_on="Code", right_on="ISO_3_Code", how="left")

    region_avg = (
        merged[merged["Antigen"].isin(["DTPCV3", "MCV1", "POL3"])]
        .groupby(["WHO_Region", "Antigen"])["Coverage"]
        .mean()
        .unstack()
        .round(1)
    )
    print("\n[Regional Coverage Averages]")
    print(region_avg)

    fig, ax = plt.subplots()
    region_avg.plot(kind="bar", ax=ax)
    ax.set_title("Average Vaccination Coverage by WHO Region")
    ax.set_ylabel("Coverage (%)")
    ax.legend(title="Antigen")
    plt.xticks(rotation=45)
    fig.savefig(REPORTS / "regional_coverage.png", dpi=150, bbox_inches="tight")
    plt.close()
    return region_avg


def q4_high_incidence_despite_high_coverage(dfs):
    """Which regions/countries have high disease incidence despite high vaccination rates?"""
    cov = dfs["coverage"]
    inc = dfs["incidence"]
    mcv = cov[cov["Antigen"] == "MCV1"].groupby(["Code", "Name"])["Coverage"].mean().reset_index()
    measles = inc[inc["Disease"] == "MEASLES"].groupby(["Code", "Name"])["Incidence_rate"].mean().reset_index()
    merged = mcv.merge(measles, on=["Code", "Name"])

    high_cov = merged[merged["Coverage"] >= 80]
    outliers = high_cov.nlargest(10, "Incidence_rate")
    print("\n[Q10] High MCV1 coverage (≥80%) but still elevated measles incidence:")
    print(outliers.to_string(index=False))
    outliers.to_csv(REPORTS / "high_cov_high_inc.csv", index=False)
    return outliers


def q5_vaccine_introduction_impact(dfs):
    """Is there a correlation between vaccine introduction and decrease in disease cases?"""
    intro = dfs["introduction"]
    cases = dfs["cases"]

    # Example: Rotavirus introduction vs (proxy) related cases – using available diseases
    # For demonstration we look at overall case trends around introduction years
    rot_intro = intro[intro["Description"].str.contains("Rotavirus", case=False)]
    first_intro = rot_intro[rot_intro["Intro"] == "Yes"].groupby("ISO_3_Code")["Year"].min()

    print("\n[Medium Q1] Example – Rotavirus vaccine first introduction year by country:")
    print(first_intro.head(10).to_string())
    return first_intro


def q6_coverage_trends(dfs):
    """Overall coverage trends over time."""
    cov = dfs["coverage"]
    key = cov[cov["Antigen"].isin(["DTPCV3", "MCV1", "POL3", "HepB3"])]
    trend = key.groupby(["Year", "Antigen"])["Coverage"].mean().unstack()

    fig, ax = plt.subplots()
    trend.plot(ax=ax, marker="o")
    ax.set_title("Global Average Coverage Trends (selected antigens)")
    ax.set_ylabel("Coverage (%)")
    ax.set_ylim(0, 100)
    fig.savefig(REPORTS / "coverage_trends.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n[Coverage Trends] Saved to reports/coverage_trends.png")
    return trend


def scenario_low_coverage_regions(dfs):
    """Scenario 1: Identify regions with low vaccination coverage for resource allocation."""
    cov = dfs["coverage"]
    intro = dfs["introduction"][["ISO_3_Code", "WHO_Region"]].drop_duplicates()
    latest = cov[cov["Year"] == cov["Year"].max()]
    latest = latest.merge(intro, left_on="Code", right_on="ISO_3_Code", how="left")

    low = (
        latest[latest["Antigen"].isin(["DTPCV3", "MCV1"])]
        .groupby(["WHO_Region", "Name", "Antigen"])["Coverage"]
        .mean()
        .reset_index()
    )
    low = low[low["Coverage"] < 70].sort_values("Coverage")
    print("\n[Scenario 1] Low coverage (<70%) areas for resource prioritization:")
    print(low.head(15).to_string(index=False))
    low.to_csv(REPORTS / "low_coverage_priority.csv", index=False)
    return low


def main():
    dfs = load_cleaned()
    print("=" * 60)
    print("VACCINATION DATA – EXPLORATORY ANALYSIS")
    print("=" * 60)

    q1_correlation_coverage_incidence(dfs)
    q2_dropoff_first_to_subsequent(dfs)
    q3_regional_disparities(dfs)
    q4_high_incidence_despite_high_coverage(dfs)
    q5_vaccine_introduction_impact(dfs)
    q6_coverage_trends(dfs)
    scenario_low_coverage_regions(dfs)

    print("\n" + "=" * 60)
    print("EDA complete. Charts and CSVs saved to reports/")
    print("=" * 60)


if __name__ == "__main__":
    main()

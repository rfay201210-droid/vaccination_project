"""
Vaccination Data Analysis Project
=================================
Script 01: Data Cleaning & Normalization

Handles missing values, unit consistency, date/year formatting,
and prepares clean CSVs ready for SQL loading.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
SAMPLE_DIR = BASE_DIR / "data" / "sample"
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


def load_data(prefer_sample: bool = True) -> dict[str, pd.DataFrame]:
    """Load raw or sample datasets. Falls back to sample if raw is empty."""
    sources = {
        "coverage": "coverage_data.csv",
        "incidence": "incidence_rate.csv",
        "cases": "reported_cases.csv",
        "introduction": "vaccine_introduction.csv",
        "schedule": "vaccine_schedule.csv",
    }
    dfs = {}
    for key, fname in sources.items():
        # Prefer sample for reproducibility in this project
        path = SAMPLE_DIR / fname if prefer_sample else RAW_DIR / fname
        if not path.exists():
            path = SAMPLE_DIR / fname
        logger.info(f"Loading {key} from {path}")
        dfs[key] = pd.read_csv(path)
    return dfs


def clean_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Clean coverage table."""
    df = df.copy()
    # Standardize column names
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

    # Handle missing
    df["Coverage"] = pd.to_numeric(df["Coverage"], errors="coerce")
    df["Target_number"] = pd.to_numeric(df["Target_number"], errors="coerce")
    df["Doses"] = pd.to_numeric(df["Doses"], errors="coerce")

    # Impute coverage from doses/target when possible
    mask = df["Coverage"].isna() & df["Doses"].notna() & df["Target_number"].notna() & (df["Target_number"] > 0)
    df.loc[mask, "Coverage"] = (df.loc[mask, "Doses"] / df.loc[mask, "Target_number"] * 100).round(1)

    # Drop rows with no coverage and no doses
    before = len(df)
    df = df.dropna(subset=["Coverage"], how="all")
    logger.info(f"Coverage: dropped {before - len(df)} rows with missing coverage")

    # Clip coverage to sensible range
    df["Coverage"] = df["Coverage"].clip(0, 100)

    # Year consistency
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Year", "Code", "Antigen"])

    # Normalize antigen codes
    df["Antigen"] = df["Antigen"].str.upper().str.strip()

    return df.reset_index(drop=True)


def clean_incidence(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df["Incidence_rate"] = pd.to_numeric(df["Incidence_rate"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Incidence_rate", "Year", "Code", "Disease"])
    df["Disease"] = df["Disease"].str.upper().str.strip()
    return df.reset_index(drop=True)


def clean_cases(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df["Cases"] = pd.to_numeric(df["Cases"], errors="coerce").fillna(0).astype(int)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Year", "Code", "Disease"])
    df["Disease"] = df["Disease"].str.upper().str.strip()
    return df.reset_index(drop=True)


def clean_introduction(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Intro"] = df["Intro"].str.strip().str.title()
    df = df.dropna(subset=["Year", "ISO_3_Code", "Description"])
    return df.reset_index(drop=True)


def clean_schedule(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Year", "ISO_3_Code", "Vaccine_code"])
    return df.reset_index(drop=True)


def main():
    logger.info("Starting data cleaning pipeline")
    dfs = load_data(prefer_sample=True)

    cleaned = {
        "coverage": clean_coverage(dfs["coverage"]),
        "incidence": clean_incidence(dfs["incidence"]),
        "cases": clean_cases(dfs["cases"]),
        "introduction": clean_introduction(dfs["introduction"]),
        "schedule": clean_schedule(dfs["schedule"]),
    }

    for name, df in cleaned.items():
        out = CLEAN_DIR / f"{name}_cleaned.csv"
        df.to_csv(out, index=False)
        logger.info(f"Saved {name}: {len(df):,} rows → {out}")

    # Quick quality report
    print("\n===== DATA QUALITY SUMMARY =====")
    for name, df in cleaned.items():
        print(f"\n{name.upper()}")
        print(f"  Rows          : {len(df):,}")
        print(f"  Columns       : {list(df.columns)}")
        print(f"  Missing %     :\n{df.isna().mean().round(3).to_string()}")
        print(f"  Year range  : {df['Year'].min()} – {df['Year'].max()}")

    logger.info("Cleaning complete. Files ready for SQL load.")


if __name__ == "__main__":
    main()

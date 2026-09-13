"""
Load cleaned CSVs into a local SQLite database.
This creates the fully functional SQL database required by the project.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
CLEAN = BASE / "data" / "cleaned"
DB_PATH = BASE / "sql" / "vaccination.db"
SCHEMA_PATH = BASE / "sql" / "01_schema.sql"


def create_schema(conn: sqlite3.Connection):
    """Create tables adapted for SQLite (SERIAL → INTEGER PRIMARY KEY AUTOINCREMENT)."""
    schema = """
    DROP TABLE IF EXISTS fact_coverage;
    DROP TABLE IF EXISTS fact_incidence;
    DROP TABLE IF EXISTS fact_reported_cases;
    DROP TABLE IF EXISTS fact_vaccine_introduction;
    DROP TABLE IF EXISTS fact_vaccine_schedule;
    DROP TABLE IF EXISTS dim_country;
    DROP TABLE IF EXISTS dim_antigen;
    DROP TABLE IF EXISTS dim_disease;
    DROP TABLE IF EXISTS dim_year;
    DROP TABLE IF EXISTS dim_coverage_category;

    CREATE TABLE dim_country (
        country_code    TEXT PRIMARY KEY,
        country_name    TEXT NOT NULL,
        who_region      TEXT
    );

    CREATE TABLE dim_antigen (
        antigen_code        TEXT PRIMARY KEY,
        antigen_description TEXT NOT NULL
    );

    CREATE TABLE dim_disease (
        disease_code        TEXT PRIMARY KEY,
        disease_description TEXT NOT NULL
    );

    CREATE TABLE dim_year (
        year_id     INTEGER PRIMARY KEY,
        decade      TEXT
    );

    CREATE TABLE dim_coverage_category (
        category_code        TEXT PRIMARY KEY,
        category_description TEXT NOT NULL
    );

    CREATE TABLE fact_coverage (
        coverage_id             INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code            TEXT NOT NULL REFERENCES dim_country(country_code),
        year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
        antigen_code            TEXT NOT NULL REFERENCES dim_antigen(antigen_code),
        coverage_category       TEXT REFERENCES dim_coverage_category(category_code),
        target_number           INTEGER,
        doses_administered      INTEGER,
        coverage_pct            REAL CHECK (coverage_pct >= 0 AND coverage_pct <= 100),
        UNIQUE (country_code, year_id, antigen_code, coverage_category)
    );

    CREATE TABLE fact_incidence (
        incidence_id            INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code            TEXT NOT NULL REFERENCES dim_country(country_code),
        year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
        disease_code            TEXT NOT NULL REFERENCES dim_disease(disease_code),
        denominator             TEXT,
        incidence_rate          REAL,
        UNIQUE (country_code, year_id, disease_code)
    );

    CREATE TABLE fact_reported_cases (
        case_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code            TEXT NOT NULL REFERENCES dim_country(country_code),
        year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
        disease_code            TEXT NOT NULL REFERENCES dim_disease(disease_code),
        cases                   INTEGER CHECK (cases >= 0),
        UNIQUE (country_code, year_id, disease_code)
    );

    CREATE TABLE fact_vaccine_introduction (
        intro_id                INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code            TEXT NOT NULL REFERENCES dim_country(country_code),
        year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
        vaccine_description     TEXT NOT NULL,
        introduced              INTEGER NOT NULL,  -- 0/1
        UNIQUE (country_code, year_id, vaccine_description)
    );

    CREATE TABLE fact_vaccine_schedule (
        schedule_id             INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code            TEXT NOT NULL REFERENCES dim_country(country_code),
        year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
        vaccine_code            TEXT NOT NULL,
        vaccine_description     TEXT,
        schedule_round          TEXT,
        target_pop              TEXT,
        target_pop_description  TEXT,
        geo_area                TEXT,
        age_administered        TEXT,
        source_comment          TEXT
    );

    CREATE INDEX idx_cov_country_year ON fact_coverage(country_code, year_id);
    CREATE INDEX idx_cov_antigen ON fact_coverage(antigen_code);
    CREATE INDEX idx_inc_disease_year ON fact_incidence(disease_code, year_id);
    CREATE INDEX idx_cases_disease_year ON fact_reported_cases(disease_code, year_id);
    """
    conn.executescript(schema)
    logger.info("Schema created")


def load_data(conn: sqlite3.Connection):
    coverage = pd.read_csv(CLEAN / "coverage_cleaned.csv")
    incidence = pd.read_csv(CLEAN / "incidence_cleaned.csv")
    cases = pd.read_csv(CLEAN / "cases_cleaned.csv")
    introduction = pd.read_csv(CLEAN / "introduction_cleaned.csv")
    schedule = pd.read_csv(CLEAN / "schedule_cleaned.csv")

    # Dimensions
    countries = coverage[["Code", "Name"]].drop_duplicates()
    countries.columns = ["country_code", "country_name"]
    region_map = introduction[["ISO_3_Code", "WHO_Region"]].drop_duplicates()
    region_map.columns = ["country_code", "who_region"]
    countries = countries.merge(region_map, on="country_code", how="left")
    countries.to_sql("dim_country", conn, if_exists="append", index=False)

    antigens = coverage[["Antigen", "Antigen_description"]].drop_duplicates()
    antigens.columns = ["antigen_code", "antigen_description"]
    antigens.to_sql("dim_antigen", conn, if_exists="append", index=False)

    diseases = pd.concat([
        incidence[["Disease", "Disease_description"]],
        cases[["Disease", "Disease_description"]]
    ]).drop_duplicates()
    diseases.columns = ["disease_code", "disease_description"]
    diseases.to_sql("dim_disease", conn, if_exists="append", index=False)

    years = coverage[["Year"]].drop_duplicates()
    years["decade"] = years["Year"].apply(
        lambda y: "2010s" if 2010 <= y <= 2019 else ("2020s" if 2020 <= y <= 2029 else "Other")
    )
    years.columns = ["year_id", "decade"]
    years.to_sql("dim_year", conn, if_exists="append", index=False)

    cats = coverage[["Coverage_category", "Coverage_category_description"]].drop_duplicates()
    cats.columns = ["category_code", "category_description"]
    cats.to_sql("dim_coverage_category", conn, if_exists="append", index=False)

    # Facts
    cov_fact = coverage.rename(columns={
        "Code": "country_code", "Year": "year_id", "Antigen": "antigen_code",
        "Coverage_category": "coverage_category", "Target_number": "target_number",
        "Doses": "doses_administered", "Coverage": "coverage_pct"
    })[["country_code", "year_id", "antigen_code", "coverage_category",
        "target_number", "doses_administered", "coverage_pct"]]
    cov_fact.to_sql("fact_coverage", conn, if_exists="append", index=False)

    inc_fact = incidence.rename(columns={
        "Code": "country_code", "Year": "year_id", "Disease": "disease_code",
        "Denominator": "denominator", "Incidence_rate": "incidence_rate"
    })[["country_code", "year_id", "disease_code", "denominator", "incidence_rate"]]
    inc_fact.to_sql("fact_incidence", conn, if_exists="append", index=False)

    case_fact = cases.rename(columns={
        "Code": "country_code", "Year": "year_id", "Disease": "disease_code", "Cases": "cases"
    })[["country_code", "year_id", "disease_code", "cases"]]
    case_fact.to_sql("fact_reported_cases", conn, if_exists="append", index=False)

    intro_fact = introduction.rename(columns={
        "ISO_3_Code": "country_code", "Year": "year_id",
        "Description": "vaccine_description"
    })
    intro_fact["introduced"] = (intro_fact["Intro"] == "Yes").astype(int)
    intro_fact = intro_fact[["country_code", "year_id", "vaccine_description", "introduced"]]
    intro_fact.to_sql("fact_vaccine_introduction", conn, if_exists="append", index=False)

    sched_fact = schedule.rename(columns={
        "ISO_3_Code": "country_code", "Year": "year_id",
        "Vaccine_code": "vaccine_code", "Vaccine_description": "vaccine_description",
        "Schedule_rounds": "schedule_round", "Target_pop": "target_pop",
        "Target_pop_description": "target_pop_description", "Geoarea": "geo_area",
        "Age_administered": "age_administered", "Source_comment": "source_comment"
    })[["country_code", "year_id", "vaccine_code", "vaccine_description",
        "schedule_round", "target_pop", "target_pop_description",
        "geo_area", "age_administered", "source_comment"]]
    sched_fact.to_sql("fact_vaccine_schedule", conn, if_exists="append", index=False)

    logger.info("All data loaded into SQLite")


def verify(conn: sqlite3.Connection):
    tables = [
        "dim_country", "dim_antigen", "dim_disease", "dim_year",
        "dim_coverage_category", "fact_coverage", "fact_incidence",
        "fact_reported_cases", "fact_vaccine_introduction", "fact_vaccine_schedule"
    ]
    print("\n===== DATABASE ROW COUNTS =====")
    for t in tables:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:35s} {cnt:,}")


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)
        load_data(conn)
        conn.commit()
        verify(conn)
        logger.info(f"Database ready: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

-- ============================================================
-- Load cleaned CSVs into the normalized schema
-- Run after 01_schema.sql
-- Assumes CSV files are accessible to the database engine
-- (adjust paths or use COPY / LOAD DATA as appropriate)
-- ============================================================

-- Example for PostgreSQL (adjust path and use \copy in psql if needed)
-- For SQLite you can use .import or Python loader (see 03_python_to_sql.py)

-- ------------------------------------------------------------
-- 1. Populate dimensions from cleaned data
-- ------------------------------------------------------------

-- dim_country (from coverage + introduction)
INSERT INTO dim_country (country_code, country_name, who_region)
SELECT DISTINCT
    Code,
    Name,
    NULL                       -- will be updated from introduction
FROM coverage_cleaned
ON CONFLICT (country_code) DO NOTHING;

UPDATE dim_country c
SET who_region = i.WHO_Region
FROM (
    SELECT DISTINCT ISO_3_Code, WHO_Region
    FROM introduction_cleaned
) i
WHERE c.country_code = i.ISO_3_Code;

-- dim_antigen
INSERT INTO dim_antigen (antigen_code, antigen_description)
SELECT DISTINCT Antigen, Antigen_description
FROM coverage_cleaned
ON CONFLICT (antigen_code) DO NOTHING;

-- dim_disease
INSERT INTO dim_disease (disease_code, disease_description)
SELECT DISTINCT Disease, Disease_description
FROM incidence_cleaned
ON CONFLICT (disease_code) DO NOTHING;

INSERT INTO dim_disease (disease_code, disease_description)
SELECT DISTINCT Disease, Disease_description
FROM cases_cleaned
ON CONFLICT (disease_code) DO NOTHING;

-- dim_year
INSERT INTO dim_year (year_id, decade)
SELECT DISTINCT Year,
       CASE
           WHEN Year BETWEEN 2010 AND 2019 THEN '2010s'
           WHEN Year BETWEEN 2020 AND 2029 THEN '2020s'
           ELSE 'Other'
       END
FROM coverage_cleaned
ON CONFLICT (year_id) DO NOTHING;

-- dim_coverage_category
INSERT INTO dim_coverage_category (category_code, category_description)
SELECT DISTINCT Coverage_category, Coverage_category_description
FROM coverage_cleaned
ON CONFLICT (category_code) DO NOTHING;

-- ------------------------------------------------------------
-- 2. Fact tables
-- ------------------------------------------------------------

INSERT INTO fact_coverage (
    country_code, year_id, antigen_code, coverage_category,
    target_number, doses_administered, coverage_pct
)
SELECT
    Code, Year, Antigen, Coverage_category,
    Target_number, Doses, Coverage
FROM coverage_cleaned
ON CONFLICT (country_code, year_id, antigen_code, coverage_category) DO NOTHING;

INSERT INTO fact_incidence (
    country_code, year_id, disease_code, denominator, incidence_rate
)
SELECT Code, Year, Disease, Denominator, Incidence_rate
FROM incidence_cleaned
ON CONFLICT (country_code, year_id, disease_code) DO NOTHING;

INSERT INTO fact_reported_cases (
    country_code, year_id, disease_code, cases
)
SELECT Code, Year, Disease, Cases
FROM cases_cleaned
ON CONFLICT (country_code, year_id, disease_code) DO NOTHING;

INSERT INTO fact_vaccine_introduction (
    country_code, year_id, vaccine_description, introduced
)
SELECT
    ISO_3_Code, Year, Description,
    CASE WHEN Intro = 'Yes' THEN TRUE ELSE FALSE END
FROM introduction_cleaned
ON CONFLICT (country_code, year_id, vaccine_description) DO NOTHING;

INSERT INTO fact_vaccine_schedule (
    country_code, year_id, vaccine_code, vaccine_description,
    schedule_round, target_pop, target_pop_description,
    geo_area, age_administered, source_comment
)
SELECT
    ISO_3_Code, Year, Vaccine_code, Vaccine_description,
    Schedule_rounds, Target_pop, Target_pop_description,
    Geoarea, Age_administered, Source_comment
FROM schedule_cleaned;

-- ------------------------------------------------------------
-- Verification queries
-- ------------------------------------------------------------
SELECT 'dim_country' AS table_name, COUNT(*) AS rows FROM dim_country
UNION ALL SELECT 'dim_antigen', COUNT(*) FROM dim_antigen
UNION ALL SELECT 'dim_disease', COUNT(*) FROM dim_disease
UNION ALL SELECT 'dim_year', COUNT(*) FROM dim_year
UNION ALL SELECT 'fact_coverage', COUNT(*) FROM fact_coverage
UNION ALL SELECT 'fact_incidence', COUNT(*) FROM fact_incidence
UNION ALL SELECT 'fact_reported_cases', COUNT(*) FROM fact_reported_cases
UNION ALL SELECT 'fact_vaccine_introduction', COUNT(*) FROM fact_vaccine_introduction
UNION ALL SELECT 'fact_vaccine_schedule', COUNT(*) FROM fact_vaccine_schedule;

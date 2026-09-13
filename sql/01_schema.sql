-- ============================================================
-- Vaccination Data Analysis Project
-- SQL Schema – Normalized Relational Design
-- Compatible with PostgreSQL / SQLite / MySQL
-- ============================================================

-- Drop existing objects (safe re-run)
DROP TABLE IF EXISTS fact_coverage CASCADE;
DROP TABLE IF EXISTS fact_incidence CASCADE;
DROP TABLE IF EXISTS fact_reported_cases CASCADE;
DROP TABLE IF EXISTS fact_vaccine_introduction CASCADE;
DROP TABLE IF EXISTS fact_vaccine_schedule CASCADE;
DROP TABLE IF EXISTS dim_country CASCADE;
DROP TABLE IF EXISTS dim_antigen CASCADE;
DROP TABLE IF EXISTS dim_disease CASCADE;
DROP TABLE IF EXISTS dim_year CASCADE;
DROP TABLE IF EXISTS dim_coverage_category CASCADE;

-- ------------------------------------------------------------
-- Dimension Tables
-- ------------------------------------------------------------

CREATE TABLE dim_country (
    country_code    CHAR(3) PRIMARY KEY,          -- ISO Alpha-3
    country_name    VARCHAR(150) NOT NULL,
    who_region      VARCHAR(10),                  -- AFRO, AMRO, EMRO, EURO, SEARO, WPRO
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_antigen (
    antigen_code        VARCHAR(20) PRIMARY KEY,
    antigen_description VARCHAR(200) NOT NULL
);

CREATE TABLE dim_disease (
    disease_code        VARCHAR(30) PRIMARY KEY,
    disease_description VARCHAR(150) NOT NULL
);

CREATE TABLE dim_year (
    year_id     INTEGER PRIMARY KEY,              -- e.g. 2023
    decade      VARCHAR(10)                       -- '2010s', '2020s'
);

CREATE TABLE dim_coverage_category (
    category_code        VARCHAR(20) PRIMARY KEY, -- ADMIN, OFFICIAL, WUENIC
    category_description VARCHAR(150) NOT NULL
);

-- ------------------------------------------------------------
-- Fact Tables
-- ------------------------------------------------------------

CREATE TABLE fact_coverage (
    coverage_id             SERIAL PRIMARY KEY,
    country_code            CHAR(3) NOT NULL REFERENCES dim_country(country_code),
    year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
    antigen_code            VARCHAR(20) NOT NULL REFERENCES dim_antigen(antigen_code),
    coverage_category       VARCHAR(20) REFERENCES dim_coverage_category(category_code),
    target_number           BIGINT,
    doses_administered      BIGINT,
    coverage_pct            NUMERIC(5,2) CHECK (coverage_pct >= 0 AND coverage_pct <= 100),
    CONSTRAINT uq_coverage UNIQUE (country_code, year_id, antigen_code, coverage_category)
);

CREATE TABLE fact_incidence (
    incidence_id            SERIAL PRIMARY KEY,
    country_code            CHAR(3) NOT NULL REFERENCES dim_country(country_code),
    year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
    disease_code            VARCHAR(30) NOT NULL REFERENCES dim_disease(disease_code),
    denominator             VARCHAR(100),
    incidence_rate          NUMERIC(12,4),
    CONSTRAINT uq_incidence UNIQUE (country_code, year_id, disease_code)
);

CREATE TABLE fact_reported_cases (
    case_id                 SERIAL PRIMARY KEY,
    country_code            CHAR(3) NOT NULL REFERENCES dim_country(country_code),
    year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
    disease_code            VARCHAR(30) NOT NULL REFERENCES dim_disease(disease_code),
    cases                   INTEGER CHECK (cases >= 0),
    CONSTRAINT uq_cases UNIQUE (country_code, year_id, disease_code)
);

CREATE TABLE fact_vaccine_introduction (
    intro_id                SERIAL PRIMARY KEY,
    country_code            CHAR(3) NOT NULL REFERENCES dim_country(country_code),
    year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
    vaccine_description     VARCHAR(150) NOT NULL,
    introduced              BOOLEAN NOT NULL,     -- TRUE = Yes
    CONSTRAINT uq_intro UNIQUE (country_code, year_id, vaccine_description)
);

CREATE TABLE fact_vaccine_schedule (
    schedule_id             SERIAL PRIMARY KEY,
    country_code            CHAR(3) NOT NULL REFERENCES dim_country(country_code),
    year_id                 INTEGER NOT NULL REFERENCES dim_year(year_id),
    vaccine_code            VARCHAR(20) NOT NULL,
    vaccine_description     VARCHAR(150),
    schedule_round          VARCHAR(10),
    target_pop              VARCHAR(50),
    target_pop_description  VARCHAR(150),
    geo_area                VARCHAR(50),
    age_administered        VARCHAR(50),
    source_comment          TEXT
);

-- ------------------------------------------------------------
-- Indexes for query performance
-- ------------------------------------------------------------
CREATE INDEX idx_cov_country_year ON fact_coverage(country_code, year_id);
CREATE INDEX idx_cov_antigen ON fact_coverage(antigen_code);
CREATE INDEX idx_inc_disease_year ON fact_incidence(disease_code, year_id);
CREATE INDEX idx_cases_disease_year ON fact_reported_cases(disease_code, year_id);
CREATE INDEX idx_intro_country ON fact_vaccine_introduction(country_code);

-- ------------------------------------------------------------
-- Helpful Views for Power BI / Analytics
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_coverage_with_region AS
SELECT
    c.country_code,
    c.country_name,
    c.who_region,
    f.year_id,
    a.antigen_code,
    a.antigen_description,
    f.coverage_category,
    f.target_number,
    f.doses_administered,
    f.coverage_pct
FROM fact_coverage f
JOIN dim_country c ON f.country_code = c.country_code
JOIN dim_antigen a ON f.antigen_code = a.antigen_code;

CREATE OR REPLACE VIEW vw_measles_coverage_incidence AS
SELECT
    c.country_code,
    c.country_name,
    c.who_region,
    cov.year_id,
    cov.coverage_pct AS mcv1_coverage,
    inc.incidence_rate AS measles_incidence
FROM fact_coverage cov
JOIN dim_country c ON cov.country_code = c.country_code
LEFT JOIN fact_incidence inc
    ON cov.country_code = inc.country_code
   AND cov.year_id = inc.year_id
   AND inc.disease_code = 'MEASLES'
WHERE cov.antigen_code = 'MCV1';

COMMENT ON TABLE fact_coverage IS 'Vaccination coverage by country, year, antigen and reporting category';
COMMENT ON TABLE fact_incidence IS 'Disease incidence rates';
COMMENT ON TABLE fact_reported_cases IS 'Absolute reported cases of vaccine-preventable diseases';
COMMENT ON TABLE fact_vaccine_introduction IS 'Yearly status of vaccine introduction into national programmes';
COMMENT ON TABLE fact_vaccine_schedule IS 'National immunization schedule details';

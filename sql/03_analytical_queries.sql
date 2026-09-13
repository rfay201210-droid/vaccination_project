-- ============================================================
-- Analytical SQL Queries – Answers to Project Questions
-- Run against vaccination.db (SQLite) or equivalent PostgreSQL DB
-- ============================================================

-- Q1 / Q9: Correlation proxy – average coverage vs average incidence (Measles)
SELECT
    c.who_region,
    ROUND(AVG(cov.coverage_pct), 1) AS avg_mcv1_coverage,
    ROUND(AVG(inc.incidence_rate), 2) AS avg_measles_incidence
FROM fact_coverage cov
JOIN dim_country c ON cov.country_code = c.country_code
LEFT JOIN fact_incidence inc
    ON cov.country_code = inc.country_code
   AND cov.year_id = inc.year_id
   AND inc.disease_code = 'MEASLES'
WHERE cov.antigen_code = 'MCV1'
GROUP BY c.who_region
ORDER BY avg_mcv1_coverage DESC;

-- Q2: Drop-off between 1st and 3rd dose (DTP) and 1st/2nd dose (MCV)
SELECT
    year_id,
    ROUND(AVG(CASE WHEN antigen_code = 'DTPCV1' THEN coverage_pct END), 1) AS dtp1,
    ROUND(AVG(CASE WHEN antigen_code = 'DTPCV3' THEN coverage_pct END), 1) AS dtp3,
    ROUND(AVG(CASE WHEN antigen_code = 'MCV1' THEN coverage_pct END), 1) AS mcv1,
    ROUND(AVG(CASE WHEN antigen_code = 'MCV2' THEN coverage_pct END), 1) AS mcv2,
    ROUND(
        (AVG(CASE WHEN antigen_code = 'DTPCV1' THEN coverage_pct END) -
         AVG(CASE WHEN antigen_code = 'DTPCV3' THEN coverage_pct END))
        / NULLIF(AVG(CASE WHEN antigen_code = 'DTPCV1' THEN coverage_pct END), 0) * 100, 1
    ) AS dtp_dropoff_pct
FROM fact_coverage
WHERE antigen_code IN ('DTPCV1', 'DTPCV3', 'MCV1', 'MCV2')
GROUP BY year_id
ORDER BY year_id;

-- Q10: High coverage but still high incidence (Measles)
SELECT
    c.country_name,
    c.who_region,
    ROUND(AVG(cov.coverage_pct), 1) AS avg_mcv1,
    ROUND(AVG(inc.incidence_rate), 2) AS avg_measles_inc
FROM fact_coverage cov
JOIN dim_country c ON cov.country_code = c.country_code
JOIN fact_incidence inc
    ON cov.country_code = inc.country_code
   AND cov.year_id = inc.year_id
   AND inc.disease_code = 'MEASLES'
WHERE cov.antigen_code = 'MCV1'
GROUP BY c.country_name, c.who_region
HAVING AVG(cov.coverage_pct) >= 80
ORDER BY avg_measles_inc DESC
LIMIT 15;

-- Medium Q1 / Q2: Vaccine introduction vs later case trends (example – Rotavirus)
WITH first_intro AS (
    SELECT country_code, MIN(year_id) AS intro_year
    FROM fact_vaccine_introduction
    WHERE vaccine_description LIKE '%Rotavirus%' AND introduced = 1
    GROUP BY country_code
)
SELECT
    c.country_name,
    f.intro_year,
    SUM(CASE WHEN rc.year_id < f.intro_year THEN rc.cases ELSE 0 END) AS cases_before,
    SUM(CASE WHEN rc.year_id >= f.intro_year THEN rc.cases ELSE 0 END) AS cases_after
FROM first_intro f
JOIN dim_country c ON f.country_code = c.country_code
LEFT JOIN fact_reported_cases rc ON f.country_code = rc.country_code
GROUP BY c.country_name, f.intro_year
ORDER BY f.intro_year;

-- Medium Q3: Diseases with largest case reduction over time
SELECT
    d.disease_description,
    SUM(CASE WHEN rc.year_id BETWEEN 2010 AND 2014 THEN rc.cases ELSE 0 END) AS cases_2010_14,
    SUM(CASE WHEN rc.year_id BETWEEN 2020 AND 2024 THEN rc.cases ELSE 0 END) AS cases_2020_24,
    ROUND(
        (SUM(CASE WHEN rc.year_id BETWEEN 2010 AND 2014 THEN rc.cases ELSE 0 END) -
         SUM(CASE WHEN rc.year_id BETWEEN 2020 AND 2024 THEN rc.cases ELSE 0 END)) * 100.0 /
        NULLIF(SUM(CASE WHEN rc.year_id BETWEEN 2010 AND 2014 THEN rc.cases ELSE 0 END), 0), 1
    ) AS pct_reduction
FROM fact_reported_cases rc
JOIN dim_disease d ON rc.disease_code = d.disease_code
GROUP BY d.disease_description
ORDER BY pct_reduction DESC;

-- Medium Q4: % of target population covered by each vaccine (latest year)
SELECT
    a.antigen_description,
    ROUND(AVG(cov.coverage_pct), 1) AS avg_coverage_pct,
    SUM(cov.doses_administered) AS total_doses,
    SUM(cov.target_number) AS total_target
FROM fact_coverage cov
JOIN dim_antigen a ON cov.antigen_code = a.antigen_code
WHERE cov.year_id = (SELECT MAX(year_id) FROM fact_coverage)
GROUP BY a.antigen_description
ORDER BY avg_coverage_pct DESC;

-- Medium Q6: Disparities in vaccine introduction timelines by WHO region
SELECT
    c.who_region,
    vi.vaccine_description,
    MIN(CASE WHEN vi.introduced = 1 THEN vi.year_id END) AS earliest_intro,
    MAX(CASE WHEN vi.introduced = 1 THEN vi.year_id END) AS latest_intro,
    COUNT(DISTINCT CASE WHEN vi.introduced = 1 THEN vi.country_code END) AS countries_introduced
FROM fact_vaccine_introduction vi
JOIN dim_country c ON vi.country_code = c.country_code
GROUP BY c.who_region, vi.vaccine_description
ORDER BY c.who_region, earliest_intro;

-- Medium Q9: Coverage gaps for high-priority antigens (HepB, BCG proxy for TB)
SELECT
    c.who_region,
    a.antigen_code,
    ROUND(AVG(cov.coverage_pct), 1) AS avg_coverage,
    COUNT(DISTINCT CASE WHEN cov.coverage_pct < 80 THEN cov.country_code END) AS countries_below_80
FROM fact_coverage cov
JOIN dim_country c ON cov.country_code = c.country_code
JOIN dim_antigen a ON cov.antigen_code = a.antigen_code
WHERE a.antigen_code IN ('HepB3', 'BCG', 'DTPCV3', 'MCV1')
  AND cov.year_id >= 2020
GROUP BY c.who_region, a.antigen_code
ORDER BY c.who_region, avg_coverage;

-- Scenario 1: Low coverage regions for resource allocation (latest year, <70%)
SELECT
    c.who_region,
    c.country_name,
    a.antigen_description,
    cov.coverage_pct,
    cov.target_number,
    cov.doses_administered
FROM fact_coverage cov
JOIN dim_country c ON cov.country_code = c.country_code
JOIN dim_antigen a ON cov.antigen_code = a.antigen_code
WHERE cov.year_id = (SELECT MAX(year_id) FROM fact_coverage)
  AND cov.antigen_code IN ('DTPCV3', 'MCV1', 'POL3')
  AND cov.coverage_pct < 70
ORDER BY cov.coverage_pct ASC
LIMIT 30;

-- Scenario 6: Progress toward 95% measles coverage by 2030
SELECT
    year_id,
    ROUND(AVG(coverage_pct), 1) AS global_avg_mcv1,
    COUNT(DISTINCT CASE WHEN coverage_pct >= 95 THEN country_code END) AS countries_at_95,
    COUNT(DISTINCT country_code) AS total_countries,
    ROUND(
        COUNT(DISTINCT CASE WHEN coverage_pct >= 95 THEN country_code END) * 100.0 /
        COUNT(DISTINCT country_code), 1
    ) AS pct_countries_at_target
FROM fact_coverage
WHERE antigen_code = 'MCV1'
GROUP BY year_id
ORDER BY year_id;

-- Scenario 2 helper: Measles cases & coverage last 5–10 years
SELECT
    cov.year_id,
    ROUND(AVG(cov.coverage_pct), 1) AS avg_mcv1,
    SUM(rc.cases) AS total_measles_cases
FROM fact_coverage cov
LEFT JOIN fact_reported_cases rc
    ON cov.country_code = rc.country_code
   AND cov.year_id = rc.year_id
   AND rc.disease_code = 'MEASLES'
WHERE cov.antigen_code = 'MCV1'
  AND cov.year_id >= 2015
GROUP BY cov.year_id
ORDER BY cov.year_id;

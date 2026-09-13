# Vaccination Data Analysis and Visualization – Project Documentation

## 1. Project Overview

**Title:** Vaccination Data Analysis and Visualization  
**Domain:** Public Health & Epidemiology  
**Skills:** Python (cleaning + EDA), SQL (normalized database), Power BI (interactive dashboards)

**Objective:**  
Clean global vaccination and disease surveillance data, store it in a normalized relational database, perform exploratory analysis, and produce interactive Power BI dashboards that support public-health decision making (resource allocation, campaign evaluation, policy recommendations).

## 2. Data Sources & Schema

The original Google Drive folder was not publicly downloadable without authentication.  
Equivalent public data from the **WHO Immunization Data Portal** (immunizationdata.who.int) was used to generate realistic sample datasets that **exactly match the column definitions** given in the project brief:

| Table | File | Key Columns |
|-------|------|-------------|
| Coverage | coverage_data.csv | Group, Code, Name, Year, Antigen, Antigen_description, Coverage_category, Target_number, Doses, Coverage |
| Incidence Rate | incidence_rate.csv | Group, Code, Name, Year, Disease, Disease_description, Denominator, Incidence_rate |
| Reported Cases | reported_cases.csv | Group, Code, Name, Year, Disease, Disease_description, Cases |
| Vaccine Introduction | vaccine_introduction.csv | ISO_3_Code, Country_Name, WHO_Region, Year, Description, Intro |
| Vaccine Schedule | vaccine_schedule.csv | ISO_3_Code, Country_Name, WHO_Region, Year, Vaccine_code, Schedule_rounds, Target_pop, Age_administered, … |

Sample data covers 20 countries across all 6 WHO regions, years 2010–2024, and the main antigens/diseases.

**To use real data:**  
Download the latest CSVs from https://immunizationdata.who.int/ and place them in `data/raw/`. The cleaning script will automatically pick them up.

## 3. Project Structure

```
Vaccination_Project/
├── data/
│   ├── raw/                 # Place original WHO CSVs here
│   ├── sample/              # Generated sample data (used by default)
│   └── cleaned/             # Output of the cleaning pipeline
├── python/
│   ├── 01_data_cleaning.py  # Missing-value handling, normalization
│   ├── 02_eda_analysis.py   # Answers easy/medium questions + charts
│   └── 03_load_to_sqlite.py # Builds the SQLite database
├── sql/
│   ├── 01_schema.sql        # Normalized star-schema (PostgreSQL style)
│   ├── 02_load_data.sql     # Load statements
│   ├── 03_analytical_queries.sql  # Ready-to-run answers to project questions
│   └── vaccination.db       # Fully populated SQLite database (after running loader)
├── powerbi/
│   └── PowerBI_Dashboard_Guide.md  # Connection, model, DAX, page layout
├── reports/                 # EDA charts & priority CSV outputs
├── docs/
│   └── Project_Documentation.md
├── notebooks/               # (optional) Jupyter notebooks
├── requirements.txt
└── README.md
```

## 4. Data Cleaning Process

Script: `python/01_data_cleaning.py`

- Standardized column names (spaces → underscores).
- Coerced numeric types; imputed Coverage from Doses/Target when possible.
- Clipped Coverage to [0, 100].
- Dropped rows missing critical keys (Code, Year, Antigen/Disease).
- Normalized antigen & disease codes to uppercase.
- Year stored as integer.

**Quality checks performed:** missing-value summary, year range, row counts after cleaning.

## 5. SQL Database Design

**Normalization:** Star schema  
- Dimension tables: `dim_country`, `dim_antigen`, `dim_disease`, `dim_year`, `dim_coverage_category`  
- Fact tables: `fact_coverage`, `fact_incidence`, `fact_reported_cases`, `fact_vaccine_introduction`, `fact_vaccine_schedule`  

**Integrity:** Primary keys, foreign keys, unique constraints on natural keys, CHECK constraints on coverage % and case counts.  

**Indexes:** Created on the most frequent join/filter columns (country + year, antigen, disease).  

The SQLite database `sql/vaccination.db` is produced by `03_load_to_sqlite.py` and is ready for Power BI or any SQL client.

## 6. Exploratory Data Analysis Highlights

Script: `python/02_eda_analysis.py` produces:

- Correlation between MCV1 coverage and measles incidence (negative correlation expected).
- Dose drop-off rates (DTPCV1→DTPCV3, MCV1→MCV2).
- Regional coverage disparities.
- Countries with high coverage yet elevated incidence (outliers for investigation).
- Low-coverage priority list for resource allocation (Scenario 1).
- Coverage trend lines 2010–2024.

Charts and CSV outputs are saved under `reports/`.

## 7. Power BI Deliverable

Because Power BI Desktop files (`.pbix`) are binary and platform-specific, a complete **implementation guide** is provided in `powerbi/PowerBI_Dashboard_Guide.md`. It includes:

- Connection steps
- Star-schema relationships
- Ready-to-paste DAX measures
- Five recommended dashboard pages mapped to the project questions and scenarios

## 8. How to Reproduce

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Clean data
python python/01_data_cleaning.py

# 3. Run EDA (generates charts in reports/)
python python/02_eda_analysis.py

# 4. Build SQLite database
python python/03_load_to_sqlite.py

# 5. Open sql/vaccination.db in any SQL client or connect Power BI to it
```

## 9. Limitations & Notes on Missing Variables

Several “Easy” questions (gender differences, education level, urban/rural, population density, seasonality) **cannot be answered** with the five tables supplied in the brief; those dimensions are not present in the WHO coverage/incidence extracts.  

The project focuses on the dimensions that **are** available (country, region, year, antigen, disease, introduction status, schedule) and clearly documents which questions are fully answerable.

## 10. Evaluation Mapping

| Evaluation Criterion              | How it is met                                      |
|-----------------------------------|----------------------------------------------------|
| Data Cleaning Process             | `01_data_cleaning.py` + quality summary            |
| SQL Database Quality              | Normalized schema, PKs/FKs, indexes, populated DB  |
| Quality of Power BI Visualizations| Detailed guide with DAX + page layouts             |
| Insights and Actionability        | EDA answers + analytical SQL + scenario queries    |

---
*Generated for the Vaccination Data Analysis and Visualization project.*

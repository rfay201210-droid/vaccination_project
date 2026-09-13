# Short Project Report  
## Vaccination Data Analysis and Visualization

**Domain:** Public Health & Epidemiology  
**Stack:** Python • SQL (SQLite) • Streamlit • Power BI (guide)  
**Period covered by data:** 2010–2024  

---

### 1. Objective

Analyse global vaccination coverage, disease incidence and reported cases to:

- Quantify the link between coverage and disease outcomes  
- Identify multi-dose drop-off and regional disparities  
- Prioritise low-coverage areas for resource allocation  
- Track progress toward the 95 % measles (MCV1) target by 2030  
- Deliver interactive tools (Streamlit dashboard + Power BI guide) for decision makers  

---

### 2. Data & Pipeline

Five tables aligned with the WHO Immunization Data Portal schemas were used:

| Table | Role |
|-------|------|
| Coverage | % coverage, doses, targets by country–year–antigen |
| Incidence Rate | Disease incidence rates |
| Reported Cases | Absolute case counts |
| Vaccine Introduction | Yearly introduction status |
| Vaccine Schedule | Dose rounds, target populations, ages |

**Pipeline**

1. Cleaning & normalisation (`python/01_data_cleaning.py`)  
2. Exploratory analysis + 18+ charts (`python/02_eda_analysis.py` + Jupyter notebook)  
3. Star-schema SQLite database (`python/03_load_to_sqlite.py` → `sql/vaccination.db`)  
4. Interactive Streamlit app (`app.py`)  
5. Power BI connection & DAX guide (`powerbi/`)  

---

### 3. Key Findings

| Question / Scenario | Main insight |
|---------------------|--------------|
| Coverage ↔ incidence | Negative correlation between MCV1 coverage and measles incidence |
| Dose drop-off | Substantial MCV1 → MCV2 drop-off (~30 % on average in sample) |
| Regional view | Differences across WHO regions; traditional antigens generally higher than newer / second-dose antigens |
| High coverage + high incidence | A set of outliers still show elevated measles incidence despite ≥80 % MCV1 – warrants investigation |
| Resource allocation | Ranked list of lowest country–antigen pairs available for targeting |
| 95 % measles target | Average coverage is high; share of countries already ≥95 % still needs growth toward 2030 |

---

### 4. Deliverables

- **Streamlit app** – filters (year, region, antigen, disease), KPIs, five analysis tabs, CSV download  
- **Jupyter EDA notebook** – full template-style analysis with ≥18 charts and business-impact commentary  
- **SQLite database** – normalised dimensions + facts, ready for Power BI or any SQL client  
- **SQL analytics file** – ready-to-run queries answering the project questions  
- **Power BI guide** – star-schema relationships, DAX measures, recommended dashboard pages  
- **Documentation & README** – local run + Streamlit Community Cloud deployment steps  

---

### 5. Recommendations

1. Prioritise the lowest-coverage country–antigen combinations for campaigns and supply.  
2. Intensify second-dose measles (MCV2) strategies to reduce drop-out.  
3. Investigate high-coverage / high-incidence outliers for data quality or immunity gaps.  
4. Use the dual-axis MCV1 tracker to set intermediate milestones toward 2030.  
5. Keep the SQLite database as the single source of truth for BI tools.  

---

### 6. How to Run / Deploy

```bash
pip install -r requirements.txt
streamlit run app.py                  # interactive dashboard
# or open notebooks/Vaccination_EDA_Capstone.ipynb
```

**Streamlit Community Cloud:** push repo to GitHub → share.streamlit.io → select `app.py`.

---

*Report generated for the Vaccination Data Analysis and Visualization project.*

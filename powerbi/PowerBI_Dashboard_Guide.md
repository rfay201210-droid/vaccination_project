# Power BI Dashboard Guide – Vaccination Data Analysis

## 1. Connect to the Database

1. Open Power BI Desktop.
2. **Get Data → More → Database → SQLite** (or PostgreSQL if you migrated the schema).
   - Alternatively: **Get Data → Text/CSV** and load the cleaned CSVs from `data/cleaned/`.
3. Select `sql/vaccination.db`.
4. Load these tables / views:
   - `dim_country`, `dim_antigen`, `dim_disease`, `dim_year`
   - `fact_coverage`, `fact_incidence`, `fact_reported_cases`
   - `fact_vaccine_introduction`, `fact_vaccine_schedule`

## 2. Data Model (Star Schema)

Create relationships:

| From (Fact)              | To (Dim)          | Key                |
|--------------------------|-------------------|--------------------|
| fact_coverage            | dim_country       | country_code       |
| fact_coverage            | dim_year          | year_id            |
| fact_coverage            | dim_antigen       | antigen_code       |
| fact_coverage            | dim_coverage_category | coverage_category |
| fact_incidence           | dim_country       | country_code       |
| fact_incidence           | dim_year          | year_id            |
| fact_incidence           | dim_disease       | disease_code       |
| fact_reported_cases      | dim_country       | country_code       |
| fact_reported_cases      | dim_year          | year_id            |
| fact_reported_cases      | dim_disease       | disease_code       |
| fact_vaccine_introduction| dim_country       | country_code       |
| fact_vaccine_introduction| dim_year          | year_id            |

Mark `dim_year[year_id]` as a Date table (or create a proper Date table).

## 3. Recommended Measures (DAX)

```dax
Avg Coverage % = AVERAGE(fact_coverage[coverage_pct])

Total Doses = SUM(fact_coverage[doses_administered])

Total Target = SUM(fact_coverage[target_number])

Total Cases = SUM(fact_reported_cases[cases])

Avg Incidence = AVERAGE(fact_incidence[incidence_rate])

Countries Below 80% Coverage = 
CALCULATE(
    DISTINCTCOUNT(fact_coverage[country_code]),
    fact_coverage[coverage_pct] < 80
)

% Countries at 95% MCV1 = 
VAR _at95 = CALCULATE(
    DISTINCTCOUNT(fact_coverage[country_code]),
    fact_coverage[antigen_code] = "MCV1",
    fact_coverage[coverage_pct] >= 95
)
VAR _total = CALCULATE(
    DISTINCTCOUNT(fact_coverage[country_code]),
    fact_coverage[antigen_code] = "MCV1"
)
RETURN DIVIDE(_at95, _total)
```

## 4. Dashboard Pages

### Page 1 – Executive Overview (KPIs)
- KPI cards: Global Avg DTPCV3, MCV1, POL3 coverage (latest year)
- KPI: % countries ≥ 95% MCV1
- KPI: Total reported measles cases (latest year)
- Trend line: Coverage of key antigens 2010–2024
- Map: Coverage by country (choropleth)

### Page 2 – Coverage Deep Dive
- Slicers: Year, WHO Region, Antigen, Coverage Category
- Bar chart: Coverage by WHO Region
- Line chart: Dose drop-off (DTPCV1 vs DTPCV3, MCV1 vs MCV2)
- Table: Lowest coverage countries (resource allocation)

### Page 3 – Disease Impact
- Scatter plot: MCV1 Coverage vs Measles Incidence (answer Q1/Q9)
- Clustered bar: Cases before/after vaccine introduction
- Heatmap / matrix: Incidence by disease × region
- Line: Measles cases & coverage over time (campaign evaluation)

### Page 4 – Vaccine Introduction & Schedule
- Timeline / bar: Year of introduction by vaccine & region
- Matrix: Schedule rounds by country
- Gap analysis: High-priority antigens (HepB3, BCG) below target

### Page 5 – Scenario / Actionable Insights
- Low-coverage priority list (Scenario 1)
- Progress to 95% measles target by 2030 (Scenario 6)
- Filterable country drill-through

## 5. Best Practices Applied
- Star schema for performance
- Consistent color palette (WHO regional colors recommended)
- Tooltips with extra context (target number, doses)
- Bookmarks for “before/after campaign” views
- Mobile layout optimized for key KPIs

## 6. Sample Visual Mapping to Project Questions

| Question | Visual |
|----------|--------|
| Coverage vs incidence correlation | Scatter + trend line |
| 1st → subsequent dose drop-off | Dual line / clustered column |
| High incidence despite high coverage | Scatter filtered + table of outliers |
| Low coverage for resource allocation | Ranked table + map |
| Progress to 95% measles | KPI + line chart with target reference line |
| Introduction timeline disparities | Gantt-style or clustered bar by region |

Export the finished `.pbix` file to the `powerbi/` folder of this project when complete.

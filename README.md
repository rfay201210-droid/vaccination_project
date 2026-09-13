# 💉 Global Vaccination Data Analysis & Visualization

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Interactive **Streamlit** dashboard + full data pipeline (Python cleaning, normalized SQL database, Power BI guide) for global vaccination coverage, disease incidence and public-health decision support.

**Live demo (after you deploy):** replace this URL with your Streamlit Community Cloud link.

---

## ✨ Features

- **Interactive filters**: Year range, WHO Region, Antigens, Diseases
- **KPI cards**: Latest MCV1 / DTPCV3 coverage, measles cases, progress to 95 % target
- **Coverage trends** over time and by country
- **Coverage vs Incidence** scatter with OLS trendline + outlier table
- **Regional comparison** and **1st → subsequent dose drop-off**
- **Vaccine introduction timelines** and **resource-allocation** scenario (low coverage)
- **Progress tracker** toward 95 % measles coverage by 2030
- **Data explorer** with CSV download
- Backend: cleaned CSVs + fully populated SQLite star-schema database

---

## 🚀 Quick Start (Local)

```bash
git clone https://github.com/<your-username>/Vaccination_Project.git
cd Vaccination_Project

python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt

streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

---

## ☁️ Deploy to Streamlit Community Cloud (Free)

1. Push this repository to **GitHub** (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**.
4. Select the repository, branch (`main`), and main file path: **`app.py`**.
5. Click **Deploy**.

Streamlit Cloud will install `requirements.txt` and run the app.  
The sample data and SQLite database are already included, so no extra secrets are required.

### Optional: custom subdomain
After the first deploy you can set a friendly URL such as `yourname-vaccination-insights.streamlit.app`.

---

## 📁 Project Structure

```
Vaccination_Project/
├── app.py                      # ← Streamlit entry point (deploy this)
├── requirements.txt
├── .streamlit/config.toml
├── .gitignore
├── README.md
├── data/
│   ├── sample/                 # Original sample CSVs (WHO schema)
│   └── cleaned/                # Cleaned data used by the app
├── python/
│   ├── 01_data_cleaning.py
│   ├── 02_eda_analysis.py
│   └── 03_load_to_sqlite.py
├── sql/
│   ├── 01_schema.sql
│   ├── 02_load_data.sql
│   ├── 03_analytical_queries.sql
│   └── vaccination.db          # Ready-to-query SQLite DB
├── powerbi/
│   └── PowerBI_Dashboard_Guide.md
├── reports/                    # Static charts from offline EDA
└── docs/
    └── Project_Documentation.md
```

---

## 🔄 Re-running the Offline Pipeline

If you update the raw data:

```bash
python python/01_data_cleaning.py
python python/02_eda_analysis.py
python python/03_load_to_sqlite.py   # rebuilds sql/vaccination.db
```

Then refresh the Streamlit app (or re-deploy).

---

## 📊 Data Notes

- Sample data covers **20 countries**, all **6 WHO regions**, years **2010–2024**, main antigens and vaccine-preventable diseases.
- Column names match the original project brief (Coverage, Incidence Rate, Reported Cases, Vaccine Introduction, Vaccine Schedule).
- For production use, download official extracts from the [WHO Immunization Data Portal](https://immunizationdata.who.int/) into `data/raw/` and re-run the cleaning scripts.

Questions that require gender / education / urban-rural / density / seasonality dimensions are **not answerable** with the five supplied tables; all other project questions are implemented in the dashboard and in the SQL analytics file.

---

## 🛠️ Tech Stack

| Layer        | Tools                          |
|--------------|--------------------------------|
| Frontend     | Streamlit + Plotly             |
| Data         | pandas, numpy                  |
| Database     | SQLite (star schema)           |
| Offline EDA  | matplotlib, seaborn            |
| BI (optional)| Power BI (guide included)      |

---

## 📜 License

MIT – feel free to use for portfolios, coursework and further research.  
Always cite WHO when using official immunization data.

---

## 🙏 Acknowledgements

- WHO / UNICEF Immunization Data Portal schemas
- Streamlit Community Cloud for free hosting

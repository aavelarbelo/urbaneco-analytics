# UrbanEco Analytics
### Transforming energy data into real estate intelligence.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?style=flat-square)
![ODS](https://img.shields.io/badge/ODS-11%20Sustainable%20Cities-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-MVP%20In%20Progress-orange?style=flat-square)
[Project Blog](https://claude.ai/public/artifacts/b30040f2-dd88-45e5-96dc-5fc5606a1500)

---

UrbanEco Analytics is a Big Data and Data Engineering MVP that investigates 
how energy efficiency may influence real estate value in Portugal.

The project integrates public real estate price indicators, synthetic 
property-level data, a PostgreSQL analytical database, and a proprietary 
**Energy Value Index (EVI)** to support data-driven interpretation of 
property value potential — aligned with **UN SDG 11: Sustainable Cities 
and Communities**.

> **Academic context:** Final interdisciplinary project — Big Data 
> Post-Graduate Programme, ISEP, 2026.

---

## Table of Contents

1. [Business Problem](#1-business-problem)
2. [MVP Scope](#2-mvp-scope)
3. [Analytical Questions](#3-analytical-questions)
4. [Architecture](#4-architecture)
5. [Energy Value Index — EVI](#5-energy-value-index--evi)
6. [Data Sources](#6-data-sources)
7. [Tech Stack](#7-tech-stack)
8. [Project Structure](#8-project-structure)
9. [Setup & Execution](#9-setup--execution)
10. [Limitations & Next Steps](#10-limitations--next-steps)
11. [Team](#11-team)

---

## 1. Business Problem

Real estate decisions are commonly driven by location, size, price, and 
property type. Energy efficiency, however, is frequently treated as 
secondary information — despite its growing influence on long-term housing 
costs, renovation priorities, sustainability compliance, and perceived 
property value.

In Portugal, a property with energy class A can be worth 20–30% more than 
a comparable property with class D in the same municipality. Yet no 
accessible platform currently integrates energy certification data with 
structured real estate analytics.

**UrbanEco Analytics addresses this gap** by building an analytical 
pipeline that quantifies the relationship between energy efficiency and 
property value potential.

---

## 2. MVP Scope

To ensure feasibility and analytical depth, the MVP focuses on Porto as the main geographical reference, using real scraped data from Bonfim and a controlled synthetic expansion to nearby municipalities.

| Municipality | District | Focus |
|-------------|----------|-------|
| Porto | Porto | Main focus, with real CasaSafari data from Bonfim (250 records) |
| Vila Nova de Gaia | Porto | Synthetic expansion based on realistic market parameters |
| Matosinhos | Porto | Synthetic expansion based on realistic market parameters |

This scope allows the project to prioritise **real data quality, dimensional modelling, pipeline execution, and clear interpretation** before scaling to a national level.

---

## 3. Analytical Questions

The project is guided by four core analytical questions:

1. Which municipalities show the highest median property price per m²?
2. How are energy efficiency classes distributed across the selected 
   municipalities?
3. Which properties present the highest Energy Value Index (EVI)?
4. Which municipalities show the strongest potential for energy-driven 
   real estate value improvement?

---

## 4. Architecture

```text
Data Sources
│
├── INE / Pordata          →  median price per m² by municipality
├── ADENE / SCE            →  energy certification statistics (public)
└── CasaSafari             →  real Bonfim records + controlled synthetic expansion
│
▼
Ingestion Layer
│  scripts/01_extract_.py
▼
Raw Data  →  data/raw/
│
▼
Transformation Layer
│  scripts/02_transform_.py  (Pandas / PySpark)
▼
PostgreSQL  →  urbaneco_dw
│
├── dim_location
├── dim_property
├── dim_energy
└── fact_property_energy_value
│
▼
Analytics Layer
│  scripts/03_calculate_evi.py
▼
Energy Value Index (EVI)
│
▼
Dashboard  →  Streamlit + Plotly
│
▼
Demo Day  →  Pitch + Product + Impact
```

**MVP implementation:** Pandas + PostgreSQL + Streamlit.  
**Production evolution:** PySpark, dbt, automated pipeline, cloud deployment, incremental updates, data quality monitoring.

### Planned Architecture Evolution

After the MVP phase, the architecture is planned to evolve into a more complete Big Data and Data Engineering pipeline, following a layered data architecture:

- **Raw layer:** ingestion of original scraped and public datasets with minimal transformation.
- **Silver layer:** cleaned, validated, standardised, and enriched datasets ready for analytical modelling.
- **Gold layer:** business-ready tables, metrics, KPIs, and dashboard-oriented datasets.

The next phase will also include:

- **Kafka** for streaming/event-based ingestion scenarios.
- **PyDeequ** for automated data quality validation.
- **InfluxDB and Grafana** for monitoring pipeline metrics, execution behaviour, and data quality indicators.

This evolution is planned as a post-MVP phase, allowing the current MVP to first validate the analytical model, dataset structure, and core business logic before scaling the architecture.

---

## 5. Energy Value Index — EVI

The **Energy Value Index** is a proprietary analytical score designed to 
estimate a property's value improvement potential based on four dimensions.

### Formula
EVI = (energy_improvement_potential × 0.40)
+ (location_market_strength     × 0.30)
+ (price_opportunity            × 0.20)
+ (building_age_factor          × 0.10)

### Component definitions

| Component | Definition | Weight |
|---|---|---|
| `energy_improvement_potential` | `1 − energy_score` — higher for low-class properties | 40% |
| `location_market_strength` | `price_m2_municipality / max_price_m2_in_sample` | 30% |
| `price_opportunity` | `1 − (property_price_m2 / municipality_reference_price_m2)` | 20% |
| `building_age_factor` | Normalised age score — older buildings score higher | 10% |

### Energy class scoring

| Class | Score |
|-------|-------|
| A+    | 1.00  |
| A     | 0.90  |
| B     | 0.80  |
| B-    | 0.70  |
| C     | 0.55  |
| D     | 0.40  |
| E     | 0.25  |
| F     | 0.10  |

### Interpretation

- **EVI → 1:** High value improvement potential after energy rehabilitation.
- **EVI → 0:** Low opportunity (already efficient or already at market peak).

> **Transparency note:** The EVI is a documented analytical hypothesis at 
> MVP stage. Weights are defined as initial assumptions and will be refined 
> as real data is incorporated. The metric does not establish causality 
> between energy class and market price — it estimates relative potential 
> based on the four dimensions above.

---

## 6. Data Sources

| Source | Type | Usage |
|--------|------|-------|
| [INE](https://www.ine.pt) | Public | Median property price per m² by municipality |
| [Pordata](https://www.pordata.pt) | Public | Housing price time series by municipality |
| [ADENE / SCE](https://www.sce.pt) | Public | Energy certification statistics |
| CasaSafari | Real scraping + controlled synthetic expansion | 250 real records from Bonfim + ~9,750 synthetic records generated within realistic market parameters |
| CasaSafari scraping status | In progress | Scraping is currently ongoing, with a target dataset size of 10,000 records |

> **Data transparency:** Real price data from INE/Pordata is used for location-level indicators. CasaSafari provides real property-level data from Bonfim, while the remaining records are synthetically expanded within realistic market distributions. All synthetic data is clearly labelled throughout the pipeline and dashboard.

---
## 7. Dataset Schema

The MVP dataset follows a property-level schema defined by the team, combining real scraped records from Bonfim with synthetically expanded records for nearby municipalities. The variables below represent the expected structure used for ingestion, validation, modelling, and dashboard development.

| Variable | Type | Required | Notes |
|----------|------|----------|-------|
| PREÇO | Numeric / Decimal | Yes | Property listing price in euros |
| ÁREA UTIL | Numeric / Decimal | Yes | Usable/private area of the property in m² |
| ÁREA BRUTA | Numeric / Decimal | No | Gross property area in m², when available |
| FREGUESIA | Text | Yes | Parish where the property is located |
| CONCELHO | Text | Yes | Municipality, e.g., Porto, Vila Nova de Gaia, Matosinhos |
| CLASSE ENERGÉTICA | Text / Category | No | Energy certification class, when available |
| TIPOLOGIA | Text / Category | Yes | Property typology, e.g., T0, T1, T2, T3 |
| ANO DE CONSTRUÇÃO | Integer | No | Construction year of the property |
| ESTADO DA HABITAÇÃO | Text / Category | No | Housing condition, e.g., new, used, renovated |
| WC | Integer | No | Number of bathrooms |
| GARAGEM | Boolean / Category | No | Indicates whether the property has garage/parking |
| VARANDA | Boolean / Category | No | Indicates whether the property has a balcony |
| ANDAR | Text / Integer | No | Floor level of the property |
| GPS LATITUDE | Decimal | No | Latitude coordinate for geospatial analysis |
| GPS LONGITUDE | Decimal | No | Longitude coordinate for geospatial analysis |
| ELEVADOR | Boolean / Category | No | Indicates whether the building has an elevator |
| EQUIPAMENTO | Text / Category | No | Additional property equipment or amenities |
| PISCINA | Boolean / Category | No | Indicates whether the property has a swimming pool |
| MORADA | Text | No | Property address, when available |
| ARRUMOS | Boolean / Category | No | Indicates whether the property has storage space |
| TERRENO/JARDIM | Boolean / Category | No | Indicates whether the property has land or garden area |
| PISOS | Integer | No | Number of floors in the property/building |
| ESTADO ANUNCIO | Text / Category | No | Listing status, e.g., active, removed, duplicated |
| DATA PUBLICAÇÃO | Date | No | Publication date of the listing |
| URL | Text | Yes | Original listing URL for traceability |

## 8. Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Data transformation | Pandas (MVP) / PySpark (evolution) |
| Database | PostgreSQL 16 |
| Query layer | SQL |
| Dashboard | Streamlit + Plotly |
| Version control | GitHub |
| Environment | Docker (PostgreSQL container) |
| Documentation | Markdown + project blog |

---

## 9. Project Structure

```text
urbaneco-analytics/
│
├── dashboard/
│   └── streamlit_app.py          # interactive dashboard
│
├── data/
│   ├── raw/                      # original downloaded files (not versioned)
│   ├── processed/                # transformed data ready for analysis
│   └── synthetic/                # controlled synthetic property dataset
│
├── docs/
│   ├── architecture.md
│   ├── requirements.md
│   └── user_flow.md
│
├── notebooks/
│   └── 00_data_exploration.ipynb
│
├── scripts/
│   ├── 01_create_synthetic_properties.py
│   ├── 02_load_to_postgres.py
│   ├── 03_calculate_evi.py
│   └── 04_export_dashboard_data.py
│
├── sql/
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   └── 03_quality_checks.sql
│
├── src/
│   ├── config.py
│   ├── database.py
│   └── evi.py
│
├── .env.example                  # environment variable template (safe to commit)
├── .gitignore
├── README.md
├── requirements.txt
└── docker-compose.yml            # PostgreSQL container
```

---

## 10. Setup & Execution

### Prerequisites
- Python 3.11+
- Docker Desktop (recommended) or PostgreSQL 16 installed locally
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR-USERNAME/urbaneco-analytics.git
cd urbaneco-analytics
```

### 2. Create and activate virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your local PostgreSQL credentials
```

### 5. Start PostgreSQL via Docker
```bash
docker compose up -d
```

### 6. Run the pipeline
```bash
python scripts/01_create_synthetic_properties.py
python scripts/02_load_to_postgres.py
python scripts/03_calculate_evi.py
python scripts/04_export_dashboard_data.py
```

### 7. Launch the dashboard
```bash
streamlit run dashboard/streamlit_app.py
```

---

## 11. Limitations & Next Steps

### Current limitations
- Property-level data is synthetic; real transaction-level data is not 
  yet available.
- EVI weights are initial hypotheses, not calibrated against observed 
  market outcomes.
- Geographical scope is limited to 3 municipalities for the MVP.
- No causal claim is made between energy class and market price.

### Next steps
- Integrate real ADENE/SCE energy certification records.
- Expand to national scope using INE transaction data.
- Calibrate EVI weights using regression analysis on real data.
- Add predictive ML layer for value estimation.
- Automate pipeline with scheduling and incremental updates.
- Deploy Streamlit dashboard publicly.
- Integrate with real estate portal APIs (pending approval).

---

## 12. Team

| Team Member | Main Responsibility |
|------------|---------------------|
| Miguel Teixeira | Web scraping and data collection |
| Pedro Sousa| Testing and validation |
| Luís Simões| Metrics and analytical indicators |
| Tiago Lemos | Data quality |
| Mariana Reis| Database management and hosting |
| Andressa | Blog, architecture, and documentation |

---

*This project is developed for academic purposes as part of the final 
interdisciplinary challenge of the Big Data Post-Graduate Programme at 
ISEP. It does not constitute financial, real estate, or investment advice.*
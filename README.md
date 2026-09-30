# System Capacity & Care Load Analytics for Unaccompanied Children (UAC)

**Healthcare Systems Analytics & 7-Day Capacity Forecasting Engine**  
**Author**: [Pattan Abrar Malik](https://github.com/PattanAbrarMalik)  

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end data science and healthcare operations analytics platform monitoring care load dynamics, intake-to-discharge pipeline flows, and 7-day forward capacity forecasting for the **U.S. Department of Health and Human Services (HHS)** and **Customs & Border Protection (CBP)** Unaccompanied Alien Children (UAC) program.

---

## 📌 Executive Overview & Healthcare Context

From an operational and healthcare delivery perspective, the UAC program operates as a dynamic, high-stakes care pipeline:
1. **Intake & Custody (CBP)**: Initial apprehension, medical screening, and intake registration.
2. **Shelter & Care Facilities (HHS)**: Safe custody transfer into HHS facilities for medical evaluation, psychological wellness, and transitional care.
3. **Discharge & Placement**: Safe reunification with vetted family sponsors or legal guardians.

System volatility and influx surges make proactive capacity awareness essential. This platform provides operational intelligence and predictive time-series models to anticipate bed availability, identify facility bottlenecks, and optimize care readiness.

```
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────────┐
│   CBP Custody   │ ────> │   HHS Care Facilities  │ ────> │ Sponsor Discharge        │
│  (Intake/Triage)│       │ (Shelter/Medical Care) │       │ (Reunification/Placement)│
└─────────────────┘       └────────────────────────┘       └──────────────────────────┘
                                      │
                         [7-Day Forecast & Analytics]
```

---

## 📊 Key Findings & Empirical Results

| Metric / Dimension | Observation | Operational Impact |
| :--- | :--- | :--- |
| **Analyzed Timeline** | Jan 12, 2023 – Dec 21, 2025 (720 validated reporting days) | Complete multi-year observation covering both peak influx and stabilization phases. |
| **System Census Trajectory** | Peaked at **11,762 children** (Dec 2023) $\rightarrow$ **2,502 children** (Dec 2025) | Demonstrates successful post-surge stabilization and long-term census decline. |
| **Workload Distribution** | **HHS Facilities: 94.6%** \| **CBP Custody: 5.4%** | Overwhelming burden of sustained care sits with HHS shelter networks. |
| **Intake-Discharge Ratio** | Mean ratio: **0.97** (Balanced steady state) | Indicates sustainable outflow equilibrium during normalized operational periods. |
| **Forecasting Benchmark** | **Local Linear Trend MAE: 21.91 children** vs. **Naive Persistence MAE: 31.22 children** | **+29.82% error reduction** over baseline on blind holdout test set with zero lookahead bias. |

---

## 🚀 Live Streamlit Application Features

The interactive dashboard ([`streamlit_app.py`](streamlit_app.py)) provides decision-makers with real-time operational tools:

- **Executive KPI Cards**: Real-time counts of active HHS census, CBP custody, net daily intake, and rolling 7-day discharge velocity.
- **Pipeline Dynamics & Trajectory**: Comparative visualizations tracking HHS bed occupancy vs. CBP staging count across customized date windows.
- **Intake vs. Discharge Flow Balance**: Rolling balance charts identifying periods of net accumulation (potential bottleneck) vs. net decompression.
- **Backlog & Pressure Indices**: Rolling operational pressure indicators measuring system stress.
- **7-Day Horizon Predictive Engine**: Model-driven forecast projecting HHS care loads one week forward with confidence intervals.
- **Sensitivity & Scenario Modeling**: Interactive stress tests projecting bed utilization under synthetic surge conditions ($\pm 10\%$ to $\pm 30\%$).

---

## 🛠️ Repository Architecture

```text
care-capacity-forecasting-engine/
├── .streamlit/
│   └── config.toml          # Streamlit deployment theme and server configuration
├── .gitignore               # Excludes virtual environments, cache, and local artifacts
├── README.md                # Project documentation and reproduction instructions
├── requirements.txt         # Pinned production dependencies for Streamlit Cloud
├── streamlit_app.py         # Main interactive Streamlit analytics application
├── data/
│   └── HHS_Unaccompanied_Alien_Children_Program.csv  # Raw immutable historical records
├── docs/
│   └── VIVA_GUIDE.md        # Presentation walkthrough and examiner Q&A preparation
├── notebooks/
│   └── 01_research_workflow.ipynb # Complete research workflow with executed figures
├── scripts/
│   └── build_project.py     # Re-exporting plotting and visualization helpers
├── src/
│   ├── __init__.py
│   ├── analysis.py          # Summary metrics, correlations, and sensitivity logic
│   ├── data.py              # Ingestion, schema validation, and SHA-256 fingerprinting
│   ├── features.py          # Domain feature engineering and rolling pressure metrics
│   ├── models.py            # Chronological splitting, baseline, ML models, and scoring
│   └── visualization.py     # Clean publication chart generators
└── tests/
    └── test_research.py     # Unit test suite verifying formulas, leakage, and data integrity
```

---

## ☁️ Deployment Guide (Streamlit Community Cloud)

This repository is optimized for zero-configuration deployment on **Streamlit Community Cloud**:

1. **Fork or Push** this repository to your GitHub account (`PattanAbrarMalik/care-capacity-forecasting-engine`).
2. Navigate to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **"New app"** and configure:
   * **Repository**: `PattanAbrarMalik/care-capacity-forecasting-engine`
   * **Branch**: `main`
   * **Main file path**: `streamlit_app.py`
4. Click **"Deploy!"**
5. Streamlit Cloud will automatically detect `requirements.txt`, install dependencies, and launch the live web application.

---

## 💻 Local Setup & Execution

### 1. Prerequisites & Virtual Environment
Ensure Python 3.11+ is installed. Clone the repository and configure the environment:

```powershell
# Clone the repository
git clone https://github.com/PattanAbrarMalik/care-capacity-forecasting-engine.git
cd care-capacity-forecasting-engine

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Application
```powershell
streamlit run streamlit_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your web browser.

---

## 🧪 Quality Assurance & Automated Testing

The codebase includes rigorous unit tests covering data schema validation, zero future lookahead leakage, and mathematical correctness:

```powershell
python -m unittest discover tests -v
```

**Test Coverage Highlights:**
- `test_source_audit_matches_delivered_file`: Validates dataset integrity and SHA-256 hash.
- `test_validation_rejects_duplicate_date_and_missing_count`: Rejects corrupted data inputs.
- `test_feature_values_cannot_see_future`: Enforces strict causal lag windows with no future leakage.
- `test_selection_and_reported_error_match_predictions`: Verifies model scoring and evaluation alignment.

---

## 📈 Methodology & Predictive Modeling

- **Temporal Chronological Split**:
  - **Training Set**: 2023-01-12 to 2024-12-31 (Initial pattern learning)
  - **Validation Set**: 2025-01-01 to 2025-06-30 (Hyperparameter selection)
  - **Test Set (Holdout)**: 2025-07-01 to 2025-12-21 (Out-of-sample evaluation)
- **Target Variable**: Active HHS care census 7 days ahead ($y_{t+7}$).
- **Evaluation Metrics**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Absolute Percentage Error (MAPE).
- **Leakage Prevention**: All features (moving averages, momentum indicators, backlog ratios) strictly use information available at or before observation time $t$.

---

## 👤 Author & Acknowledgments

- **Author**: Pattan Abrar Malik
- **Role**: Data Science & Healthcare Analytics Intern
- **Institution / Program**: Unified Mentor Data Science Internship
- **Data Source**: U.S. Department of Health and Human Services (HHS) & U.S. Customs and Border Protection (CBP) Public Datasets

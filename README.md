# System Capacity & Care Load Analytics for Unaccompanied Children (UAC)

**Unified Mentor Data Science & Healthcare Analytics Internship Submission**  
**Author**: Pattan Abrar Malik  

An end-to-end data science and healthcare capacity analytics platform for the U.S. Department of Health and Human Services (HHS) and Customs & Border Protection (CBP) Unaccompanied Alien Children (UAC) program.

---

## 🚀 Quick Start (Run Locally)

### 1. Prerequisites & Environment Setup
Clone the repository and install dependencies:
```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Launch the Streamlit Live Dashboard
```powershell
streamlit run streamlit_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 📦 Project Submission Deliverables

| Deliverable | Location | Description |
| :--- | :--- | :--- |
| **Streamlit Web Dashboard** | [`streamlit_app.py`](streamlit_app.py) | Interactive healthcare capacity dashboard with system load overview, CBP vs HHS comparison, net intake & backlog trends, KPI cards, and 7-day predictive forecasting. |
| **Research Paper / Report** | [`reports/Internship_Report.docx`](reports/Internship_Report.docx) | Formal academic and technical report covering problem statement, EDA, capacity metrics, baseline comparisons, and limitations. |
| **Executive Policy Briefing** | [`reports/Executive_Summary_Stakeholders.docx`](reports/Executive_Summary_Stakeholders.docx) ([MD](reports/Executive_Summary_Stakeholders.md)) | Strategic briefing for HHS ORR and CBP leadership highlighting capacity bottlenecks and early warning thresholds. |
| **Research Notebook** | [`notebooks/01_research_workflow.ipynb`](notebooks/01_research_workflow.ipynb) | 16 pre-executed code cells containing exploratory analysis, statistical tables, and model evaluation charts. |
| **Viva & Defense Guide** | [`docs/VIVA_GUIDE.md`](docs/VIVA_GUIDE.md) | Structured 7-minute demonstration sequence and answers to technical reviewer questions. |

---

## 📊 Measured Empirical Results

* **Valid Source Observations**: 720 reports from 2023-01-12 to 2025-12-21 (purging 450 blank records with verified SHA-256 fingerprint).
* **System Census Trajectory**: Peak load of **11,762 children** (Dec 2023) decreasing to **2,502 children** (Dec 2025).
* **Workload Allocation**: HHS shelter facilities consistently shoulder **94.6%** of active care burden; CBP custody accounts for **5.4%**.
* **Model Benchmark (7-Day Ahead Forecast)**:
  * **Selected Winner**: Local Linear Trend (Validation MAE: 20.08 children; Test MAE: **21.91 children**).
  * **Naive Persistence Baseline**: Test MAE of **31.22 children**.
  * **Skill Gain**: **+29.82% lower holdout MAE** over baseline with zero future data leakage.

---

## 📁 Repository Architecture

```text
care-capacity-forecasting-engine/
├── .gitignore               # Excludes virtual environments and local cache
├── README.md                # Project documentation and reproduction instructions
├── requirements.txt         # Core project dependencies (Streamlit, Plotly, Scikit-learn, etc.)
├── streamlit_app.py         # Main interactive Streamlit analytics application
├── data/
│   └── HHS_Unaccompanied_Alien_Children_Program.csv  # Raw immutable historical records
├── docs/
│   └── VIVA_GUIDE.md        # Presentation walkthrough and examiner Q&A preparation
├── notebooks/
│   └── 01_research_workflow.ipynb # Executed Jupyter notebook with findings and figures
├── reports/
│   ├── Executive_Summary_Stakeholders.docx  # Policy briefing for government stakeholders
│   ├── Executive_Summary_Stakeholders.md    # Markdown version of executive summary
│   ├── Internship_Report.docx               # Full academic internship report
│   └── figures/                             # Generated publication-quality figures
├── scripts/
│   └── build_project.py     # Re-exporting plotting and visualization helpers
├── src/
│   ├── __init__.py
│   ├── analysis.py          # Summary metrics, correlations, and sensitivity logic
│   ├── data.py              # Data ingestion, schema validation, and SHA-256 digests
│   ├── features.py          # Domain feature engineering and rolling pressure metrics
│   ├── models.py            # Chronological splitting, baseline, ML models, and scoring
│   └── visualization.py     # Matplotlib publication chart generators
└── tests/
    └── test_research.py     # Unit test suite verifying formulas, leakage, and data integrity
```

---

## 🧪 Automated Testing

Verify data integrity, feature formulas, and temporal leakage prevention:
```powershell
python -m unittest discover tests -v
```

---

## ☁️ 1-Click Deployment (Streamlit Community Cloud)

This repository is optimized for native deployment on **Streamlit Community Cloud**:
1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
2. Click **New app** and select:
   * **Repository**: `PattanAbrarMalik/care-capacity-forecasting-engine`
   * **Branch**: `main`
   * **Main file path**: `streamlit_app.py`
3. Click **Deploy!** — Streamlit will automatically read `requirements.txt` and launch your live application with a public sharing URL.


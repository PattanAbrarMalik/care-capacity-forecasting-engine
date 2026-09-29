# Executive Summary & Policy Briefing
## System Capacity & Care Load Analytics for the Unaccompanied Alien Children (UAC) Program
**Prepared for**: Department of Health and Human Services (HHS), Office of Refugee Resettlement (ORR), and CBP Leadership  
**Project Track**: Unified Mentor Data Science & Healthcare Analytics Internship  
**Author**: Harish V J  
**Date**: September 2026  

---

### Executive Overview

The federally mandated Unaccompanied Alien Children (UAC) Program constitutes a high-stakes, dynamic care pipeline. Minors apprehended by U.S. Customs and Border Protection (CBP) require prompt medical screening, quarantine, sheltering in licensed HHS facilities, and structured placement with vetted sponsors.

Historically, operational decision-making across this pipeline has suffered from fragmented daily reporting, leading to reactive responses during sudden border influxes. This project establishes an **auditable, policy-aligned healthcare capacity and care-load analytics framework** designed to provide continuous situational awareness, quantify pipeline bottlenecks, and deliver reliable 7-day predictive forecasting.

---

### Key Operational Findings

1. **Long-Term System Load Trajectory**:
   * Between January 2023 and December 2025, total reported care load peaked at **11,762 children** in December 2023.
   * Following operational interventions and seasonal shifts, active system census decreased to **2,502 children** by December 2025 (a **78.7% reduction** from peak levels).
   * **HHS facilities consistently shoulder 94.6% of active care burden**, while CBP custody accounts for an average of 5.4% (intake station buffer).

2. **Inflow vs. Outflow Imbalance (The Backlog Engine)**:
   * **Discharge Offset Ratio**: The aggregate ratio of sponsor discharges to incoming transfers is **0.96**, indicating that overall outflow closely tracked inflow across the multi-year timeline.
   * **Prolonged Strain Windows**: Despite long-term parity, localized surges created significant backlog accumulation. A standardized **"4-of-7 days positive net intake"** pressure rule identified key strain windows where inflow outpaced shelter discharge capacity, leading to temporary shelter saturation.

3. **Data Quality & Constraint Audit**:
   * Of 1,170 raw records, **450 completely blank records** were purged, yielding **720 valid daily observations** spanning 1,074 calendar days (67.0% calendar reporting coverage; 355 unobserved weekend/holiday dates).
   * **Logical Constraint Adherence**: Discharges never exceeded active HHS facility census (0 violations). While daily transfers exceeded same-day CBP snapshot custody on 40 occasions, domain analysis confirms this reflects high intra-day processing turnover rather than corrupted data.

---

### Predictive Forecasting & Model Performance

To transition HHS from reactive response to proactive capacity allocation, four forecasting architectures were tested on a strictly chronological holdout test set (99 exact 7-calendar-day target pairs):

| Candidate Model | Validation MAE (Children) | Test MAE (Children) | Test RMSE (Children) | Improvement vs. Persistence |
| :--- | :---: | :---: | :---: | :---: |
| **Local Linear Trend (Selected)** | **20.08** | **21.91** | **28.60** | **+29.82% lower error** |
| Random Forest Regressor | 27.99 | 29.56 | 36.42 | +5.32% |
| Ridge Regression (L2) | 28.16 | 30.14 | 36.98 | +3.46% |
| Naive Persistence Baseline | 29.41 | 31.22 | 39.55 | *Baseline (0%)* |

* **Methodological Insight**: The validation-selected **Local Linear Trend** reduced test Mean Absolute Error from **31.22 to 21.91 children**—a **29.82% error reduction** over naive persistence. Higher-complexity non-linear models suffered from sample size constraints and historical regime shifts.
* **Leakage Controls**: Zero future data leakage was verified through strict chronological boundaries ($Train < Validation < Test$) and boundary-crossing pair purging.

---

### Strategic Recommendations for Government Stakeholders

1. **Deploy Streamlit Centralized Decision-Support**:
   Operationalize the interactive Streamlit monitoring application (`streamlit_app.py`) across HHS ORR regional command centers for live visibility into active census, growth velocity, and inflow-outflow ratios.
2. **Automate Surge Early-Warning Thresholds**:
   Institute automated alerts when the 7-day rolling net flow remains positive for 4 or more consecutive reporting cycles, triggering pre-negotiated temporary shelter expansion contracts before facilities exceed 85% capacity.
3. **Formalize Sponsor Placement Acceleration Protocols**:
   When the Discharge Offset Ratio drops below 0.85 for 14 consecutive days, deploy surge background-check personnel to sponsor vetting units to accelerate safe reunifications and relieve facility pressure.
4. **Mandate Complete Calendar Telemetry**:
   Transition from irregular 5-day reporting to 7-day automated telemetry to eliminate the 355 unobserved calendar gaps, improving time-series model fidelity and multi-horizon planning accuracy.

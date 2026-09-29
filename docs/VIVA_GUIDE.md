# Internship presentation and viva guide

## A defensible project explanation

“My project studies aggregate care-load observations from the HHS UAC program. I built a reproducible pipeline that audits source quality, analyzes census and flow patterns, creates interpretable indicators, and compares four seven-day forecasting methods. The model is chosen using validation data and checked on a later test period. In this experiment, a local linear trend reduced test MAE from 31.22 to 21.91 children, a 29.82% improvement over persistence. The dashboard makes those results and their limits inspectable.”

Use this explanation only after running the project and understanding the implementation. Do not claim operational deployment, real-time ingestion, clinical prediction, or an internship outcome that did not occur.

## Suggested seven-minute demonstration

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:45 | Research overview | Problem, source, and what question the analysis answers |
| 0:45–1:30 | Source audit | 450 blank rows, 720 valid reports, 355 unobserved dates |
| 1:30–2:30 | Load and flow charts | Stocks versus flows, actual calendar spacing, clear units |
| 2:30–3:15 | Pressure sensitivity | Why 4-of-7 is a project convention and how thresholds change results |
| 3:15–4:45 | Forecast laboratory | Exact targets, chronological split, baseline comparison, model selection |
| 4:45–5:30 | Test chart and limitations | Errors in children; one holdout; no causal or capacity claim |
| 5:30–6:15 | Executed notebook and manifest | Shared code, reproducibility and source checksum |
| 6:15–7:00 | Explorer/API and conclusion | Working application, measurable result, realistic next steps |

## Likely questions

**Why is this more than a dashboard?**
It contains a validated data pipeline, explicit research question, feature engineering, competing models, leakage controls, held-out evaluation, sensitivity checks, and reproducible artifacts. The interface communicates the scientific work.

**What is the project’s significance?**
It turns irregular aggregate records into traceable evidence and tests predictive value against a baseline. The source audit prevents misleading daily-rate claims, and the model comparison demonstrates that complexity must improve measured performance.

**Why does the simple model win?**
It has the lowest validation MAE among the fixed candidates. The selected local trend also performs better than persistence in the later test period. This is an empirical result for the specified split, not a claim that local trends always beat machine learning.

**What does 29.82% mean?**
It is the reduction in holdout MAE: `(31.22 - 21.91) / 31.22 × 100`, using displayed rounded scores. It is not classification accuracy or a success probability.

**Why not randomly split rows?**
Random splitting would mix past and future regimes. The chronological split more closely represents forecasting and prevents future labels from entering training. Boundary-crossing pairs are also excluded.

**Is seven observations the same as seven days?**
No. Rolling metrics use observation windows because reporting is incomplete. Forecast targets use exact calendar-day matching. These conventions are explicitly separated.

**How are missing values handled?**
Fully blank source records are counted and removed. Invalid required values fail validation. Missing calendar dates stay unobserved; there is no automatic interpolation or zero fill.

**Why retain transfers greater than custody?**
A flow during a day can exceed an end-of-day stock because of turnover and timing. Such rows are review flags, not automatically invalid observations.

**Can this measure overcrowding?**
No. It has no available-bed or staffing denominator. It measures reported load and descriptive pressure proxies.

**Why does the composite stress rule flag zero high-score rows?**
Its four conditions do not co-occur at the chosen threshold in this dataset. That reveals a limitation of the rule; it does not prove absence of strain. A validated operational outcome is needed to design a useful alert.

**Is the forecast interval statistically calibrated?**
No. It is a descriptive range based on validation absolute errors. Temporal dependence and regime shifts prevent claiming 90% future coverage.

**What would you improve next?**
Confirm source timing definitions, acquire capacity and staffing data, perform rolling-origin evaluation across multiple regimes, assess missing-target bias, test forecast stability, and add operational monitoring only after validation.

## Eight-slide presentation outline

1. Title, research question and practical motivation.
2. Dataset and source audit: rows, coverage and limitations.
3. Pipeline architecture and reproducibility.
4. Load and flow EDA using `reports/figures/load_history.png`.
5. Feature definitions and pressure sensitivity.
6. Exact seven-day prediction and chronological evaluation.
7. Model comparison and held-out predictions using the supplied figures.
8. Contribution, limitations, demonstrated result and next steps.

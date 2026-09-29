# UAC Insight: Care Load Dynamics and Seven-Day Forecasting

**Data Science internship submission — Harish V J**

An auditable study of HHS UAC program observations, with a working research dashboard, chronological forecasting experiment, executed notebook, and editable report.

## What makes this a Data Science project?

The project answers a specific question: **How do reported care loads and flows evolve, and can an exact seven-day HHS-care prediction outperform persistence?**

It includes source validation and provenance, exploratory analysis, observation-aware feature engineering, sensitivity analysis, four forecasting candidates, temporal leakage protection, validation-based selection, held-out evaluation, and a reproducible evidence pipeline. The application presents the scientific work and lets a reviewer inspect the underlying data.

## Measured results from the supplied source

| Evidence | Result |
| --- | --- |
| Valid observations | 720, from 2023-01-12 to 2025-12-21 |
| Blank source records removed | 450 |
| Observed-date coverage | 66.98%; 355 unobserved dates |
| Latest / peak combined load | 2,502 / 11,762 |
| Validation-selected model | Local linear trend |
| Test MAE / persistence MAE | 21.91 / 31.22 children |
| Test MAE improvement | 29.82% on 99 exact seven-day target pairs |

The study is historical. The model result applies to the documented split; it is not universal accuracy or a present-day forecast. No capacity, staffing, or causal effect is inferred from this file.

## Start on Windows PowerShell

Install Python **3.11 or 3.12**. The submitted run used Python 3.12. Use a path to the extracted folder; do not run the commands inside the ZIP.

```powershell
cd "C:\path\to\UAC_Analytics"
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:8501**. Stop with Ctrl+C. No virtual-environment activation is required, so PowerShell execution-policy changes are unnecessary. If you have Python 3.11, replace `py -3.12` with `py -3.11`. If the port is busy, run `app.py --port 8502`.

On macOS/Linux: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python app.py`.

## What to open for evaluation

1. **`reports/Internship_Report.docx`** — editable report with the research question, source audit, generated figures, methods, results, and limitations.
2. **`notebooks/01_research_workflow.ipynb`** — 16 executed code cells with actual tables and figures.
3. **Dashboard** — research overview, flows and pressure, forecast laboratory, source audit, data explorer, and project guide.
4. **`docs/VIVA_GUIDE.md`** — demo sequence, presentation notes, and likely reviewer questions.
5. **`docs/CODE_WALKTHROUGH.md`** — module/function explanations and the frontend-to-backend request path.
6. **`reports/run_manifest.json`** — source checksum, package versions, and reproduction settings.

## Reproduce the evidence

```powershell
.venv\Scripts\python.exe scripts/build_project.py
.venv\Scripts\python.exe scripts/build_notebook.py
.venv\Scripts\python.exe scripts/build_report.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To open and rerun in JupyterLab:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.venv\Scripts\python.exe -m jupyter lab notebooks/01_research_workflow.ipynb
```

The builders always use the original CSV. A report built after manually changing the raw CSV requires that new source to pass validation. The supplied notebook is already executed and can be reviewed without running it.

## Project structure

| Location | Purpose |
| --- | --- |
| `src/data.py` | Read source, validate schema/counts/dates, compute fingerprints |
| `src/features.py` | Derive explanatory metrics and origin-safe predictors |
| `src/models.py` | Exact seven-day targets, train/validation/test splits, fixed candidates, scores |
| `src/analysis.py` | EDA, annual/monthly tables, rank associations, sensitivity, research bundle |
| `app.py` | Local HTTP server and REST routes; caches research by dataset content |
| `store.py` | Validated SQLite working copy and CRUD operations |
| `analytics.py` | Lightweight observation summaries for API filters |
| `web/` | HTML structure, CSS presentation, JavaScript API calls and interactive charts |
| `scripts/` | Rebuild tables, figures, executed notebook, and Word report |
| `reports/` | Submission report, figures, tables, results, and run manifest |
| `tests/` | Source, formula, leakage and API checks using disposable databases |

## Scientific design

**Target:** HHS care exactly seven calendar days after an origin. No report on the target date means the pair is omitted; no labels are interpolated.

**Candidates:** persistence, 14-observation calendar-time local trend, standardized ridge regression, and a random forest with fixed settings and seed 42. Learned regressors predict census change and add it to the origin census.

**Split:** 70/15/15 chronological boundaries on raw observations. Training labels must precede validation, and validation labels must precede test. Validation MAE chooses the model. The learned candidates are then refit on pre-test eligible pairs. Test MAE, RMSE, and bias are reported without using them to select the winner.

**Interpretation:** Local trend wins this experiment. A more complex model is not assumed to be better. Errors are in children, not percentage accuracy. The final forecast starts at the historical dataset cutoff. Its validation-error reference range is not a calibrated confidence interval.

**Limitations:** irregular reporting, exact-target selection bias, dependent overlapping forecast errors, one temporal holdout, unknown within-day measurement alignment, and no capacity denominator. The relative-stress composite flags zero high-score records here; that is a limitation of this rule, not proof of no operational strain.

## Dataset and working-copy behavior

The original CSV is preserved in `data/`. First launch seeds `data/observations.sqlite3`. Edits from Data Explorer update only that local copy and trigger recalculation. A fingerprint notice appears if the working data differs from the source. Reports and notebooks remain tied to the source, and the ZIP excludes the mutable database.

To restore source observations: stop the server, back up any wanted edits, delete `data/observations.sqlite3`, then restart. Deleting all observations through the API leaves the working dataset empty on restart; it does not silently reseed it.

## REST API

| Method | Route | Use |
| --- | --- | --- |
| GET | `/api/health` | Server health |
| GET | `/api/research` | Full EDA and modeling bundle |
| GET | `/api/observations?start=2025-01-01&end=2025-12-31` | Filtered records and summaries |
| GET | `/api/observations/{id}` | One stored record |
| POST | `/api/observations` | Create a working-copy observation; 201 |
| PUT | `/api/observations/{id}` | Replace all six record fields |
| DELETE | `/api/observations/{id}` | Delete a working-copy observation |

Example JSON for POST/PUT:

```json
{"date":"2026-01-05","cbp_intake":10,"cbp_custody":20,"transfers":8,"hhs_care":2500,"discharges":12}
```

Date must be valid ISO format and unique. Counts must be integers from 0 to 2,000,000,000. Invalid input returns 400, duplicate dates 409, and missing IDs 404. All SQL values are parameterized. This research application binds to localhost and has no authentication; it is not configured for public hosting.

## Submission checklist

- Read the report and understand the limitations before presenting.
- Run the tests and dashboard on your own computer.
- Walk through the notebook from source audit through model evaluation.
- Explain the validation winner and the 29.82% holdout MAE reduction precisely.
- Show the source checksum, reproducible commands, and one API operation.
- Add any institution-required cover page, supervisor details, or internship declaration yourself; none has been invented here.

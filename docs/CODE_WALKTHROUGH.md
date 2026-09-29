# Code walkthrough

## The complete flow

The source CSV enters `src/data.py`. Validated observations enter `src/features.py`. `src/analysis.py` produces descriptive tables, while `src/models.py` builds and evaluates forecast candidates. The notebook and report builder import these same modules. The local application reads a SQLite working copy, calls the same research pipeline, and sends JSON to the browser.

The flow for a browser edit is: HTML form → JavaScript `fetch` → Python request handler → validation → parameterized SQL → JSON response → recomputed analysis → refreshed charts. The original CSV is untouched.

## Data Science modules

### `src/data.py`

`read_source()` reads every source record as text so formatting is not lost prematurely. It counts wholly blank rows, maps the six source column names, parses the explicit date format, strips numeric separators, and calls validation. Its audit contains source coverage and a SHA-256 checksum.

`validate_frame()` selects required fields, enforces unique valid dates and whole non-negative counts, and sorts chronologically. It raises an error for malformed records. `fingerprint()` hashes canonical values, allowing dashboard edits to be detected without relying on database IDs.

### `src/features.py`

`derive()` produces load, net flow, growth, offset ratio, reporting intervals, full-window rolling averages, normalized volatility, and pressure indicators. Relative historical thresholds use a shift before the expanding quantile, so current values do not define their own benchmark.

`model_features()` creates only current or lagged predictors. All rolling windows end at the origin. A 14-observation slope uses actual elapsed calendar days, so a reporting gap is not treated as a one-day interval.

### `src/models.py`

`prepare()` joins each origin to an actual report exactly seven days later. Missing target dates are excluded. It returns the feature frame, complete labeled pairs, and predictor names.

`estimator()` specifies fixed ridge and random-forest configurations. Ridge scaling lives inside a scikit-learn pipeline and therefore learns only from the fit partition.

`fit_predict()` handles both baselines and learned regressors. The local trend adds seven times the historical daily slope to the current census. Learned regressors predict the change from current census; outputs are floored at zero because negative counts are impossible.

`scores()` computes MAE, RMSE and signed bias. `run_experiment()` creates chronological boundaries, excludes crossing labels, selects by validation MAE, refits learned models using pre-test data, reports test performance, and produces a historical forward estimate. The test score never changes model choice.

The final error reference is the 90th percentile of absolute validation errors. It is not a statistically calibrated interval and is labeled accordingly.

### `src/analysis.py`

`summarize()` assembles EDA tables, coverage, annual/monthly summaries, Spearman rank correlations, and pressure-rule sensitivity. Stocks are averaged; reported flows are summed with observation counts. `research_bundle()` joins this evidence to the model experiment and source audit. JSON serialization converts missing numeric values to `null`.

## Backend

### `store.py`

`initialize()` creates tables and seeds the working database once. A separate initialization marker prevents an intentionally emptied database from reseeding on restart. `validate()` checks API fields before SQL. `create`, `get_row`, `list_rows`, `update`, and `delete` implement CRUD with placeholders rather than SQL string interpolation. Each connection is scoped to an operation.

### `app.py`

`Handler.route()` is the request-routing boundary. Its responsibilities correspond to middleware in a larger framework: parse requests, dispatch to the correct operation, catch expected validation errors, and return consistent JSON status codes. This small app has no hidden framework middleware.

`read_json()` bounds request size. `respond()` writes content type, length and status. `static()` serves only an allowlist of HTML, CSS and JavaScript files, preventing arbitrary file retrieval. `cached_research()` caches by the full dataset snapshot; editing any record changes the key and recalculates the analysis. A lock avoids concurrent duplicate model builds.

The server is local development/research infrastructure, not a production service. Authentication, audit history, shared multiuser permissions, public hosting, and operational monitoring are future extensions.

## Frontend

`index.html` provides semantic sections, filter controls, a data table, and a native dialog form. `styles.css` defines reusable cards, chart panels, navigation and responsive breakpoints. `app.js` manages the selected range and page state, calls the API, renders evidence, and handles CRUD.

The chart renderer plots every point on a calendar-time x-axis. It does not sample away peaks. Hovering a point reveals its date and value. Missing rolling indicators are skipped, and explanatory captions identify what connected lines mean. The explorer exposes a numeric table and CSV download.

## Reproducible artifacts

`build_project.py` reads the immutable source, computes results, writes CSV/JSON evidence and five matplotlib figures, and records a run manifest. `build_notebook.py` authors and executes 16 cells and stores real outputs in the notebook. `build_report.py` uses the generated results and figures to create the editable report.

This separation makes the code explainable: transformations belong in `src/`, presentation belongs in `web/`, and artifact generation belongs in `scripts/`.

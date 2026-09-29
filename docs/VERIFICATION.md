# Verification record

## Completed checks

- **11 automated tests passed** using disposable databases, covering source counts, invalid values, duplicate dates, zero denominators, full rolling windows, future-feature invariance, exact-date targets, chronological label boundaries, reported error calculations, dataset fingerprints, sparse-data handling, and live HTTP CRUD operations.
- `/api/research` returned the full source-matching bundle and an available model experiment.
- **16 notebook code cells executed without errors**, with real tables and five embedded figures.
- **Five standalone analysis figures** and CSV evidence tables generated from the raw source.
- JavaScript passed `node --check web/app.js`.
- The editable Word report rendered to **9 pages** for layout review.

## Scope and limits

Browser rendering and click-through automation were not completed in the build environment because a usable browser could not be downloaded. API behavior and JavaScript syntax were checked, but responsive layout and interactive controls should also be reviewed in Chrome or Edge on the submission computer. This limitation does not count as a passed browser test.

## Manual demo checks on your computer

1. Start the application and confirm the API-connected indicator.
2. Inspect all six navigation sections.
3. Filter to December 2025, then reset to all history.
4. Hover chart points and compare a value with the explorer.
5. Confirm the selected model, 99 test pairs, and 21.91 test MAE.
6. Download filtered records and inspect the CSV.
7. Add a temporary observation, edit it, and delete it. Verify the source-mismatch notice appears during edits and clears once original values are restored.
8. Test duplicate-date rejection and an invalid date range.
9. Narrow the browser window and review navigation, cards, chart labels and table scrolling.

Do not claim production deployment, multiuser authentication, or a calibrated forecast interval. Those features are outside this research submission.

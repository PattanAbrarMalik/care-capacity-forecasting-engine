"""A fixed, reproducible seven-day forecasting experiment.

Choose the model on validation MAE. Refit on information available before
the test period, then evaluate a chronological holdout exactly once. No
random row split, future scaling, or filled future labels are used.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .features import model_features
from .data import validate_frame

SEED = 42
NAMES = ['Persistence', 'Local linear trend', 'Ridge regression', 'Random forest']


def estimator(name):
    if name == 'Ridge regression':
        return make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    return RandomForestRegressor(n_estimators=160, max_depth=6,
                                 min_samples_leaf=8, random_state=SEED, n_jobs=1)


def prepare(frame):
    clean = validate_frame(frame)
    features = model_features(clean)
    columns = [column for column in features if column != 'date']
    # Exact-date join excludes targets on dates that were never reported.
    features['target_date'] = features.date + pd.Timedelta(days=7)
    targets = clean[['date', 'hhs_care']].rename(columns={'date': 'target_date', 'hhs_care': 'target'})
    pairs = features.merge(targets, on='target_date', how='left')
    return features, pairs.dropna(subset=[*columns, 'target']).reset_index(drop=True), columns


def fit_predict(name, training, evaluation, columns):
    if name == 'Persistence':
        return evaluation.hhs_care.to_numpy(float), None
    if name == 'Local linear trend':
        return np.maximum(0, evaluation.hhs_care.to_numpy() + 7 * evaluation.slope14_per_day.to_numpy()), None
    model = estimator(name)
    # Predict change, then add the latest observed census back to the estimate.
    model.fit(training[columns], training.target - training.hhs_care)
    predictions = np.maximum(0, evaluation.hhs_care.to_numpy() + model.predict(evaluation[columns]))
    return predictions, model


def scores(actual, predicted):
    error = np.asarray(predicted) - np.asarray(actual)
    return {'mae': round(float(np.abs(error).mean()), 2),
            'rmse': round(float(np.sqrt(np.mean(error ** 2))), 2),
            'bias': round(float(error.mean()), 2)}


def run_experiment(frame):
    clean = validate_frame(frame)
    if len(clean) < 160:
        return {'available': False, 'reason': 'At least 160 observations and 100 exact seven-day target pairs are required.'}
    features, pairs, columns = prepare(clean)
    if len(clean) < 160 or len(pairs) < 100:
        return {'available': False, 'reason': 'At least 160 observations and 100 exact seven-day target pairs are required.'}
    validation_start = clean.date.iloc[int(len(clean) * .70)]
    test_start = clean.date.iloc[int(len(clean) * .85)]
    train = pairs[pairs.target_date < validation_start]
    validation = pairs[(pairs.date >= validation_start) & (pairs.target_date < test_start)]
    before_test = pairs[pairs.target_date < test_start]
    test = pairs[pairs.date >= test_start]
    if min(len(train), len(validation), len(test)) < 10:
        return {'available': False, 'reason': 'Not enough exact-date pairs in each chronological partition.'}
    table, validation_predictions, test_predictions = [], {}, {}
    for name in NAMES:
        val_pred, _ = fit_predict(name, train, validation, columns)
        tst_pred, _ = fit_predict(name, before_test, test, columns)
        validation_predictions[name] = val_pred
        test_predictions[name] = tst_pred
        table.append({'model': name, 'validation': scores(validation.target, val_pred),
                      'test': scores(test.target, tst_pred)})
    # Validation decides the winner. Test metrics never influence selection.
    winner = min(table, key=lambda item: item['validation']['mae'])['model']
    last = features.dropna(subset=columns).tail(1)
    forecast, final_model = fit_predict(winner, pairs, last, columns)
    weights = []
    if winner == 'Random forest':
        weights = sorted([{'feature': feature, 'weight': round(float(weight), 5)}
                          for feature, weight in zip(columns, final_model.feature_importances_)],
                         key=lambda item: -item['weight'])
    elif winner == 'Ridge regression':
        weights = sorted([{'feature': feature, 'weight': round(float(weight), 3)}
                          for feature, weight in zip(columns, final_model[-1].coef_)],
                         key=lambda item: -abs(item['weight']))
    residual = np.abs(validation.target.to_numpy() - validation_predictions[winner])
    radius = float(np.quantile(residual, .90))
    baseline_mae = table[0]['test']['mae']
    selected_score = next(row for row in table if row['model'] == winner)
    prediction_rows = []
    for index, (_, row) in enumerate(test.iterrows()):
        prediction_rows.append({'origin': row.date.strftime('%Y-%m-%d'),
                                'date': row.target_date.strftime('%Y-%m-%d'),
                                'actual': int(row.target),
                                'selected': round(float(test_predictions[winner][index]), 2),
                                'persistence': round(float(test_predictions['Persistence'][index]), 2)})
    return {'available': True, 'horizon_days': 7, 'target': 'HHS care census', 'seed': SEED,
            'feature_names': columns, 'eligible_pairs': len(pairs),
            'split': {'validation_start': str(validation_start.date()), 'test_start': str(test_start.date()),
                      'train_pairs': len(train), 'validation_pairs': len(validation), 'test_pairs': len(test),
                      'train_last_target': str(train.target_date.max().date()),
                      'validation_last_target': str(validation.target_date.max().date()),
                      'test_first_origin': str(test.date.min().date())},
            'scores': table, 'selected_model': winner,
            'test_skill_vs_persistence_pct': round(100 * (baseline_mae - selected_score['test']['mae']) / baseline_mae, 2) if baseline_mae else None,
            'forecast': {'origin': str(last.date.iloc[0].date()),
                         'date': str(last.target_date.iloc[0].date()), 'estimate': round(float(forecast[0])),
                         'error_reference_low': round(max(0, float(forecast[0]) - radius)),
                         'error_reference_high': round(float(forecast[0]) + radius),
                         'error_radius': round(radius, 1)},
            'test_predictions': prediction_rows, 'feature_weights': weights,
            'limitations': ['Exact seven-day pairs exclude dates with missing future observations.',
                           'Nearby origins overlap, so errors are serially dependent.',
                           'One historical split is evidence for this regime, not deployment readiness.',
                           'The validation absolute-error range is descriptive, not a guaranteed prediction interval.']}

"""Explanatory indicators and forecasting features available at each origin."""
import numpy as np
from .data import validate_frame


def derive(frame):
    d = validate_frame(frame)
    d['total_load'] = d.cbp_custody + d.hhs_care
    d['net_flow'] = d.transfers - d.discharges
    d['gap_days'] = d.date.diff().dt.days
    d['load_change'] = d.total_load.diff()
    d['growth_pct'] = d.total_load.pct_change(fill_method=None) * 100
    d['growth_pct'] = d.growth_pct.replace([np.inf, -np.inf], np.nan)
    d['offset_ratio'] = d.discharges / d.transfers.replace(0, np.nan)
    for window in [7, 14]:
        # A headline rolling indicator needs the entire observation window.
        d[f'load_mean{window}'] = d.total_load.rolling(window).mean()
        d[f'net_mean{window}'] = d.net_flow.rolling(window).mean()
    d['volatility14'] = 100 * d.load_change.rolling(14).std() / d.load_mean14.replace(0, np.nan)
    d['pressure_4of7'] = (d.net_flow.rolling(7).sum() > 0) & ((d.net_flow > 0).rolling(7).sum() >= 4)
    d['transfer_review'] = d.transfers > d.cbp_custody
    d['discharge_review'] = d.discharges > d.hhs_care
    # Compare with PRIOR history only; today's large value cannot set its own threshold.
    d['prior_load_p90'] = d.total_load.shift(1).expanding(min_periods=60).quantile(.9)
    d['prior_volatility_p90'] = d.volatility14.shift(1).expanding(min_periods=60).quantile(.9)
    d['high_load'] = d.total_load > d.prior_load_p90
    d['high_volatility'] = d.volatility14 > d.prior_volatility_p90
    d['stress_eligible'] = d.prior_volatility_p90.notna() & d.prior_load_p90.notna()
    d['relative_stress_score'] = (d.high_load.astype(int) + d.high_volatility.astype(int)
                                  + (d.net_mean7 > 0).astype(int) + (d.offset_ratio < 1).astype(int))
    d['relative_stress_score'] = d.relative_stress_score.where(d.stress_eligible)
    return d


def model_features(frame):
    """Only same-date and earlier information is allowed in these predictors.

    The target is the EXACT seven-calendar-day-ahead HHS census. We retain
    origins only when that future date was actually observed (no imputation).
    Lag windows count reported observations; elapsed gaps are explicit features.
    """
    d = derive(frame)
    features = d[['date', 'hhs_care', 'cbp_custody', 'cbp_intake', 'transfers', 'discharges']].copy()
    features['hhs_lag1'] = d.hhs_care.shift(1)
    features['hhs_mean7'] = d.hhs_care.rolling(7).mean()
    features['hhs_mean14'] = d.hhs_care.rolling(14).mean()
    features['hhs_std14'] = d.hhs_care.rolling(14).std()
    features['net_mean7'] = d.net_mean7
    features['elapsed_gap'] = d.gap_days
    features['hhs_change_per_day'] = d.hhs_care.diff() / d.gap_days
    features['span14_days'] = (d.date - d.date.shift(13)).dt.days
    slopes = []
    for index in range(len(d)):
        window = d.iloc[max(0, index - 13):index + 1]
        if len(window) < 14:
            slopes.append(np.nan)
        else:
            days = (window.date - window.date.iloc[0]).dt.days.to_numpy()
            slopes.append(float(np.polyfit(days, window.hhs_care, 1)[0]))
    features['slope14_per_day'] = slopes
    return features

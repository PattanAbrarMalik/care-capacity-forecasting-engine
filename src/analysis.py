"""Evidence tables assembled once for the dashboard, notebook and report."""
import json
import numpy as np
import pandas as pd
from .data import read_source, fingerprint
from .features import derive
from .models import run_experiment


def records(frame):
    """Pandas writes missing values as JSON null, never invalid NaN tokens."""
    return json.loads(frame.to_json(orient='records', date_format='iso', date_unit='s'))


def summarize(frame):
    d = derive(frame)
    if d.empty:
        return {'observations': [], 'monthly': [], 'yearly': [], 'summary': {}, 'correlations': [], 'sensitivity': []}
    days = (d.date.max() - d.date.min()).days + 1
    monthly = d.set_index('date').resample('MS').agg(
        observations=('hhs_care', 'count'), hhs_mean=('hhs_care', 'mean'),
        cbp_mean=('cbp_custody', 'mean'), average_load=('total_load', 'mean'),
        reported_transfers=('transfers', 'sum'), reported_discharges=('discharges', 'sum'))
    monthly['coverage_pct'] = 100 * monthly.observations / monthly.index.days_in_month
    monthly = monthly.reset_index()
    yearly = d.groupby(d.date.dt.year).agg(observations=('date', 'count'),
        mean_load=('total_load', 'mean'), minimum_load=('total_load', 'min'),
        maximum_load=('total_load', 'max'), positive_flow_share=('net_flow', lambda x: 100 * (x > 0).mean())).reset_index()
    sensitivity = []
    for window, positives in [(5, 3), (7, 4), (7, 5)]:
        eligible = len(d) - window + 1
        flag = (d.net_flow.rolling(window).sum() > 0) & ((d.net_flow > 0).rolling(window).sum() >= positives)
        sensitivity.append({'rule': f'{positives} of {window}', 'flagged': int(flag.sum()),
                            'eligible': max(0, eligible),
                            'share_pct': round(100 * flag.sum() / eligible, 2) if eligible > 0 else None})
    cols = ['cbp_intake', 'cbp_custody', 'transfers', 'hhs_care', 'discharges', 'net_flow']
    # Spearman describes rank association; it is not evidence of causality.
    matrix = d[cols].corr(method='spearman')
    correlations = [{'x': x, 'y': y, 'value': round(float(matrix.loc[x, y]), 3) if pd.notna(matrix.loc[x,y]) else None}
                    for x in cols for y in cols]
    peak = d.loc[d.total_load.idxmax()]
    last = d.iloc[-1]
    return {'observations': records(d), 'monthly': records(monthly.round(3)),
            'yearly': records(yearly.round(3)), 'sensitivity': sensitivity,
            'correlations': correlations,
            'summary': {'count': len(d), 'calendar_days': days, 'unobserved_days': days - len(d),
                        'coverage_pct': round(100 * len(d) / days, 2),
                        'latest_date': str(last.date.date()), 'latest_load': int(last.total_load),
                        'peak_date': str(peak.date.date()), 'peak_load': int(peak.total_load),
                        'change_from_peak_pct': round(100 * (last.total_load / peak.total_load - 1), 2) if peak.total_load else None,
                        'transfer_review_count': int(d.transfer_review.sum()),
                        'discharge_review_count': int(d.discharge_review.sum()),
                        'gaps_gt_one': int((d.gap_days > 1).sum()),
                        'median_reporting_gap': float(d.gap_days.dropna().median()) if len(d)>1 else None,
                        'largest_gap': int(d.gap_days.max()) if len(d)>1 else 0,
                        'eligible_stress_rows': int(d.stress_eligible.sum()),
                        'high_relative_stress_rows': int((d.relative_stress_score >= 3).sum()),
                        'source_latest_age_days': (pd.Timestamp.now().normalize() - last.date).days}}


def research_bundle(frame=None):
    source, audit = read_source()
    frame = source if frame is None else frame
    result = summarize(frame)
    result['source_audit'] = audit
    result['working_fingerprint'] = fingerprint(frame)
    result['matches_source'] = result['working_fingerprint'] == audit['dataset_fingerprint']
    result['models'] = run_experiment(frame)
    return result

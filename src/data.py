"""Validate source records and preserve a reproducible provenance record."""
from hashlib import sha256
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/HHS_Unaccompanied_Alien_Children_Program.csv'
COUNTS = ['cbp_intake', 'cbp_custody', 'transfers', 'hhs_care', 'discharges']
MAPPING = dict(zip([
    'Date', 'Children apprehended and placed in CBP custody*',
    'Children in CBP custody', 'Children transferred out of CBP custody',
    'Children in HHS Care', 'Children discharged from HHS Care',
], ['date', *COUNTS]))


def validate_frame(frame):
    """Fail visibly on invalid records; never silently repair or drop data."""
    data = frame[['date', *COUNTS]].copy()
    data['date'] = pd.to_datetime(data['date'], errors='raise')
    if data.empty:
        return data
    if data['date'].isna().any() or data['date'].duplicated().any():
        raise ValueError('Dates must be present and unique.')
    for column in COUNTS:
        data[column] = pd.to_numeric(data[column], errors='raise')
        values = data[column]
        if values.isna().any() or (values < 0).any() or (values % 1 != 0).any():
            raise ValueError(f'{column} must contain non-negative whole counts.')
        data[column] = values.astype('int64')
    return data.sort_values('date').reset_index(drop=True)


def read_source(path=SOURCE):
    """Drop only wholly blank records; capture the original file checksum."""
    path = Path(path)
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    if not set(MAPPING).issubset(raw.columns):
        raise ValueError('CSV does not contain the required HHS columns.')
    blank = raw.apply(lambda column: column.str.strip().eq('')).all(axis=1)
    frame = raw.loc[~blank].rename(columns=MAPPING)
    frame['date'] = pd.to_datetime(frame['date'], format='%B %d, %Y', errors='raise')
    for column in COUNTS:
        frame[column] = frame[column].str.replace(',', '', regex=False).str.strip()
    frame = validate_frame(frame)
    audit = {'filename': path.name, 'sha256': sha256(path.read_bytes()).hexdigest(),
             'source_rows': len(raw), 'blank_rows_removed': int(blank.sum()),
             'valid_rows': len(frame), 'invalid_rows': 0, 'duplicate_dates': 0,
             'first_date': str(frame.date.min().date()), 'last_date': str(frame.date.max().date()),
             'dataset_fingerprint': fingerprint(frame)}
    return frame, audit


def fingerprint(frame):
    """Stable digest of canonical values, independent of record IDs or row order."""
    clean = validate_frame(frame)
    return sha256(clean.to_csv(index=False, date_format='%Y-%m-%d').encode()).hexdigest()

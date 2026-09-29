"""SQLite working copy and input validation. The supplied raw CSV is never edited."""

import csv
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "HHS_Unaccompanied_Alien_Children_Program.csv"
DB = ROOT / "data" / "observations.sqlite3"
COLUMNS = ("cbp_intake", "cbp_custody", "transfers", "hhs_care", "discharges")
RAW_COLUMNS = (
    "Children apprehended and placed in CBP custody*",
    "Children in CBP custody",
    "Children transferred out of CBP custody",
    "Children in HHS Care",
    "Children discharged from HHS Care",
)


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    return connection


def initialize():
    """Import valid rows once; future edits persist in the SQLite copy."""
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            cbp_intake INTEGER NOT NULL CHECK(cbp_intake >= 0),
            cbp_custody INTEGER NOT NULL CHECK(cbp_custody >= 0),
            transfers INTEGER NOT NULL CHECK(transfers >= 0),
            hhs_care INTEGER NOT NULL CHECK(hhs_care >= 0),
            discharges INTEGER NOT NULL CHECK(discharges >= 0)
        )""")
        # An empty database after deleting all rows remains empty on restart.
        db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY)")
        if db.execute("SELECT 1 FROM settings WHERE key='seeded'").fetchone():
            return
        with RAW.open(encoding="utf-8-sig", newline="") as source:
            for raw in csv.DictReader(source):
                if not raw["Date"].strip():
                    continue
                from datetime import datetime
                day = datetime.strptime(raw["Date"], "%B %d, %Y").date().isoformat()
                values = [int(raw[column].replace(",", "")) for column in RAW_COLUMNS]
                db.execute("""INSERT INTO observations
                    (date, cbp_intake, cbp_custody, transfers, hhs_care, discharges)
                    VALUES (?, ?, ?, ?, ?, ?)""", [day, *values])
        db.execute("INSERT INTO settings VALUES ('seeded')")


def validate(payload):
    """Reject missing, malformed, negative, fractional or unknown values."""
    if not isinstance(payload, dict) or set(payload) != {"date", *COLUMNS}:
        raise ValueError("Provide date and all five count fields, with no extra fields.")
    try:
        day = date.fromisoformat(payload["date"]).isoformat()
        if day != payload['date']:
            raise ValueError('Use YYYY-MM-DD.')
    except (ValueError, TypeError):
        raise ValueError("Date must be a valid YYYY-MM-DD date.") from None
    values = {}
    for key in COLUMNS:
        value = payload[key]
        if type(value) is not int or not 0 <= value <= 2_000_000_000:
            raise ValueError(f"{key} must be a whole number between 0 and 2,000,000,000.")
        values[key] = value
    return {"date": day, **values}


def list_rows(start=None, end=None):
    with connect() as db:
        sql = "SELECT * FROM observations WHERE 1=1"
        parameters = []
        if start:
            sql += " AND date >= ?"
            parameters.append(start)
        if end:
            sql += " AND date <= ?"
            parameters.append(end)
        return [dict(row) for row in db.execute(sql + " ORDER BY date", parameters)]


def get_row(row_id):
    with connect() as db:
        row = db.execute("SELECT * FROM observations WHERE id=?", (row_id,)).fetchone()
        return dict(row) if row else None


def create(payload):
    item = validate(payload)
    with connect() as db:
        cursor = db.execute("""INSERT INTO observations
            (date, cbp_intake, cbp_custody, transfers, hhs_care, discharges)
            VALUES (:date, :cbp_intake, :cbp_custody, :transfers, :hhs_care, :discharges)""", item)
        row = db.execute("SELECT * FROM observations WHERE id=?", (cursor.lastrowid,)).fetchone()
        return dict(row)


def update(row_id, payload):
    item = validate(payload)
    with connect() as db:
        cursor = db.execute("""UPDATE observations SET date=:date,
            cbp_intake=:cbp_intake, cbp_custody=:cbp_custody,
            transfers=:transfers, hhs_care=:hhs_care, discharges=:discharges
            WHERE id=:id""", {**item, "id": row_id})
        if not cursor.rowcount:
            return None
    return get_row(row_id)


def delete(row_id):
    with connect() as db:
        return bool(db.execute("DELETE FROM observations WHERE id=?", (row_id,)).rowcount)

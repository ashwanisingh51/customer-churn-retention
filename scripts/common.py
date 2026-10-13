"""Shared paths, dates and serialization. All currency amounts are synthetic USD."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AS_OF = pd.Timestamp("2026-08-31")
FIRST_MONTH = pd.Timestamp("2024-09-01")
SEED = 20260913
DATE_COLUMNS = {"signup_date", "subscription_start_date", "subscription_end_date",
                "last_activity_date", "churn_date", "snapshot_month", "as_of_date",
                "acquisition_cohort", "churn_month", "cohort_month", "month",
                "observation_date", "label_month"}

def ensure_dirs():
    for name in ["data/raw", "data/processed", "data/quarantine", "outputs/charts",
                 "outputs/sql_results", "outputs/model", "quicksight/manifests", "notebooks"]:
        (ROOT / name).mkdir(parents=True, exist_ok=True)

def write_csv(frame, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", float_format="%.8f", encoding="utf-8")

def write_json(value, path):
    def convert(obj):
        if isinstance(obj, np.generic): return obj.item()
        if isinstance(obj, (pd.Timestamp, Path)): return str(obj)
        raise TypeError(type(obj).__name__)
    Path(path).write_text(json.dumps(value, indent=2, default=convert, allow_nan=False) + "\n", encoding="utf-8")

def read_csv(name):
    frame = pd.read_csv(ROOT / "data/processed" / f"{name}.csv")
    for col in set(frame) & DATE_COLUMNS:
        frame[col] = pd.to_datetime(frame[col], errors="raise")
    return frame

def ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else None

def month_age(later, earlier):
    return (later.dt.year - earlier.dt.year) * 12 + later.dt.month - earlier.dt.month

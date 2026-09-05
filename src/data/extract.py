"""
extract.py
----------
Converts raw GTFS static files into an 8-feature vector CSV with delay labels.

Since SMART only provides static schedule data (no GTFS-RT actuals), we derive
proxy delay labels from schedule patterns. This is a known limitation documented
in docs/architecture.md.

Features:
    0  trip_start_offset      - seconds from midnight to trip start (normalized)
    1  stop_sequence_norm     - stop index normalized 0-1 across the trip
    2  scheduled_arrival_sec  - scheduled arrival in seconds from midnight (normalized)
    3  segment_duration       - scheduled seconds between this and previous stop (normalized)
    4  time_of_day_sin        - sin encoding of arrival hour (captures cyclical time)
    5  time_of_day_cos        - cos encoding of arrival hour
    6  day_of_week            - 0=Monday ... 6=Sunday (normalized 0-1)
    7  route_id_encoded       - integer-encoded route ID (normalized)

Label:
    0 = On Time       (proxy: off-peak + short segment)
    1 = Late          (proxy: peak hours or long segment)
    2 = Severely Late (proxy: peak hours + long segment + late in sequence)

Usage:
    python src/data/extract.py
    python src/data/extract.py --mode inference
"""

import argparse
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")
INFERENCE_DIR = os.path.join(ROOT, "data", "inference")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PEAK_HOURS = {7, 8, 9, 16, 17, 18}          # AM + PM rush
LATE_THRESHOLD_SEC = 120                      # 2 min  → Late
SEVERE_THRESHOLD_SEC = 600                    # 10 min → Severely Late
SECONDS_IN_DAY = 86400


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def time_to_seconds(t: str) -> int:
    """Convert HH:MM:SS string to seconds. GTFS allows hours > 24."""
    try:
        h, m, s = map(int, t.strip().split(":"))
        return h * 3600 + m * 60 + s
    except Exception:
        return 0


def load_gtfs(folder: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the four files we need from a GTFS folder."""
    def path(name):
        return os.path.join(folder, name)

    stop_times = pd.read_csv(path("stop_times.txt"), dtype=str)
    trips      = pd.read_csv(path("trips.txt"),      dtype=str)
    routes     = pd.read_csv(path("routes.txt"),     dtype=str)
    calendar   = pd.read_csv(path("calendar.txt"),   dtype=str)

    return stop_times, trips, routes, calendar


def build_proxy_label(row: pd.Series) -> int:
    """
    Assign a proxy delay label based on schedule heuristics.

    Rules (conservative and explainable):
      - Severely Late : peak hour AND stop is >60% through route AND long segment
      - Late          : peak hour OR long segment (top 25%)
      - On Time       : everything else
    """
    is_peak      = row["arrival_hour"] in PEAK_HOURS
    deep_in_trip = row["stop_sequence_norm"] > 0.6
    long_segment = row["is_long_segment"]

    if is_peak and deep_in_trip and long_segment:
        return 2   # Severely Late
    elif is_peak or long_segment:
        return 1   # Late
    else:
        return 0   # On Time


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def extract_features(gtfs_folder: str, route_encoder: LabelEncoder | None = None,
                     fit_encoder: bool = False) -> tuple[pd.DataFrame, LabelEncoder]:
    """
    Extract feature vectors from one GTFS folder.

    Returns:
        df             - DataFrame with 8 features + label
        route_encoder  - fitted LabelEncoder (reuse across months for consistency)
    """
    print(f"\n  Loading GTFS from: {gtfs_folder}")
    stop_times, trips, routes, calendar = load_gtfs(gtfs_folder)

    # ---- Merge trips → stop_times to get route_id per stop event ----------
    merged = stop_times.merge(trips[["trip_id", "route_id", "service_id"]], on="trip_id", how="left")

    # ---- Convert times to seconds -----------------------------------------
    merged["arrival_sec"]   = merged["arrival_time"].apply(time_to_seconds)
    merged["departure_sec"] = merged["departure_time"].apply(time_to_seconds)
    merged["stop_sequence"] = pd.to_numeric(merged["stop_sequence"], errors="coerce").fillna(0).astype(int)

    # ---- Trip start time (first stop of each trip) -------------------------
    trip_start = (
        merged.groupby("trip_id")["arrival_sec"]
        .min()
        .rename("trip_start_sec")
        .reset_index()
    )
    merged = merged.merge(trip_start, on="trip_id", how="left")

    # ---- Normalize stop sequence 0-1 within each trip ----------------------
    trip_len = (
        merged.groupby("trip_id")["stop_sequence"]
        .max()
        .rename("max_seq")
        .reset_index()
    )
    merged = merged.merge(trip_len, on="trip_id", how="left")
    merged["stop_sequence_norm"] = merged["stop_sequence"] / merged["max_seq"].clip(lower=1)

    # ---- Segment duration (time since previous stop) -----------------------
    merged = merged.sort_values(["trip_id", "stop_sequence"])
    merged["prev_arrival_sec"] = merged.groupby("trip_id")["arrival_sec"].shift(1)
    merged["segment_duration"] = (merged["arrival_sec"] - merged["prev_arrival_sec"]).fillna(0).clip(lower=0)

    # ---- Long segment flag (top 25% of segment durations) -----------------
    q75 = merged["segment_duration"].quantile(0.75)
    merged["is_long_segment"] = merged["segment_duration"] > q75

    # ---- Time of day -------------------------------------------------------
    merged["arrival_hour"] = (merged["arrival_sec"] % SECONDS_IN_DAY) // 3600
    merged["time_of_day_sin"] = np.sin(2 * np.pi * merged["arrival_sec"] / SECONDS_IN_DAY)
    merged["time_of_day_cos"] = np.cos(2 * np.pi * merged["arrival_sec"] / SECONDS_IN_DAY)

    # ---- Day of week from calendar (approximate: use service_id hash) ------
    # GTFS calendar has mon-sun columns; we use a hash as a proxy since we
    # don't have trip-level date instances here.
    merged["day_of_week"] = merged["service_id"].apply(lambda x: hash(x) % 7) / 6.0

    # ---- Route encoding ----------------------------------------------------
    if fit_encoder or route_encoder is None:
        route_encoder = LabelEncoder()
        route_encoder.fit(merged["route_id"].fillna("unknown"))

    merged["route_id_enc"] = route_encoder.transform(
        merged["route_id"].fillna("unknown").where(
            merged["route_id"].fillna("unknown").isin(route_encoder.classes_), "unknown"
        )
    )
    n_routes = len(route_encoder.classes_)

    # ---- Proxy labels ------------------------------------------------------
    merged["label"] = merged.apply(build_proxy_label, axis=1)

    # ---- Normalize continuous features to [0, 1] ---------------------------
    def norm(col, max_val):
        return (merged[col].clip(lower=0) / max_val).clip(0, 1)

    df = pd.DataFrame({
        "trip_start_offset":     norm("trip_start_sec",   SECONDS_IN_DAY),
        "stop_sequence_norm":    merged["stop_sequence_norm"],
        "scheduled_arrival_sec": norm("arrival_sec",      SECONDS_IN_DAY * 1.5),  # GTFS can exceed 24h
        "segment_duration":      norm("segment_duration", merged["segment_duration"].quantile(0.99).clip(1)),
        "time_of_day_sin":       (merged["time_of_day_sin"] + 1) / 2,             # remap [-1,1] → [0,1]
        "time_of_day_cos":       (merged["time_of_day_cos"] + 1) / 2,
        "day_of_week":           merged["day_of_week"],
        "route_id_encoded":      merged["route_id_enc"] / max(n_routes - 1, 1),
        "label":                 merged["label"],
    })

    # Drop rows with NaN (first stop of each trip has no segment duration)
    df = df.dropna().reset_index(drop=True)

    print(f"  Extracted {len(df):,} stop events")
    print(f"  Label distribution:\n{df['label'].value_counts().sort_index().to_string()}\n")

    return df, route_encoder


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(mode: str = "train"):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(INFERENCE_DIR, exist_ok=True)

    if mode == "train":
        # Expect data/raw/month1 and data/raw/month2
        month_folders = [
            os.path.join(RAW_DIR, "month1"),
            os.path.join(RAW_DIR, "month2"),
        ]

        all_dfs = []
        route_encoder = None

        for i, folder in enumerate(month_folders):
            if not os.path.exists(folder):
                print(f"[WARN] {folder} not found, skipping.")
                continue

            fit = (i == 0)  # Fit encoder on first month, reuse for second
            df, route_encoder = extract_features(folder, route_encoder, fit_encoder=fit)
            all_dfs.append(df)

        if not all_dfs:
            print("[ERROR] No data found. Place unzipped GTFS in data/raw/month1 and data/raw/month2")
            return

        combined = pd.concat(all_dfs, ignore_index=True)
        out_path = os.path.join(PROCESSED_DIR, "features.csv")
        combined.to_csv(out_path, index=False)
        print(f"[OK] Training features saved to {out_path} ({len(combined):,} rows)")

    elif mode == "inference":
        # Expect data/raw/inference
        folder = os.path.join(RAW_DIR, "inference")
        if not os.path.exists(folder):
            print(f"[ERROR] {folder} not found.")
            return

        # Re-fit encoder from training data if available
        train_path = os.path.join(PROCESSED_DIR, "features.csv")
        route_encoder = None
        if os.path.exists(train_path):
            train_df = pd.read_csv(train_path)
            # Encoder classes are implicit in the normalized values; for inference
            # we just fit fresh (acceptable for proxy labels)

        df, _ = extract_features(folder, route_encoder, fit_encoder=True)
        out_path = os.path.join(INFERENCE_DIR, "features.csv")
        df.to_csv(out_path, index=False)
        print(f"[OK] Inference features saved to {out_path} ({len(df):,} rows)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["train", "inference"], default="train",
                        help="train: process month1+month2 | inference: process inference month")
    args = parser.parse_args()
    main(args.mode)

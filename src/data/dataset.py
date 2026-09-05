"""
dataset.py
----------
PyTorch Dataset for the EdgeTransit feature CSV.
"""

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

FEATURE_COLS = [
    "trip_start_offset",
    "stop_sequence_norm",
    "scheduled_arrival_sec",
    "segment_duration",
    "time_of_day_sin",
    "time_of_day_cos",
    "day_of_week",
    "route_id_encoded",
]
N_FEATURES = len(FEATURE_COLS)   # 8
N_CLASSES  = 3                   # On-Time, Late, Severely Late


class TransitDataset(Dataset):
    def __init__(self, csv_path: str):
        df = pd.read_csv(csv_path)
        self.X = torch.tensor(df[FEATURE_COLS].values, dtype=torch.float32)
        self.y = torch.tensor(df["label"].values,      dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

    @property
    def class_weights(self) -> torch.Tensor:
        """Inverse-frequency weights for imbalanced labels."""
        counts = torch.bincount(self.y, minlength=N_CLASSES).float()
        weights = 1.0 / counts.clamp(min=1)
        return weights / weights.sum()

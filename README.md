# EdgeTransit — Embedded ML Transit Classifier

A 3-class transit delay classifier trained in PyTorch with CUDA mixed-precision and deployed on a STM32F446RE (Cortex-M4) microcontroller via INT8 quantization and CMSIS-NN kernels.

Classifies live transit stop events as **On-Time**, **Late**, or **Severely Late** by streaming feature vectors from a host PC over UART to the MCU for on-device inference.

---

## Stack

| Layer | Tools |
|---|---|
| Data | GTFS Static (SMART), Python, Pandas |
| Training | PyTorch, CUDA mixed-precision (AMP) |
| Quantization | ONNX, STM32CubeAI |
| Deployment | STM32F446RE, CMSIS-NN, C |
| Host pipeline | Python, pyserial |

---

## How It Works

```
GTFS Data (3 months)
       │
       ▼
Feature Extraction          8 features per stop event
       │
       ▼
MLP Training (PyTorch)      8 → 32 → 16 → 3  (~800 params)
CUDA mixed-precision
       │
       ▼
INT8 Quantization           ONNX → STM32CubeAI → C
       │
       ▼
STM32F446RE                 Inference under 128KB SRAM
       ▲
       │  UART (32 bytes)
       │
PC Python Script            Streams inference features at 20Hz
```

---

## Features

Each stop event is encoded as an 8-element float32 vector:

| # | Feature | Description |
|---|---|---|
| 0 | `trip_start_offset` | Seconds from midnight to trip origin (normalized) |
| 1 | `stop_sequence_norm` | Stop index normalized 0–1 across the trip |
| 2 | `scheduled_arrival_sec` | Scheduled arrival in seconds from midnight (normalized) |
| 3 | `segment_duration` | Scheduled travel time from previous stop (normalized) |
| 4 | `time_of_day_sin` | Sin encoding of arrival hour |
| 5 | `time_of_day_cos` | Cos encoding of arrival hour |
| 6 | `day_of_week` | 0 (Mon) – 1 (Sun), normalized |
| 7 | `route_id_encoded` | Integer-encoded route ID, normalized |

Sin/cos encoding is used for time-of-day to correctly handle the midnight boundary.

---

## Labels

| Class | Meaning | Threshold |
|---|---|---|
| 0 | On-Time | Off-peak, short segment |
| 1 | Late | Peak hour or long segment |
| 2 | Severely Late | Peak hour + long segment + deep in route |

---

## Dataset

- **Agency:** Suburban Mobility Authority for Regional Transit (SMART), Detroit MI
- **Source:** [MobilityDatabase](https://mobilitydatabase.org) — GTFS Static feeds
- **Training:** 2 months → 482,016 stop events
- **Inference:** 1 held-out month → 250,610 stop events

---

## Project Structure

```
EdgeTransit/
├── data/
│   ├── raw/
│   │   ├── month1/         # Training month 1 (unzipped GTFS)
│   │   ├── month2/         # Training month 2 (unzipped GTFS)
│   │   └── inference/      # Held-out month (unzipped GTFS)
│   ├── processed/          # features.csv (train)
│   └── inference/          # features.csv (inference)
│
├── src/
│   ├── data/
│   │   ├── extract.py      # GTFS → 8-feature vector + proxy labels
│   │   └── dataset.py      # PyTorch Dataset + class weights
│   ├── model/
│   │   ├── mlp.py          # MLP architecture
│   │   └── train.py        # Training loop with CUDA AMP
│   ├── inference/
│   │   ├── quantize.py     # INT8 quantization + ONNX export
│   │   └── validate.py     # PC float32 vs MCU INT8 accuracy comparison
│   └── uart/
│       └── stream.py       # UART feature streaming to STM32
│
└── README.md
```

---

## Quickstart

```bash
git clone https://github.com/yourusername/edgetransit
cd edgetransit
pip install torch pandas numpy scikit-learn onnx onnxruntime pyserial

# Extract features
python -m src.data.extract --mode train
python -m src.data.extract --mode inference

# Train
python -m src.model.train

# Quantize + export to ONNX
python -m src.inference.quantize

# Stream to STM32
python -m src.uart.stream --port /dev/ttyACM0
```

---

## Memory Footprint

| Component | Size |
|---|---|
| Model parameters | ~800 |
| Weights (Flash) | < 4KB |
| Activations (SRAM) | < 1KB |
| SRAM budget | 128KB |

---

## Status

- [x] GTFS feature extraction pipeline
- [ ] MLP training with CUDA mixed-precision
- [ ] INT8 quantization + ONNX export
- [ ] STM32CubeAI code generation
- [ ] UART streaming + MCU validation

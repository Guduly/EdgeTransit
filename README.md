# EdgeTransit — Embedded ML Transit Classifier

A 3-class transit delay classifier trained in PyTorch with CUDA mixed-precision and deployed on a STM32F446RE (Cortex-M4) microcontroller via a hand-written C++ inference engine.

Classifies transit stop events as **On-Time**, **Late**, or **Severely Late** by streaming feature vectors from a host PC over UART to the MCU for on-device inference.

---

## Results

| Metric | Value |
|---|---|
| Validation accuracy | 98.9% |
| Training samples | 482,016 stop events |
| MCU mean inference latency | 0.13ms |
| MCU max inference latency | 1ms |
| Flash usage | 18KB / 512KB |
| SRAM usage | 328 bytes / 128KB |
| PC vs MCU agreement | 100% (250,610 samples) |

---

## Stack

| Layer | Tools |
|---|---|
| Data | GTFS Static (SMART), Python, Pandas |
| Training | PyTorch, CUDA mixed-precision (AMP) |
| Export | Custom Python weight exporter → C++ headers |
| Inference | Hand-written C++ forward pass, STM32 HAL |
| Deployment | STM32F446RE Cortex-M4, arm-none-eabi-g++, OpenOCD |
| Host pipeline | Python, pyserial, CMake, Ninja |

---

## How It Works

```
GTFS Static Data (3 months, SMART Detroit)
         │
         ▼
Feature Extraction (extract.py)
8 features per stop event → 482K training rows
         │
         ▼
MLP Training (PyTorch + CUDA AMP)
Architecture: 8 → 32 → 16 → 3  (~800 parameters)
Validation accuracy: 98.9%
         │
         ▼
Weight Export (export.py)
Float32 weights → C++ header files
         │
         ▼
C++ Inference Engine (inference.cpp)
Hand-written forward pass using STM32 hardware FPU
18KB Flash, 328 bytes SRAM, 0.13ms mean latency
         │
         ▲  UART 115200 baud (32 bytes → 1 byte)
         │
PC Python Stream (stream.py)
Reads inference CSV, packs 8 floats as 32 bytes,
sends to MCU, logs predictions + latency
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

| Class | Meaning | Proxy Rule |
|---|---|---|
| 0 | On-Time | Off-peak + short segment |
| 1 | Late | Peak hour or long segment |
| 2 | Severely Late | Peak hour + long segment + deep in route |

> **Note:** Labels are proxy-derived from GTFS schedule heuristics since SMART does not publish archived GTFS-RT actuals. The pipeline is designed to accept real actuals — swapping in ground truth labels only requires updating `extract.py`.

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
│   │   ├── mlp.py          # MLP architecture (8→32→16→3)
│   │   └── train.py        # Training loop with CUDA AMP
│   ├── inference/
│   │   ├── export.py       # Float32 weight export to C++ headers
│   │   └── validate.py     # PC float32 vs MCU agreement check
│   ├── uart/
│   │   └── stream.py       # UART feature streaming + latency logging
│   └── stm32/
│       ├── Core/
│       │   ├── main.cpp        # UART receive loop + HAL init
│       │   ├── inference.cpp   # C++ MLP forward pass
│       │   └── inference.h     # predict() declaration
│       ├── weights/            # Exported float32 C++ headers
│       └── CMakeLists.txt      # CMake + Ninja build
│
└── logs/
    └── mcu_predictions.csv     # Streamed predictions + latency per sample
```

---

## Quickstart

```bash
git clone https://github.com/yourusername/edgetransit
cd edgetransit
pip install torch pandas numpy scikit-learn pyserial

# 1. Place unzipped GTFS folders in data/raw/month1, month2, inference/
# 2. Extract features
python -m src.data.extract --mode train
python -m src.data.extract --mode inference

# 3. Train
python -m src.model.train

# 4. Export weights to C++ headers
python -m src.inference.export

# 5. Build and flash STM32
cd src/stm32
cmake -B build -G Ninja
ninja -C build
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
        -c "program build/edgetransit.elf verify reset exit"

# 6. Stream inference data to MCU
cd ../..
python -m src.uart.stream --port /dev/ttyACM0 --limit 1000

# 7. Validate MCU vs PyTorch
python -m src.inference.validate
```

---

## Memory Footprint

```
arm-none-eabi-size build/edgetransit.elf
   text    data     bss     dec
  18432      20     308   18760
```

| Section | Size | Description |
|---|---|---|
| Flash (text) | 18KB | Code + model weights |
| SRAM (data+bss) | 328 bytes | HAL state + activation buffers |
| SRAM budget | 128KB | STM32F446RE total |

---

## Hardware

- **MCU:** STM32F446RE (Cortex-M4F, 180MHz, 512KB Flash, 128KB SRAM)
- **Board:** NUCLEO-F446RE
- **Interface:** USART2 via ST-Link USB (PA2=TX, PA3=RX)
- **Toolchain:** arm-none-eabi-gcc 16.2.0, OpenOCD, CMake, Ninja

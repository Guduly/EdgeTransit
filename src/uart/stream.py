import serial
import struct
import csv
import argparse
import pandas as pd
import time
import os

LABEL_MAP = {0: "On-Time", 1: "Late", 2: "Severely Late"}

def main():
    parser = argparse.ArgumentParser(description="Stream inference features over UART to MCU.")
    parser.add_argument("--port",    type=str,   default="/dev/ttyACM0")
    parser.add_argument("--baud",    type=int,   default=115200)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--limit",   type=int,   default=None)
    args = parser.parse_args()

    # Load inference features
    csv_path = "data/inference/features.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df          = pd.read_csv(csv_path)
    feature_cols = df.columns[:8].tolist()
    features_df  = df[feature_cols]

    if args.limit:
        features_df = features_df.head(args.limit)

    os.makedirs("logs", exist_ok=True)
    log_path = "logs/mcu_predictions.csv"

    # Open serial port
    ser = None
    if not args.dry_run:
        try:
            ser = serial.Serial(args.port, args.baud, timeout=2.0)
            time.sleep(2)
        except serial.SerialException as e:
            print(f"Failed to open {args.port}: {e}")
            return

    latencies = []

    with open(log_path, mode="w", newline="") as log_file:
        writer = csv.writer(log_file)
        writer.writerow(["index", "prediction", "label_string", "latency_ms", "timestamp"])

        print(f"Starting stream {'(DRY RUN)' if args.dry_run else ''}...")

        for index, row in features_df.iterrows():
            row_values = [float(x) for x in row]
            payload    = struct.pack("<8f", *row_values)

            if args.dry_run:
                time.sleep(0.001)
                prediction = index % 3
                elapsed_ms = 0
            else:
                ser.write(payload)
                ser.flush()

                # Read 5 bytes: 1 byte prediction + 4 bytes elapsed (uint32)
                response = ser.read(5)
                if len(response) == 5:
                    prediction = int.from_bytes(response[:1], byteorder="little")
                    elapsed_ms = struct.unpack("<I", response[1:5])[0]
                    latencies.append(elapsed_ms)
                else:
                    print(f"Warning: Timeout at index {index}")
                    continue

            label_string = LABEL_MAP.get(prediction, "Unknown")
            timestamp    = time.time()

            writer.writerow([index, prediction, label_string, elapsed_ms, timestamp])
            print(f"Idx: {index:6d} | {label_string:<15} | Latency: {elapsed_ms}ms")

    if ser:
        ser.close()

    # Print latency summary
    if latencies:
        import numpy as np
        print("\n=== Latency Summary ===")
        print(f"Min:    {np.min(latencies)}ms")
        print(f"Max:    {np.max(latencies)}ms")
        print(f"Mean:   {np.mean(latencies):.2f}ms")
        print(f"Median: {np.median(latencies):.2f}ms")
        print(f"Samples: {len(latencies)}")

    print("Streaming complete.")

if __name__ == "__main__":
    main()

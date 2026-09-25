import serial
import struct
import csv
import argparse
import pandas as pd
import time
import os

# Define feature columns (Replace placeholders with your exact 8 feature names if needed)
# FEATURE_COLS = ["feat1", "feat2", "feat3", "feat4", "feat5", "feat6", "feat7", "feat8"]
FEATURE_COLS = None 

LABEL_MAP = {0: "On-Time", 1: "Late", 2: "Severely Late"}

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Stream inference features over UART to MCU.")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port connection")
    parser.add_argument("--baud", type=int, default=115200, help="UART baud rate")
    parser.add_argument("--dry_run", action="store_true", help="Simulate execution without sending UART data")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of rows to process")
    args = parser.parse_args()

    # 1. Load data/inference/features.csv with pandas
    csv_path = "data/inference/features.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    
    # Select the 8 feature columns
    global FEATURE_COLS
    if FEATURE_COLS is None:
        FEATURE_COLS = df.columns[:8].tolist()
    
    features_df = df[FEATURE_COLS]

    # Apply limits if provided
    if args.limit is not None:
        features_df = features_df.head(args.limit)

    # Ensure output log directory exists
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/mcu_predictions.csv"

    # Open serial port if not a dry run
    ser = None
    if not args.dry_run:
        try:
            ser = serial.Serial(args.port, args.baud, timeout=2.0)
            time.sleep(2) # Allow MCU time to reset/initialize
        except serial.SerialException as e:
            print(f"Failed to open serial port {args.port}: {e}")
            return

    # Open log file to append predictions
    with open(log_path, mode="a", newline="") as log_file:
        writer = csv.writer(log_file)
        
        # Write header if file is empty
        if os.stat(log_path).st_size == 0:
            writer.writerow(["index", "prediction", "label_string", "timestamp"])

        print(f"Starting stream {'(DRY RUN)' if args.dry_run else ''}...")

        # 2. Loop over rows
        for index, row in features_df.iterrows():
            # Convert row to list of 8 floats and pack them
            row_values = [float(x) for x in row]
            payload = struct.pack("<8f", *row_values)

            prediction = 0
            if args.dry_run:
                # Simulate a dummy prediction response (e.g., alternating labels)
                time.sleep(0.05) 
                prediction = index % 3
            else:
                # Send data over serial
                ser.write(payload)
                ser.flush()
                
                # Read 1 byte back containing the prediction class integer
                response = ser.read(1)
                if len(response) == 1:
                    prediction = int.from_bytes(response, byteorder="big")
                else:
                    print(f"Warning: Timeout reading byte back at index {index}")
                    continue

            # Resolve label string description
            label_string = LABEL_MAP.get(prediction, "Unknown")
            timestamp = time.time()

            # 3. Log index, prediction, label string, timestamp
            writer.writerow([index, prediction, label_string, timestamp])
            print(f"Idx: {index} | Pred: {prediction} ({label_string})")

    if ser:
        ser.close()
    print("Streaming complete.")

if __name__ == "__main__":
    main()

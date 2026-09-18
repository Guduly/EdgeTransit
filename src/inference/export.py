import torch
import os
import numpy as np
from src.model.mlp import TransitMLP

OUT_DIR = "src/stm32/weights"

def write_header(name, arr, scale, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    upper = name.upper()
    path  = os.path.join(out_dir, f"{name}.h")

    with open(path, "w") as f:
        f.write(f"#pragma once\n")
        f.write(f"#include <stdint.h>\n\n")
        f.write(f"#define {upper}_SCALE {scale:.6f}f\n")

        # write shape defines
        if arr.ndim == 2:
            f.write(f"#define {upper}_ROWS {arr.shape[0]}\n")
            f.write(f"#define {upper}_COLS {arr.shape[1]}\n\n")
            f.write(f"static const int8_t {upper}[{arr.shape[0]}][{arr.shape[1]}] = {{\n")
            for row in arr:
                f.write("    {" + ", ".join(str(v) for v in row) + "},\n")
        else:
            f.write(f"#define {upper}_SIZE {arr.shape[0]}\n\n")
            f.write(f"static const int8_t {upper}[{arr.shape[0]}] = {{\n")
            f.write("    " + ", ".join(str(v) for v in arr) + "\n")

        f.write("};\n")

    print(f"[OK] wrote {path}")

def quantize(arr):
    scale    = np.max(np.abs(arr)) / 127.0
    int8_arr = np.clip(np.round(arr / scale), -128, 127).astype(np.int8)
    return int8_arr, scale

def export():
    model = TransitMLP()
    # Fixed the missing quotes in the path string
    model.load_state_dict(torch.load("src/model/checkpoints/best.pt", map_location="cpu"))
    model.eval()
    
    # Extract fc1, fc2, fc3 weights and biases
    # Assumes the layer names inside TransitMLP are fc1, fc2, and fc3
    layers = {
        "fc1_weight": model.fc1.weight.detach().numpy(),
        "fc1_bias": model.fc1.bias.detach().numpy(),
        "fc2_weight": model.fc2.weight.detach().numpy(),
        "fc2_bias": model.fc2.bias.detach().numpy(),
        "fc3_weight": model.fc3.weight.detach().numpy(),
        "fc3_bias": model.fc3.bias.detach().numpy(),
    }

    for name, tensor in layers.items(): 
        q, scale = quantize(tensor)
        write_header(name, q, scale, OUT_DIR)

if __name__ == "__main__":
    export()

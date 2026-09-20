import torch
import os
import numpy as np
from src.model.mlp import TransitMLP

OUT_DIR = "src/stm32/weights"

def write_header(name, arr, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    upper = name.upper()
    path  = os.path.join(out_dir, f"{name}.h")

    with open(path, "w") as f:
        f.write(f"#pragma once\n\n")
        if arr.ndim == 2:
            f.write(f"static const float {upper}[{arr.shape[0]}][{arr.shape[1]}] = {{\n")
            for row in arr:
                f.write("    {" + ", ".join(f"{v:.6f}f" for v in row) + "},\n")
        else:
            f.write(f"static const float {upper}[{arr.shape[0]}] = {{\n")
            f.write("    " + ", ".join(f"{v:.6f}f" for v in arr) + "\n")
        f.write("};\n")

    print(f"[OK] wrote {path}")

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
        write_header(name, tensor, OUT_DIR)

if __name__ == "__main__":
    export()

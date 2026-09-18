import torch
from src.model.mlp import TransitMLP

model = TransitMLP()
model.load_state_dict(torch.load("src/model/checkpoints/best.pt", map_location="cpu"))

for name, param in model.named_parameters():
    print(f"{name}: {param.shape}")

import pandas as pd
import torch
import numpy as np
from src.model.mlp import TransitMLP
from src.data.dataset import FEATURE_COLS


# -------------------------------------------------------------
# TODO: Import your PyTorch model architecture class here
# from model import YourMLPModel 
# -------------------------------------------------------------

def main():
    print("Loading features...")
    features_df = pd.read_csv('data/inference/features.csv')
    features_tensor = torch.tensor(features_df[FEATURE_COLS].values, dtype=torch.float32)   

    print("Running inference on PyTorch baseline model...")
    
    model = TransitMLP()
    model.load_state_dict(torch.load('src/model/checkpoints/best.pt', map_location="cpu"))
    model.eval()
    
    with torch.no_grad():
        outputs =  model(features_tensor) 
        pc_preds = torch.argmax(outputs, dim=1).numpy()

    # 3. Load logs/mcu_predictions.csv
    print("Loading MCU predictions...")
    mcu_df = pd.read_csv('logs/mcu_predictions.csv')
    
    # Assuming predictions are the first/only column in the CSV
    mcu_preds = mcu_df["prediction"].values
    
    # 4. Compare PC predictions vs MCU predictions
    #if len(pc_preds) != len(mcu_preds):
     #   print(f"Warning: Shape mismatch! PC rows ({len(pc_preds)}) vs MCU rows ({len(mcu_preds)})")
        # Align lengths if necessary to prevent crashing
      #  min_len = min(len(pc_preds), len(mcu_preds))
       # pc_preds, mcu_preds = pc_preds[:min_len], mcu_preds[:min_len]

    # merge on index so rows align correctly
    merged = pd.merge(
        pd.DataFrame({"index": range(len(pc_preds)), "pc_pred": pc_preds}),
        mcu_df[["index", "prediction"]].rename(columns={"prediction": "mcu_pred"}),
        on="index"
    )
    correct_matches = np.sum(merged["pc_pred"] == merged["mcu_pred"])
    total = len(merged)
    agreement_percentage = (correct_matches / total) * 100

    print("\n" + "="*30)
    print(f"Agreement Percentage: {agreement_percentage:.2f}%")
    print(f"Matching predictions: {correct_matches}/{len(pc_preds)}")
    print("="*30)

if __name__ == "__main__":
    main()

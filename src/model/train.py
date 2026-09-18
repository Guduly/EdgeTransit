import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

from src.data.dataset import TransitDataset
from src.model.mlp import TransitMLP

DATA_PATH = "data/processed/features.csv"
EPOCHS = 40
BATCH_SIZE = 256
LR = 1e-3

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")
    scaler = torch.amp.GradScaler("cuda")
    
    dataset = TransitDataset(DATA_PATH)
    n_val = int(len(dataset)*.2)
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=True)

    model = TransitMLP().to(device)
    crit = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    best_val_acc = 0.0
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0
        for X, y in train_loader:
            optimizer.zero_grad()
            X, y = X.to(device), y.to(device) 
            
            with torch.autocast(device_type="cuda"):
                output = model(X)
                loss = crit(output,y)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item() * len(y)

        avg_loss = total_loss/n_train

        model.eval()
        correct = 0

        with torch.no_grad():
            for X, y in val_loader:
                X, y = X.to(device), y.to(device) 
                preds = model(X).argmax(dim=1)
                correct += (preds==y).sum().item()
        
        val_acc = correct / n_val
        
        if val_acc > best_val_acc: 
            best_val_acc = val_acc
            torch.save(model.state_dict(), "src/model/checkpoints/best.pt")
            print(f"Curr best model saved to src/model/checkpoints/best.pt, val_acc={val_acc:.4f}")

        print(f"Epoch {epoch+1}/{EPOCHS}  loss={loss.item():.4f} val_acc={val_acc:.4f}")

if __name__ == "__main__":
    train()

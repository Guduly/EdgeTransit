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
    dataset = TransitDataset(DATA_PATH)
    n_val = int(len(dataset)*.2)
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=True)

    model = TransitMLP()
    crit = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0
        for X, y in train_loader:
            optimizer.zero_grad()
            output = model(X)
            loss = crit(output,y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y)

        avg_loss = total_loss/n_train

        model.eval()
        correct = 0

        with torch.no_grad():
            for X, y in val_loader:
                preds = model(X).argmax(dim=1)
                correct += (preds==y).sum().item()

        val_acc = correct / n_val
        print(f"Epoch {epoch+1}/{EPOCHS}  loss={loss.item():.4f} val_acc={val_acc:.4f}")

if __name__ == "__main__":
    train()

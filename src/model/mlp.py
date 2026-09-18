import torch
import torch.nn as nn

class TransitMLP(nn.Module):
    def __init__(self):
        super().__init__(); 
        self.fc1 = nn.Linear(in_features=8, out_features=32, bias=True)
        self.fc2 = nn.Linear(in_features=32, out_features=16, bias=True)
        self.fc3 = nn.Linear(in_features=16, out_features=3, bias=True)

    def forward(self, x):
        x = torch.relu(self.fc1(x)) 
        x = torch.relu(self.fc2(x)) 
        x = self.fc3(x)
        return x
    

if __name__ == "__main__":
    model = TransitMLP()
    dummy = torch.randn(4,8)
    out = model(dummy)
    print(out.shape) 


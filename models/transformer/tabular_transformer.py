import torch
import torch.nn as nn

class TabularTransformer(nn.Module):
    def __init__(self, input_dim: int, num_heads: int = 4, hidden_dim: int = 64):
        super().__init__()

        self.embedding = nn.Linear(input_dim, hidden_dim)
        self.encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(self.encoder_layer, num_layers=2)
        self.output = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        # x: (batch_size, features)
        x = self.embedding(x).unsqueeze(1)
        x = self.transformer(x)
        x = x.mean(dim=1)
        return torch.sigmoid(self.output(x))
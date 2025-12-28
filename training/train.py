import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

def train_model(model, X_train, y_train, epochs=10, lr=1e-3):
    dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32)
    )

    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for x_batch, y_batch in loader:
            optimizer.zero_grad()
            preds = model(x_batch).squeeze()
            loss = criterion(preds, y_batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        print(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f}")

    return model
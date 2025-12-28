import torch
from models.transformer.tabular_transformer import TabularTransformer

def test_transformer_forward_pass():
    model = TabularTransformer(input_dim=5)
    x = torch.rand(2, 5)
    output = model(x)
    assert output.shape == (2, 1)
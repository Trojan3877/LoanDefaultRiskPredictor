import pandas as pd
from features.feature_engineering import FeatureEngineer

def test_feature_scaling():
    df = pd.DataFrame({"income": [100, 200], "debt": [50, 100]})
    fe = FeatureEngineer()
    transformed = fe.fit_transform(df.copy())
    assert transformed.mean().abs().sum() < 1
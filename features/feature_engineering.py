import pandas as pd
from sklearn.preprocessing import StandardScaler

class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
        df[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
        df[numeric_cols] = self.scaler.transform(df[numeric_cols])
        return df
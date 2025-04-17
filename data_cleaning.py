import pandas as pd

def load_and_clean_data(filepath):
    df = pd.read_csv(filepath)
    df.dropna(inplace=True)
    df['Loan_Status'] = df['Loan_Status'].map({'Y': 1, 'N': 0})
    return df

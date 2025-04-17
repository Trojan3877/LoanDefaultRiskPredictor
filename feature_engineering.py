def encode_and_scale(df):
    df = pd.get_dummies(df, drop_first=True)
    X = df.drop("Loan_Status", axis=1)
    y = df["Loan_Status"]
    return X, y

from sklearn.linear_model import LogisticRegression

def train_logistic_regression(X_train, y_train):
    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        solver="lbfgs"
    )
    model.fit(X_train, y_train)
    return model
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, roc_auc_score
import json

def train_and_evaluate(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    f1 = f1_score(y_test, preds)
    roc = roc_auc_score(y_test, preds)

    metrics = {"F1 Score": f1, "ROC-AUC": roc}
    with open("outputs/metrics.json", "w") as f:
        json.dump(metrics, f)

    return model, metrics

from sklearn.metrics import roc_auc_score, accuracy_score, precision_recall_fscore_support

def evaluate_model(y_true, y_pred_probs):
    y_pred = (y_pred_probs >= 0.5).astype(int)

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "roc_auc": roc_auc_score(y_true, y_pred_probs),
        "precision": precision_recall_fscore_support(y_true, y_pred, average="binary")[0],
        "recall": precision_recall_fscore_support(y_true, y_pred, average="binary")[1],
        "f1": precision_recall_fscore_support(y_true, y_pred, average="binary")[2],
    }
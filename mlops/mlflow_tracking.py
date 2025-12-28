import mlflow

def log_experiment(params: dict, metrics: dict, model=None):
    with mlflow.start_run():
        for k, v in params.items():
            mlflow.log_param(k, v)

        for k, v in metrics.items():
            mlflow.log_metric(k, v)

        if model is not None:
            mlflow.pytorch.log_model(model, artifact_path="model")
import json
import sys

import src.train as train
from tests.helpers import loan_frame


def test_metrics_record_includes_the_same_training_commit_as_the_bundle(monkeypatch, tmp_path):
    class FakeLoader:
        def iter_chunks(self, _chunk_size):
            yield loan_frame()

    saved_bundle: dict[str, object] = {}
    metrics_path = tmp_path / "metrics.json"
    monkeypatch.setenv("GITHUB_SHA", "evidence-commit")
    monkeypatch.setattr(train.DataLoader, "from_uri", lambda _uri: FakeLoader())
    monkeypatch.setattr(
        train,
        "train_candidate",
        lambda *_args, **_kwargs: (
            object(),
            object(),
            {"roc_auc": 0.5},
            {"roc_auc": 0.4},
            "stratified-random-fallback",
            64,
            16,
        ),
    )
    monkeypatch.setattr(train, "dataset_fingerprint", lambda _source: "dataset-fingerprint")
    monkeypatch.setattr(
        train,
        "save_bundle",
        lambda *_args, **kwargs: saved_bundle.update(kwargs),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "train.py",
            "--uri",
            str(tmp_path / "source.csv"),
            "--output",
            str(tmp_path / "bundle"),
            "--metrics-output",
            str(metrics_path),
        ],
    )

    train.main()

    record = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert record["training_commit"] == "evidence-commit"
    assert saved_bundle["training_commit"] == record["training_commit"]

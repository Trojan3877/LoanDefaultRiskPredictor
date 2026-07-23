"""Versioned, checksummed model bundles shared by training and serving."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
from pydantic import BaseModel, ConfigDict, Field


class ModelManifest(BaseModel):
    """Portable metadata required to verify and interpret a model artifact."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    model_version: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    model_file: str = "model.joblib"
    model_sha256: str
    feature_schema_version: str = "loan-request-v1"
    policy_version: str = "review-policy-v1"
    threshold: float = Field(ge=0.0, le=1.0)
    dataset_id: str
    training_commit: str
    metrics: dict[str, float | int | str] = Field(default_factory=dict)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_bundle(
    destination: str | Path,
    payload: dict[str, Any],
    *,
    model_version: str,
    threshold: float,
    dataset_id: str,
    training_commit: str,
    metrics: dict[str, float | int | str],
) -> ModelManifest:
    directory = Path(destination)
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "model.joblib"
    joblib.dump(payload, model_path)
    manifest = ModelManifest(
        model_version=model_version,
        model_sha256=sha256_file(model_path),
        threshold=threshold,
        dataset_id=dataset_id,
        training_commit=training_commit,
        metrics=metrics,
    )
    (directory / "manifest.json").write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def load_bundle(source: str | Path) -> tuple[ModelManifest, dict[str, Any]]:
    """Verify before deserializing. Only load bundles from an administrator-controlled path."""

    directory = Path(source).resolve()
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Model manifest not found: {manifest_path}")
    manifest = ModelManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    model_path = (directory / manifest.model_file).resolve()
    if model_path.parent != directory or not model_path.is_file():
        raise ValueError("Manifest model path is invalid")
    if sha256_file(model_path) != manifest.model_sha256:
        raise ValueError("Model artifact checksum mismatch")
    payload = joblib.load(model_path)  # nosec B301
    required = {"model", "feature_engineer"}
    if not isinstance(payload, dict) or not required.issubset(payload):
        raise ValueError("Model payload is missing required components")
    return manifest, payload


def dataset_fingerprint(path: str | Path) -> str:
    return f"sha256:{sha256_file(Path(path))}"

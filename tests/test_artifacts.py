import json

import pytest

from src.artifacts import load_bundle
from tests.helpers import create_test_bundle


def test_bundle_roundtrip_and_checksum(tmp_path):
    path = create_test_bundle(tmp_path / "bundle")
    manifest, payload = load_bundle(path)
    assert manifest.model_version == "test-v1"
    assert set(payload) == {"model", "feature_engineer"}
    with (path / "model.joblib").open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        load_bundle(path)


def test_manifest_rejects_unknown_fields(tmp_path):
    path = create_test_bundle(tmp_path / "bundle")
    manifest_path = path / "manifest.json"
    document = json.loads(manifest_path.read_text())
    document["unexpected"] = True
    manifest_path.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        load_bundle(path)

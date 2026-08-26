"""Release metadata and workflow contracts that are cheap to verify locally."""

from __future__ import annotations

import tomllib
from pathlib import Path

from src.version import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_has_a_single_source_of_truth() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["dynamic"] == ["version"]
    assert metadata["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "src.version.__version__"
    }
    assert __version__ == "0.3.0"


def test_release_workflow_requires_an_immutable_tag_and_builds_distributions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert 'tags: ["v*"]' in workflow
    assert "python -m build" in workflow
    assert "twine check dist/*" in workflow
    assert "actions/attest-build-provenance@v2" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "PUBLISH_PYPI" in workflow

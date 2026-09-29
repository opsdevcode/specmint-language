from __future__ import annotations

from pathlib import Path


def test_platform_composition_doc_names_federated_manifest() -> None:
    source = Path("specification/mint/v0/platform-composition.md").read_text(encoding="utf-8")
    assert "opsdevcode.capability-manifest/v1alpha1" in source
    assert "mint apply" in source

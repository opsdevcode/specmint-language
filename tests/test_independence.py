from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN = frozenset({"overpass", "toll", "dispatch", "repave_engine", "relay"})
SRC = Path(__file__).resolve().parents[1] / "src"


def test_language_does_not_import_product_packages() -> None:
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module.split(".", 1)[0])
            for name in names:
                if name in FORBIDDEN:
                    offenders.append(f"{path}:{name}")
    assert offenders == []


def test_standalone_doc_matches_import_boundary() -> None:
    text = (Path(__file__).resolve().parents[1] / "docs" / "standalone.md").read_text(
        encoding="utf-8"
    )
    assert "does not import" in text
    assert "Repave" in text
    assert "Overpass" in text
    assert "Toll" in text
    assert "Dispatch" in text
    assert "Relay" in text
    assert "mint apply" in text
    assert "not PyPI" in text
    assert "Kubernetes" in text
    assert "snapshot integration" in text
    assert "mint-integration-local" in text
    assert "mint-integration-github" in text

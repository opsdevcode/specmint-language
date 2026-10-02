from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = (REPO / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")


def test_release_is_tag_driven_and_once_built() -> None:
    assert "tags:" in WORKFLOW
    assert '"v*"' in WORKFLOW or "'v*'" in WORKFLOW
    assert "branches: [main]" not in WORKFLOW
    assert "python -m build --sdist --wheel" in WORKFLOW
    assert "Test exact artifacts in isolated Python 3.12 venvs" in WORKFLOW
    assert "sha256sum" in WORKFLOW
    assert "anchore/sbom-action@66cbf4bc1f1c0d2edc94016e65bc221b6bb0ad6c" in WORKFLOW
    assert "actions/attest-build-provenance@db473fddc028af60658334401dc6fa3ffd8669fd" in WORKFLOW
    assert "pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e" in WORKFLOW


def test_release_refuses_latest_rebuild_and_pypi_token() -> None:
    assert "never publish latest" in WORKFLOW
    assert "fail closed (do not rebuild or overwrite)" in WORKFLOW
    assert "PYPI_TOKEN" not in WORKFLOW
    assert "password:" not in WORKFLOW
    assert "skip-existing: false" in WORKFLOW
    assert "packages-dir: pypi-dist" in WORKFLOW
    assert "GH_REPO: ${{ github.repository }}" in WORKFLOW
    assert "refuse 1.x tag" in WORKFLOW


def test_release_pins_third_party_actions_to_shas() -> None:
    for line in WORKFLOW.splitlines():
        stripped = line.strip()
        if stripped.startswith("uses:"):
            spec = stripped.split("uses:", 1)[1].strip()
            if spec.startswith("./"):
                continue
            name, _, ref = spec.partition("@")
            assert name, spec
            sha = ref.split()[0]
            assert len(sha) == 40, f"unpin {spec}"
            assert all(ch in "0123456789abcdef" for ch in sha), spec

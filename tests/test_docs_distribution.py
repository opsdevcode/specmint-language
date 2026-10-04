from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAGES = (REPO / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
README = (REPO / "README.md").read_text(encoding="utf-8")
CANONICAL_DOCS_URL = "https://opsdevcode.github.io/specmint-language/"
SUPERSEDED_RELEASE_PINS = ("0.1.0a2", "0.1.0-alpha.2")
CURRENT_INSTALL_DOCS = (
    REPO / "README.md",
    REPO / "docs" / "index.md",
    REPO / "docs" / "quickstart.md",
    REPO / "docs" / "releases.md",
    REPO / "docs" / "compatibility.md",
    REPO / "editors" / "vscode" / "README.md",
)


def _current_versions() -> tuple[str, str]:
    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    semver = pyproject["project"]["version"]
    pep440 = semver.replace("-alpha.", "a")
    return semver, pep440


def test_current_install_docs_are_unpinned() -> None:
    semver, pep440 = _current_versions()
    assert "pipx install specmint" in README
    assert "uv tool install specmint" in README
    assert "pipx install specmint==" not in README
    assert "uv tool install specmint==" not in README
    for path in CURRENT_INSTALL_DOCS:
        text = path.read_text(encoding="utf-8")
        for pin in SUPERSEDED_RELEASE_PINS:
            assert pin not in text, f"{path} still pins superseded {pin}"
        assert f"pipx install specmint=={pep440}" not in text
        assert f"pipx install specmint=={semver}" not in text


def test_canonical_docs_url_is_github_pages() -> None:
    assert CANONICAL_DOCS_URL in README
    assert 'Documentation = "https://opsdevcode.github.io/specmint-language/"' in (
        REPO / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert "GitHub Pages for this repository is not enabled" not in (
        REPO / "docs" / "index.md"
    ).read_text(encoding="utf-8")


def test_pages_workflow_deploys_static_docs() -> None:
    assert "actions/deploy-pages@" in PAGES
    assert "scripts/build_docs_site.py" in PAGES
    assert "Pages disabled at org" not in PAGES
    assert "skip:" not in PAGES
    assert ":latest" not in PAGES
    assert "tag: latest" not in PAGES
    for line in PAGES.splitlines():
        stripped = line.strip()
        if not stripped.startswith("uses:"):
            continue
        spec = stripped.split("uses:", 1)[1].strip()
        sha = spec.partition("@")[2].split()[0]
        assert len(sha) == 40, spec
        assert all(ch in "0123456789abcdef" for ch in sha), spec


def test_docs_site_builds_index(tmp_path: Path) -> None:
    out = tmp_path / "site"
    built = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_docs_site.py"), "--out", str(out)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "Mint language" in index
    assert 'rel="canonical" href="https://opsdevcode.github.io/specmint-language/"' in index
    assert 'href="specification/mint/v0/language.html"' in index
    assert (out / "docs" / "quickstart.html").is_file()
    assert (out / "specification" / "mint" / "v0" / "language.html").is_file()
    assert (out / "specification" / "mint" / "v0" / "grammar.ebnf").is_file()
    assert (out / ".nojekyll").is_file()
    quickstart = (out / "docs" / "quickstart.html").read_text(encoding="utf-8")
    assert "pipx install specmint" in quickstart
    assert "0.1.0a2" not in quickstart

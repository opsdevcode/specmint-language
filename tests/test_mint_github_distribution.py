"""Offline GitHub-first catalog coordinate checks. No network and no PyPI."""

from __future__ import annotations

import hashlib
from pathlib import Path

from opsdevcode_specmint.mint.catalog import github_catalog_integrations
from opsdevcode_specmint.mint.github_distribution import (
    match_bytes,
    parse_sha256sums,
    sha256_digest,
    verify_recorded_assets,
)


def test_match_bytes_names_the_expected_digest() -> None:
    payload = b"mint-github-first"
    expected = sha256_digest(payload)
    ok = match_bytes(payload, expected=expected, path="demo.whl")
    assert ok.ok is True
    wrong = match_bytes(payload, expected="sha256:" + "0" * 64, path="demo.whl")
    assert wrong.ok is False
    assert "does not match recorded" in wrong.message


def test_parse_sha256sums_strips_dot_slash() -> None:
    text = (
        "591e1b3ebdd7e4f9373996e0cdeafa62d8fea39d2640ded8270ff2e59c68094d  "
        "./mint_integration_local-0.2.0a1-py3-none-any.whl\n"
    )
    parsed = parse_sha256sums(text)
    assert parsed["mint_integration_local-0.2.0a1-py3-none-any.whl"] == (
        "sha256:591e1b3ebdd7e4f9373996e0cdeafa62d8fea39d2640ded8270ff2e59c68094d"
    )


def test_verify_recorded_assets_against_local_files(tmp_path: Path) -> None:
    records = github_catalog_integrations()
    for record in records:
        coordinate = record.github
        assert coordinate is not None
        repo_dir = tmp_path / Path(coordinate.repository).name
        repo_dir.mkdir()
        wheel = b"wheel:" + coordinate.artifact.encode()
        manifest = b"manifest:" + record.identity.encode()
        # rebuild recorded hashes to match files we control
        wheel_digest = "sha256:" + hashlib.sha256(wheel).hexdigest()
        manifest_digest = "sha256:" + hashlib.sha256(manifest).hexdigest()
        (repo_dir / coordinate.artifact).write_bytes(wheel)
        (repo_dir / "mint-integration.json").write_bytes(manifest)
        (repo_dir / "SHA256SUMS").write_text(
            f"{wheel_digest.removeprefix('sha256:')}  ./{coordinate.artifact}\n",
            encoding="utf-8",
        )
        from dataclasses import replace

        from opsdevcode_specmint.mint.catalog import CatalogIntegration

        patched_github = replace(
            coordinate, artifact_digest=wheel_digest, manifest_digest=manifest_digest
        )
        patched = CatalogIntegration(
            identity=record.identity,
            version=record.version,
            name=record.name,
            summary=record.summary,
            capabilities=record.capabilities,
            target_kinds=record.target_kinds,
            phases=record.phases,
            execution_support=record.execution_support,
            origin="github",
            github=patched_github,
        )
        matches = verify_recorded_assets(tmp_path, records=(patched,))
        assert matches
        assert all(item.ok for item in matches), [item.message for item in matches]


def test_catalog_github_records_are_not_pypi() -> None:
    for record in github_catalog_integrations():
        assert record.github is not None
        assert "pypi.org" not in record.github.url
        assert record.github.tag != "latest"
        assert record.github.artifact_digest.startswith("sha256:")
        assert record.github.manifest_digest.startswith("sha256:")

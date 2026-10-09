"""Offline GitHub-first integration coordinate checks.

Language-core stays offline. Callers supply already-downloaded bytes.
A CI script may fetch GitHub Release assets; add/verify never do.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from opsdevcode_specmint.mint.catalog import CatalogIntegration, github_catalog_integrations

_SHA256_LINE = re.compile(r"^([0-9a-f]{64})\s+\*?\.?/?(.+?)\s*$")


@dataclass(frozen=True, slots=True)
class DigestMatch:
    ok: bool
    path: str
    expected: str
    actual: str
    message: str


def sha256_digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def match_bytes(payload: bytes, *, expected: str, path: str) -> DigestMatch:
    actual = sha256_digest(payload)
    if actual == expected:
        return DigestMatch(
            ok=True,
            path=path,
            expected=expected,
            actual=actual,
            message=f"{path} matches {expected}",
        )
    return DigestMatch(
        ok=False,
        path=path,
        expected=expected,
        actual=actual,
        message=f"{path} digest {actual} does not match recorded {expected}",
    )


def match_file(path: Path, *, expected: str) -> DigestMatch:
    if path.is_symlink() or not path.is_file():
        return DigestMatch(
            ok=False,
            path=str(path),
            expected=expected,
            actual="",
            message=f"{path} must be a real file to verify against {expected}",
        )
    return match_bytes(path.read_bytes(), expected=expected, path=path.name)


def parse_sha256sums(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        matched = _SHA256_LINE.match(line)
        if matched is None:
            continue
        digest, name = matched.group(1), Path(matched.group(2)).name
        found[name] = "sha256:" + digest
    return found


def verify_recorded_assets(
    assets_dir: Path, *, records: tuple[CatalogIntegration, ...] | None = None
) -> tuple[DigestMatch, ...]:
    chosen = records if records is not None else github_catalog_integrations()
    matches: list[DigestMatch] = []
    for record in chosen:
        coordinate = record.github
        if coordinate is None:
            continue
        repo_dir = assets_dir / Path(coordinate.repository).name
        sums_path = repo_dir / "SHA256SUMS"
        if sums_path.is_file() and not sums_path.is_symlink():
            listed = parse_sha256sums(sums_path.read_text(encoding="utf-8"))
            recorded = listed.get(coordinate.artifact)
            if recorded != coordinate.artifact_digest:
                matches.append(
                    DigestMatch(
                        ok=False,
                        path=str(sums_path),
                        expected=coordinate.artifact_digest,
                        actual=recorded or "",
                        message=(
                            f"{sums_path} does not list {coordinate.artifact} as "
                            f"{coordinate.artifact_digest}"
                        ),
                    )
                )
        artifact_path = repo_dir / coordinate.artifact
        matches.append(match_file(artifact_path, expected=coordinate.artifact_digest))
        manifest_path = repo_dir / "mint-integration.json"
        matches.append(match_file(manifest_path, expected=coordinate.manifest_digest))
    return tuple(matches)

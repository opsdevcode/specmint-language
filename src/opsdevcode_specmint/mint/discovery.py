"""Offline integration discovery and project pinning.

search / inspect / add / remove / verify / status / update stay local.
add and update never install packages, never execute an integration, and
never open a network path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from opsdevcode_specmint.integration.models import parse_manifest
from opsdevcode_specmint.integration.reference_server import (
    IDENTITY as REFERENCE_IDENTITY,
)
from opsdevcode_specmint.integration.reference_server import (
    VERSION as REFERENCE_VERSION,
)
from opsdevcode_specmint.integration.reference_server import (
    artifact_digest,
    manifest_document,
)
from opsdevcode_specmint.integration.supervisor import ProcessStatus
from opsdevcode_specmint.mint.catalog import (
    CATALOG_RECORDS_SCHEMA,
    catalog_integration,
    search_catalog_integrations,
)
from opsdevcode_specmint.mint.errors import coded_error
from opsdevcode_specmint.mint.project import (
    LOCK_NAME,
    ProjectIntegration,
    ProjectManifest,
    build_lockfile,
    check_lockfile,
    load_manifest,
    render_manifest,
    write_lockfile,
    write_manifest,
)

_NETWORK_SCHEMES = frozenset({"http", "https", "git", "ssh", "git+https", "git+ssh"})
_NETWORK_HINTS = (
    "://",
    "git@",
    "github.com",
    "gitlab.com",
    "pypi.org",
    "pypi.python.org",
)


def refuse_network_source(raw: str, *, label: str) -> None:
    text = raw.strip()
    if not text:
        return
    scheme = urlsplit(text).scheme.lower()
    lowered = text.lower()
    if scheme in _NETWORK_SCHEMES or any(hint in lowered for hint in _NETWORK_HINTS):
        raise coded_error(
            "MINT_INTEGRATION",
            f"{label} stays local; refuse network source {raw}",
        )


def search_integrations(
    *,
    query: str = "",
    capability: str = "",
    target_kind: str = "",
) -> dict[str, Any]:
    refuse_network_source(query, label="search query")
    refuse_network_source(capability, label="capability filter")
    refuse_network_source(target_kind, label="target-kind filter")
    records = [
        item.to_record()
        for item in search_catalog_integrations(
            query=query,
            capability=capability,
            target_kind_filter=target_kind,
        )
    ]
    return {
        "integrations": records,
        "network": False,
        "ok": True,
        "query": query,
        "schema": CATALOG_RECORDS_SCHEMA,
    }


def inspect_integration(identity: str) -> dict[str, Any]:
    refuse_network_source(identity, label="inspect identity")
    if identity == REFERENCE_IDENTITY:
        return manifest_document()
    record = catalog_integration(identity)
    if record is None:
        raise coded_error("MINT_INTEGRATION", f"unknown integration {identity}")
    return {
        "catalog": record.to_record(),
        "identity": record.identity,
        "network": False,
        "ok": True,
        "schema": "mint.integration/v0",
        "version": record.version,
    }


def add_integration(
    project: Path,
    *,
    identity: str = "",
    local: str = "",
) -> dict[str, Any]:
    refuse_network_source(identity, label="add identity")
    refuse_network_source(local, label="add --local")
    if identity.lower() in {"pip", "pipx", "uv"} or local.lower() in {"pip", "pipx", "uv"}:
        raise coded_error(
            "MINT_INTEGRATION",
            "mint integrations add does not pip, pipx, or execute an integration",
        )
    manifest = load_manifest(_project_manifest_path(project))
    requirement = _requirement_for_add(manifest, identity=identity, local=local)
    if any(item.source == requirement.source for item in manifest.integrations):
        raise coded_error(
            "MINT_INTEGRATION",
            f"{requirement.source} is already pinned in {manifest.path.name}",
        )
    updated = _with_integrations(manifest, (*manifest.integrations, requirement))
    write_manifest(updated)
    lock = build_lockfile(updated)
    write_lockfile(updated, lock)
    pinned = next(item for item in lock.integrations if item.identity == requirement.source)
    origin = "local"
    if not requirement.local:
        origin = "packaged" if requirement.source == REFERENCE_IDENTITY else "github"
    return {
        "action": "add",
        "artifactDigest": pinned.artifact_digest,
        "executed": False,
        "identity": requirement.source,
        "installed": False,
        "lock": LOCK_NAME,
        "manifestDigest": pinned.manifest_digest,
        "network": False,
        "ok": True,
        "origin": origin,
        "version": requirement.version,
    }


def remove_integration(project: Path, identity: str) -> dict[str, Any]:
    refuse_network_source(identity, label="remove identity")
    manifest = load_manifest(_project_manifest_path(project))
    remaining = tuple(item for item in manifest.integrations if item.source != identity)
    if len(remaining) == len(manifest.integrations):
        raise coded_error(
            "MINT_INTEGRATION",
            f"{identity} is not pinned in {manifest.path.name}",
        )
    updated = _with_integrations(manifest, remaining)
    write_manifest(updated)
    lock = build_lockfile(updated)
    write_lockfile(updated, lock)
    return {
        "action": "remove",
        "identity": identity,
        "lock": LOCK_NAME,
        "network": False,
        "ok": True,
        "remaining": [item.source for item in remaining],
    }


def verify_integrations(project: Path) -> dict[str, Any]:
    manifest = load_manifest(_project_manifest_path(project))
    lock = check_lockfile(manifest)
    return {
        "action": "verify",
        "catalogDigest": lock.catalog_digest,
        "executed": False,
        "integrations": [
            {
                "artifactDigest": item.artifact_digest,
                "identity": item.identity,
                "manifestDigest": item.manifest_digest,
                "matched": True,
                "origin": _origin_for(manifest, item.identity),
                "version": item.version,
            }
            for item in lock.integrations
        ],
        "lock": LOCK_NAME,
        "lockUpdated": True,
        "network": False,
        "ok": True,
    }


def status_integrations(project: Path) -> dict[str, Any]:
    manifest = load_manifest(_project_manifest_path(project))
    lock = check_lockfile(manifest)
    statuses = [
        ProcessStatus(
            identity=item.identity,
            version=item.version,
            phase="",
            running=False,
            pid=None,
            artifact_digest=item.artifact_digest,
            last_digest="",
            ok=True,
            message="idle",
        ).to_record()
        | {"origin": _origin_for(manifest, item.identity)}
        for item in lock.integrations
    ]
    return {
        "action": "status",
        "executed": False,
        "integrations": statuses,
        "lock": LOCK_NAME,
        "network": False,
        "ok": True,
        "running": False,
    }


def update_integrations(project: Path) -> dict[str, Any]:
    path = _project_manifest_path(project)
    manifest = load_manifest(path)
    refreshed = tuple(
        _requirement_for_add(manifest, identity=item.source, local=item.local)
        for item in manifest.integrations
    )
    updated = _with_integrations(manifest, refreshed)
    write_manifest(updated)
    lock = build_lockfile(updated)
    write_lockfile(updated, lock)
    return {
        "action": "update",
        "executed": False,
        "installed": False,
        "integrations": [
            {
                "artifactDigest": item.artifact_digest,
                "identity": item.identity,
                "manifestDigest": item.manifest_digest,
                "origin": _origin_for(updated, item.identity),
                "version": item.version,
            }
            for item in lock.integrations
        ],
        "lock": LOCK_NAME,
        "network": False,
        "ok": True,
        "pip": False,
        "updated": True,
    }


def _origin_for(manifest: ProjectManifest, identity: str) -> str:
    for item in manifest.integrations:
        if item.source != identity:
            continue
        if item.local:
            return "local"
        if item.source == REFERENCE_IDENTITY:
            return "packaged"
        record = catalog_integration(item.source, item.version, origin="github")
        if record is not None:
            return "github"
        return "packaged"
    return "unknown"


def _requirement_for_add(
    manifest: ProjectManifest,
    *,
    identity: str,
    local: str,
) -> ProjectIntegration:
    if local:
        relative = local.strip().replace("\\", "/")
        document = _load_local_manifest(manifest, relative)
        return ProjectIntegration(
            source=str(document["identity"]),
            version=str(document["version"]),
            local=relative,
            capabilities=tuple(str(item["id"]) for item in document["capabilities"]),
            targets=tuple(str(item) for item in document["targetKinds"]),
            phases=tuple(str(item) for item in document["phases"]),
            realization="",
        )
    chosen = identity.strip() or REFERENCE_IDENTITY
    if chosen == REFERENCE_IDENTITY:
        packaged = parse_manifest(manifest_document()).document
        if packaged["artifact"]["digest"] != artifact_digest():
            raise coded_error("MINT_DIGEST", f"artifact digest mismatch for {REFERENCE_IDENTITY}")
        return ProjectIntegration(
            source=REFERENCE_IDENTITY,
            version=REFERENCE_VERSION,
            local="",
            capabilities=tuple(str(item["id"]) for item in packaged["capabilities"]),
            targets=tuple(str(item) for item in packaged["targetKinds"]),
            phases=tuple(str(item) for item in packaged["phases"]),
            realization="",
        )
    record = catalog_integration(chosen, origin="github")
    if record is None or record.github is None:
        raise coded_error(
            "MINT_INTEGRATION",
            f"missing local manifest for {chosen}; pass --local PATH or pin a "
            "github catalog identity",
        )
    return ProjectIntegration(
        source=record.identity,
        version=record.version,
        local="",
        capabilities=tuple(capability_id for capability_id, _version in record.capabilities),
        targets=record.target_kinds,
        phases=record.phases,
        realization="",
    )


def _load_local_manifest(manifest: ProjectManifest, relative: str) -> dict[str, Any]:
    refuse_network_source(relative, label="local manifest")
    path = manifest.directory / Path(relative)
    if path.is_symlink() or not path.is_file():
        raise coded_error(
            "MINT_PATH",
            f"{relative} must be a real project-relative mint.integration/v0 file",
        )
    try:
        path.resolve().relative_to(manifest.directory.resolve())
    except ValueError:
        raise coded_error(
            "MINT_PATH",
            f"{relative} escapes the project directory; use a path under the manifest",
        ) from None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise coded_error(
            "MINT_INTEGRATION",
            f"{relative} must be mint.integration/v0 JSON",
        ) from exc
    return parse_manifest(document).document


def _with_integrations(
    manifest: ProjectManifest,
    integrations: tuple[ProjectIntegration, ...],
) -> ProjectManifest:
    return ProjectManifest(
        schema=manifest.schema,
        name=manifest.name,
        edition=manifest.edition,
        root=manifest.root,
        units=manifest.units,
        catalogs=manifest.catalogs,
        extension_paths=manifest.extension_paths,
        profiles=manifest.profiles,
        directory=manifest.directory,
        integrations=tuple(sorted(integrations, key=lambda item: item.source)),
    )


def _project_manifest_path(project: Path) -> Path:
    path = project.expanduser()
    if path.is_file() and path.name == "mint.toml":
        return path
    if path.is_dir():
        return path / "mint.toml"
    raise coded_error(
        "MINT_PROJECT",
        "pass --project to a mint.toml directory",
    )


def preview_manifest(manifest: ProjectManifest) -> str:
    return render_manifest(manifest)

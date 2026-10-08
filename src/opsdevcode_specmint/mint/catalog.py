"""Closed language catalog loaded from local records. No provider SDKs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opsdevcode_specmint.mint.errors import catalog_error

ENSURE_MARKER_TYPE = "local.sandbox.ensure_marker"
ENSURE_MARKER_VERSION = "v1alpha1"
MINT_CATALOG_VERSION = "v0"
REPO_GITHUB_KIND = "repo.github"
REPO_SETTINGS_TYPE = "repo.settings"
REPO_BRANCH_PROTECTION_TYPE = "repo.branch_protection"
REPO_SECURITY_TYPE = "repo.security"
REPO_MANAGED_FILE_TYPE = "repo.managed_file"
CAPABILITY_VERSION = "v1alpha1"
CATALOG_RECORDS_SCHEMA = "mint.catalog-records/v0"

SUPPORT_FULL = "full"
SUPPORT_PARTIAL = "partial"
SUPPORT_NONE = "none"
_SUPPORT = frozenset({SUPPORT_FULL, SUPPORT_PARTIAL, SUPPORT_NONE})


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    automation_type: str
    version: str


@dataclass(frozen=True, slots=True)
class TargetKind:
    kind: str
    fields: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class CapabilityDecl:
    capability_type: str
    version: str
    target_kinds: frozenset[str]
    support: str = SUPPORT_FULL


@dataclass(frozen=True, slots=True)
class CatalogIntegration:
    identity: str
    version: str
    name: str
    summary: str
    capabilities: tuple[tuple[str, str], ...]
    target_kinds: tuple[str, ...]
    phases: tuple[str, ...]
    execution_support: str
    origin: str

    def to_record(self) -> dict[str, Any]:
        return {
            "capabilities": [
                {"id": capability_id, "version": capability_version}
                for capability_id, capability_version in self.capabilities
            ],
            "executionSupport": self.execution_support,
            "identity": self.identity,
            "name": self.name,
            "origin": self.origin,
            "phases": list(self.phases),
            "summary": self.summary,
            "targetKinds": list(self.target_kinds),
            "version": self.version,
        }


def catalog_records_path() -> Path:
    return Path(__file__).with_name("catalog_records") / "v0.json"


def load_catalog_records() -> dict[str, Any]:
    raw = json.loads(catalog_records_path().read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise catalog_error("catalog records must be a JSON object")
    if raw.get("schema") != CATALOG_RECORDS_SCHEMA:
        raise catalog_error(f"catalog records schema must be {CATALOG_RECORDS_SCHEMA}")
    if raw.get("version") != MINT_CATALOG_VERSION:
        raise catalog_error(f"catalog records version must be {MINT_CATALOG_VERSION}")
    return raw


def _target_kinds_from_records(document: dict[str, Any]) -> tuple[TargetKind, ...]:
    items = document.get("targetKinds")
    if not isinstance(items, list) or not items:
        raise catalog_error("catalog records need a non-empty targetKinds array")
    kinds: list[TargetKind] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise catalog_error("each target kind record must be an object")
        kind = str(item.get("kind", ""))
        fields_raw = item.get("fields")
        if not kind or not isinstance(fields_raw, list) or not fields_raw:
            raise catalog_error(f"target kind {kind or 'record'} needs kind and fields")
        if kind in seen:
            raise catalog_error(f"duplicate target kind {kind}")
        seen.add(kind)
        fields: list[tuple[str, str]] = []
        for pair in fields_raw:
            if not isinstance(pair, list) or len(pair) != 2:
                raise catalog_error(f"target kind {kind} fields must be [name, type] pairs")
            fields.append((str(pair[0]), str(pair[1])))
        kinds.append(TargetKind(kind, tuple(fields)))
    return tuple(kinds)


def _capabilities_from_records(document: dict[str, Any]) -> tuple[CapabilityDecl, ...]:
    items = document.get("capabilities")
    if not isinstance(items, list) or not items:
        raise catalog_error("catalog records need a non-empty capabilities array")
    capabilities: list[CapabilityDecl] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if not isinstance(item, dict):
            raise catalog_error("each capability record must be an object")
        ident = str(item.get("id", ""))
        version = str(item.get("version", ""))
        support = str(item.get("support", SUPPORT_FULL))
        kinds_raw = item.get("targetKinds")
        if not ident or not version or not isinstance(kinds_raw, list) or not kinds_raw:
            raise catalog_error("capability records need id, version, and targetKinds")
        if support not in _SUPPORT:
            raise catalog_error(f"capability {ident} support must be full, partial, or none")
        key = (ident, version)
        if key in seen:
            raise catalog_error(f"duplicate capability {ident} {version}")
        seen.add(key)
        capabilities.append(
            CapabilityDecl(ident, version, frozenset(str(kind) for kind in kinds_raw), support)
        )
    return tuple(capabilities)


def _integrations_from_records(document: dict[str, Any]) -> tuple[CatalogIntegration, ...]:
    items = document.get("integrations", [])
    if items in (None, []):
        return ()
    if not isinstance(items, list):
        raise catalog_error("catalog records integrations must be an array")
    integrations: list[CatalogIntegration] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if not isinstance(item, dict):
            raise catalog_error("each catalog integration record must be an object")
        allowed = {
            "capabilities",
            "executionSupport",
            "identity",
            "name",
            "origin",
            "phases",
            "summary",
            "targetKinds",
            "version",
        }
        unknown = sorted(set(item) - allowed)
        if unknown:
            raise catalog_error(f"remove unknown catalog integration keys {unknown}")
        identity = str(item.get("identity", ""))
        version = str(item.get("version", ""))
        origin = str(item.get("origin", ""))
        if origin not in {"packaged", "local"}:
            raise catalog_error(
                f"catalog integration {identity or 'record'} origin must be packaged or local"
            )
        capabilities_raw = item.get("capabilities")
        kinds_raw = item.get("targetKinds")
        phases_raw = item.get("phases")
        if (
            not identity
            or not version
            or not isinstance(capabilities_raw, list)
            or not capabilities_raw
            or not isinstance(kinds_raw, list)
            or not kinds_raw
            or not isinstance(phases_raw, list)
            or not phases_raw
        ):
            raise catalog_error(
                "catalog integration records need identity, version, capabilities, "
                "targetKinds, and phases"
            )
        key = (identity, version)
        if key in seen:
            raise catalog_error(f"duplicate catalog integration {identity} {version}")
        seen.add(key)
        capabilities: list[tuple[str, str]] = []
        for capability in capabilities_raw:
            if not isinstance(capability, dict):
                raise catalog_error(f"catalog integration {identity} capabilities must be objects")
            capabilities.append((str(capability.get("id", "")), str(capability.get("version", ""))))
        integrations.append(
            CatalogIntegration(
                identity=identity,
                version=version,
                name=str(item.get("name", "")),
                summary=str(item.get("summary", "")),
                capabilities=tuple(capabilities),
                target_kinds=tuple(str(kind) for kind in kinds_raw),
                phases=tuple(str(phase) for phase in phases_raw),
                execution_support=str(item.get("executionSupport", "")),
                origin=origin,
            )
        )
    return tuple(sorted(integrations, key=lambda item: (item.identity, item.version)))


_RECORDS = load_catalog_records()
TARGET_KINDS: tuple[TargetKind, ...] = _target_kinds_from_records(_RECORDS)
CAPABILITIES: tuple[CapabilityDecl, ...] = _capabilities_from_records(_RECORDS)
INTEGRATIONS: tuple[CatalogIntegration, ...] = _integrations_from_records(_RECORDS)
ENSURE_MARKER = CatalogEntry(ENSURE_MARKER_TYPE, ENSURE_MARKER_VERSION)
CATALOG: frozenset[CatalogEntry] = frozenset({ENSURE_MARKER})


def bind_catalog_entry(*, automation_type: str, version: str) -> CatalogEntry:
    entry = CatalogEntry(automation_type, version)
    if capability_for(automation_type, version) is None:
        accepted = ", ".join(
            sorted(f"{item.capability_type} {item.version}" for item in CAPABILITIES)
        )
        raise catalog_error(
            f"unknown automation type {automation_type} {version}; "
            f"catalog {MINT_CATALOG_VERSION} accepts {accepted}"
        )
    return entry


def capability_for(capability_type: str, version: str) -> CapabilityDecl | None:
    for item in CAPABILITIES:
        if item.capability_type == capability_type and item.version == version:
            return item
    return None


def target_kind(kind: str) -> TargetKind | None:
    for item in TARGET_KINDS:
        if item.kind == kind:
            return item
    return None


def sorted_catalog_ids() -> tuple[str, ...]:
    return tuple(sorted(f"{item.capability_type}@{item.version}" for item in CAPABILITIES))


def catalog_integration(identity: str, version: str | None = None) -> CatalogIntegration | None:
    matches = [item for item in INTEGRATIONS if item.identity == identity]
    if version:
        matches = [item for item in matches if item.version == version]
    if len(matches) == 1:
        return matches[0]
    return None


def search_catalog_integrations(
    *,
    query: str = "",
    capability: str = "",
    target_kind_filter: str = "",
) -> tuple[CatalogIntegration, ...]:
    needle = query.strip().lower()
    found: list[CatalogIntegration] = []
    for item in INTEGRATIONS:
        haystack = " ".join(
            [
                item.identity,
                item.name,
                item.summary,
                " ".join(kind for kind in item.target_kinds),
                " ".join(capability_id for capability_id, _version in item.capabilities),
            ]
        ).lower()
        if needle and needle not in haystack:
            continue
        if capability and capability not in {ident for ident, _version in item.capabilities}:
            continue
        if target_kind_filter and target_kind_filter not in item.target_kinds:
            continue
        found.append(item)
    return tuple(found)

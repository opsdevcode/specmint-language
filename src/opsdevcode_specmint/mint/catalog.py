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


_RECORDS = load_catalog_records()
TARGET_KINDS: tuple[TargetKind, ...] = _target_kinds_from_records(_RECORDS)
CAPABILITIES: tuple[CapabilityDecl, ...] = _capabilities_from_records(_RECORDS)
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

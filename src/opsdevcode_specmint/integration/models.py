"""Typed mint.integration/v0 manifests and realization bindings."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from opsdevcode_specmint.integration.canonical import (
    EXECUTION_SUPPORT,
    PHASES,
    SCHEMA_INTEGRATION,
    SCHEMA_REALIZATION,
    content_digest,
    reject_absolute_path,
    reject_secrets,
    reject_unknown,
)

_IDENTITY = re.compile(r"^[a-z][a-z0-9_-]*(\.[a-z][a-z0-9_-]*)+$")
_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_MANIFEST_KEYS = frozenset(
    {
        "artifact",
        "capabilities",
        "compatibility",
        "configurationSchemas",
        "deprecation",
        "executionSupport",
        "identity",
        "implementation",
        "name",
        "namespace",
        "permissions",
        "phases",
        "protocolVersions",
        "provenance",
        "schema",
        "targetKinds",
        "version",
    }
)


@dataclass(frozen=True, slots=True)
class IntegrationManifest:
    document: dict[str, Any]

    @property
    def identity(self) -> str:
        return str(self.document["identity"])

    @property
    def version(self) -> str:
        return str(self.document["version"])

    @property
    def phases(self) -> tuple[str, ...]:
        return tuple(self.document["phases"])

    @property
    def execution_support(self) -> str:
        return str(self.document["executionSupport"])

    def digest(self) -> str:
        return content_digest(self.document)

    def supports(self, phase: str) -> bool:
        return phase in self.phases


def parse_manifest(document: Any) -> IntegrationManifest:
    if not isinstance(document, dict):
        raise ValueError("integration manifest must be a JSON object")
    reject_unknown(document, _MANIFEST_KEYS, label="mint.integration/v0")
    reject_secrets(document, label="mint.integration/v0")
    if document.get("schema") != SCHEMA_INTEGRATION:
        raise ValueError(f"schema must be {SCHEMA_INTEGRATION}")
    namespace = document.get("namespace")
    name = document.get("name")
    identity = document.get("identity")
    version = document.get("version")
    if not isinstance(namespace, str) or not isinstance(name, str):
        raise ValueError("namespace and name must be strings")
    if identity != f"{namespace}.{name}":
        raise ValueError("identity must equal namespace.name")
    if not isinstance(identity, str) or not _IDENTITY.fullmatch(identity):
        raise ValueError(f"invalid integration identity {identity!r}")
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        raise ValueError(f"invalid integration version {version!r}")
    protocols = document.get("protocolVersions")
    if protocols != ["mint.protocol/v0"]:
        raise ValueError("protocolVersions must be [mint.protocol/v0]")
    capabilities = document.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("capabilities must be a non-empty list")
    for item in capabilities:
        if not isinstance(item, dict) or set(item) != {"id", "version"}:
            raise ValueError("each capability needs id and version only")
        if not _IDENTITY.fullmatch(str(item["id"])):
            raise ValueError(f"invalid capability id {item['id']!r}")
    kinds = document.get("targetKinds")
    phases = document.get("phases")
    if not isinstance(kinds, list) or not kinds or not all(isinstance(item, str) for item in kinds):
        raise ValueError("targetKinds must be a non-empty string list")
    if sorted(kinds) != kinds:
        raise ValueError("targetKinds must be sorted")
    if not isinstance(phases, list) or not phases:
        raise ValueError("phases must be a non-empty list")
    if sorted(phases) != list(phases):
        raise ValueError("phases must be sorted")
    if any(item not in PHASES for item in phases):
        raise ValueError(f"unsupported phase in {phases}")
    if "execute" in phases and document.get("executionSupport") == "none":
        raise ValueError("execute phase requires executionSupport other than none")
    schemas = document.get("configurationSchemas")
    if not isinstance(schemas, list):
        raise ValueError("configurationSchemas must be a list")
    for item in schemas:
        if not isinstance(item, dict) or set(item) != {"digest", "identity"}:
            raise ValueError("configuration schema entries need identity and digest")
        if not _DIGEST.fullmatch(str(item["digest"])):
            raise ValueError("configuration schema digest must be sha256")
    artifact = document.get("artifact")
    if not isinstance(artifact, dict) or set(artifact) != {"digest", "identity"}:
        raise ValueError("artifact needs identity and digest")
    if not _DIGEST.fullmatch(str(artifact["digest"])):
        raise ValueError("artifact digest must be sha256")
    implementation = document.get("implementation")
    if not isinstance(implementation, dict) or set(implementation) != {"executable", "runtime"}:
        raise ValueError("implementation needs runtime and executable")
    for field in ("executable", "runtime"):
        if not isinstance(implementation[field], str) or not implementation[field]:
            raise ValueError(f"implementation.{field} must be a non-empty string")
        reject_absolute_path(implementation[field], label="implementation")
    permissions = document.get("permissions")
    if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
        raise ValueError("permissions must be a string list")
    if document.get("executionSupport") not in EXECUTION_SUPPORT:
        raise ValueError("executionSupport must be none, fake, or privileged")
    provenance = document.get("provenance")
    if provenance != {"deterministic": True}:
        raise ValueError("provenance must be {deterministic: true}")
    compatibility = document.get("compatibility")
    deprecation = document.get("deprecation")
    if not isinstance(compatibility, dict) or not isinstance(deprecation, dict):
        raise ValueError("compatibility and deprecation must be objects")
    reject_unknown(
        compatibility,
        frozenset({"adapterId", "adapterSchema", "adapterVersion", "notes"}),
        label="compatibility",
    )
    reject_unknown(
        deprecation,
        frozenset({"deprecated", "eligibleRemoval", "successor"}),
        label="deprecation",
    )
    if deprecation.get("deprecated") is not False and deprecation.get("deprecated") is not True:
        raise ValueError("deprecation.deprecated must be a boolean")
    return IntegrationManifest(document=document)


def load_manifest_text(text: str) -> IntegrationManifest:
    return parse_manifest(json.loads(text))


def realization_document(
    *,
    capability_id: str,
    capability_version: str,
    target_id: str,
    target_kind: str,
    manifest: IntegrationManifest,
) -> dict[str, Any]:
    body = {
        "capability": {"id": capability_id, "version": capability_version},
        "integration": {
            "artifactDigest": manifest.document["artifact"]["digest"],
            "identity": manifest.identity,
            "manifestDigest": manifest.digest(),
            "version": manifest.version,
        },
        "schema": SCHEMA_REALIZATION,
        "target": {"id": target_id, "kind": target_kind},
    }
    body["digest"] = content_digest({key: value for key, value in body.items() if key != "digest"})
    return body

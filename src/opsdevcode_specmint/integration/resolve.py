"""Deterministic capability-to-integration realization. Fail closed."""

from __future__ import annotations

from dataclasses import dataclass

from opsdevcode_specmint.integration.models import IntegrationManifest, realization_document


@dataclass(frozen=True, slots=True)
class IntegrationRequirement:
    source: str
    version: str
    local: str
    capabilities: tuple[str, ...]
    targets: tuple[str, ...]
    phases: tuple[str, ...]
    realization: str


@dataclass(frozen=True, slots=True)
class ResolutionFailure(Exception):
    code: str
    message: str
    kind: str


def select(
    requirements: tuple[IntegrationRequirement, ...],
    manifests: tuple[IntegrationManifest, ...],
    *,
    capability_id: str,
    capability_version: str,
    target_id: str,
    target_kind: str,
    phase: str,
) -> dict[str, object]:
    indexed = {item.identity: item for item in manifests}
    if len(indexed) != len(manifests):
        raise ResolutionFailure("MINT_INTEGRATION", "duplicate integration identity", "invalid")
    matches: list[IntegrationManifest] = []
    explicit = ""
    for requirement in requirements:
        manifest = indexed.get(requirement.source)
        if manifest is None:
            raise ResolutionFailure(
                "MINT_INTEGRATION",
                f"missing integration {requirement.source}",
                "unavailable",
            )
        if requirement.version != manifest.version:
            raise ResolutionFailure(
                "MINT_INTEGRATION",
                f"incompatible integration version for {requirement.source}",
                "invalid",
            )
        if "mint.protocol/v0" not in manifest.document["protocolVersions"]:
            raise ResolutionFailure(
                "MINT_PROTOCOL",
                f"unsupported protocol for {requirement.source}",
                "unsupported",
            )
        capability_ok = any(
            item["id"] == capability_id and item["version"] == capability_version
            for item in manifest.document["capabilities"]
        )
        if capability_id not in requirement.capabilities or not capability_ok:
            continue
        kinds = manifest.document["targetKinds"]
        if target_kind not in requirement.targets or target_kind not in kinds:
            continue
        if phase not in requirement.phases or phase not in manifest.phases:
            continue
        if requirement.realization and requirement.realization != manifest.identity:
            raise ResolutionFailure(
                "MINT_REALIZATION",
                f"explicit realization {requirement.realization} != {manifest.identity}",
                "invalid",
            )
        explicit = requirement.realization or explicit
        matches.append(manifest)
    if explicit:
        matches = [item for item in matches if item.identity == explicit]
    if not matches:
        raise ResolutionFailure(
            "MINT_REALIZATION",
            f"no integration realizes {capability_id} for {target_kind} phase {phase}",
            "unavailable",
        )
    if len(matches) > 1:
        names = ", ".join(sorted(item.identity for item in matches))
        raise ResolutionFailure(
            "MINT_REALIZATION",
            f"ambiguous integrations {names} for {capability_id}",
            "ambiguous",
        )
    chosen = matches[0]
    if capability_version not in {
        item["version"] for item in chosen.document["capabilities"] if item["id"] == capability_id
    }:
        raise ResolutionFailure(
            "MINT_CAPABILITY",
            f"unsupported capability version {capability_version}",
            "unsupported",
        )
    return realization_document(
        capability_id=capability_id,
        capability_version=capability_version,
        target_id=target_id,
        target_kind=target_kind,
        manifest=chosen,
    )

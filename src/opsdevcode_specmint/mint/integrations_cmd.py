"""mint integrations CLI. Adapter commands remain deprecated aliases."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from opsdevcode_specmint.integration.canonical import canonical_json_bytes
from opsdevcode_specmint.integration.harness import run_conformance
from opsdevcode_specmint.integration.models import parse_manifest, realization_document
from opsdevcode_specmint.integration.reference_server import (
    IDENTITY,
    VERSION,
    artifact_digest,
    manifest_document,
)
from opsdevcode_specmint.integration.resolve import (
    IntegrationRequirement,
    ResolutionFailure,
    select,
)
from opsdevcode_specmint.mint.adapters.registry import builtin_registry
from opsdevcode_specmint.mint.adapters.types import AdapterManifest
from opsdevcode_specmint.mint.errors import coded_error
from opsdevcode_specmint.mint.project import load_manifest

_REMOVAL = "0.2.0"


def deprecation_notice(command: str) -> str:
    return json.dumps(
        {
            "code": "MINT_DEPRECATED_ADAPTER",
            "command": command,
            "eligibleRemoval": _REMOVAL,
            "message": (
                "mint adapters is a deprecated alias of mint integrations for one alpha "
                f"window; removal is eligible at {_REMOVAL}"
            ),
            "severity": "warning",
        },
        sort_keys=True,
    )


def adapter_as_integration(manifest: AdapterManifest) -> dict[str, Any]:
    if manifest.mode != "plan-only" or manifest.mutation != "forbidden":
        raise coded_error(
            "MINT_INTEGRATION",
            f"refuse {manifest.adapter_id}; mint.adapter/v0 mapping is not lossless",
        )
    return {
        "compatibility": {
            "adapterId": manifest.adapter_id,
            "adapterSchema": "mint.adapter/v0",
            "adapterVersion": manifest.version,
            "notes": "lossless plan-only mapping",
        },
        "identity": manifest.adapter_id,
        "schema": "mint.integration/v0",
        "targetKinds": sorted(manifest.target_kinds),
        "version": manifest.version,
    }


def run_integrations(args: Any, *, stdout: TextIO, stderr: TextIO) -> int:
    del stderr
    command = args.integrations_command
    if command == "list":
        payload = {
            "integrations": [
                adapter_as_integration(item) for item in builtin_registry().manifests()
            ],
            "ok": True,
            "reference": manifest_document(),
            "schema": "mint.integration/v0",
        }
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if command == "inspect":
        if args.identity == IDENTITY:
            stdout.write(json.dumps(manifest_document(), indent=2, sort_keys=True) + "\n")
            return 0
        found = None
        for item in builtin_registry().manifests():
            if item.adapter_id == args.identity:
                found = adapter_as_integration(item)
        if found is None:
            raise coded_error(
                "MINT_INTEGRATION",
                f"unknown integration {args.identity}",
            )
        stdout.write(json.dumps(found, indent=2, sort_keys=True) + "\n")
        return 0
    if command == "check":
        text = Path(args.manifest).read_text(encoding="utf-8")
        manifest = parse_manifest(json.loads(text))
        stdout.write(canonical_json_bytes(manifest.document).decode("utf-8"))
        return 0
    if command == "resolve":
        return _resolve(args, stdout=stdout)
    if command == "conformance":
        return _conformance(args, stdout=stdout)
    raise coded_error(
        "MINT_INTEGRATION",
        "mint integrations accepts list, inspect, check, resolve, or conformance",
    )


def _resolve(args: Any, *, stdout: TextIO) -> int:
    project = load_manifest(Path(args.project))
    requirements = tuple(
        IntegrationRequirement(
            source=item.source,
            version=item.version,
            local=item.local,
            capabilities=item.capabilities,
            targets=item.targets,
            phases=item.phases,
            realization=item.realization,
        )
        for item in project.integrations
    )
    if not requirements:
        requirements = (
            IntegrationRequirement(
                source=IDENTITY,
                version=VERSION,
                local="",
                capabilities=(IDENTITY,),
                targets=("local.sandbox", "sandbox"),
                phases=("describe", "evidence", "observe", "plan", "validate", "verify"),
                realization="",
            ),
        )
    manifest = parse_manifest(manifest_document())
    try:
        document = select(
            requirements,
            (manifest,),
            capability_id=args.capability,
            capability_version=args.capability_version,
            target_id=args.target,
            target_kind=args.target_kind,
            phase=args.phase,
        )
    except ResolutionFailure as exc:
        raise coded_error(exc.code, exc.message) from exc
    stdout.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
    return 0


def _conformance(args: Any, *, stdout: TextIO) -> int:
    server = Path(reference_server_path())
    report = run_conformance(
        [sys.executable, str(server)],
        artifact_bytes=server.read_bytes(),
        identity=IDENTITY,
        version=VERSION,
    )
    if args.integration not in {IDENTITY, str(server)}:
        raise coded_error(
            "MINT_INTEGRATION",
            f"conformance reference is {IDENTITY}",
        )
    stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


def reference_server_path() -> str:
    return str(Path(__file__).resolve().parents[1] / "integration" / "reference_server.py")


def reference_realization(target_id: str, target_kind: str) -> dict[str, Any]:
    return realization_document(
        capability_id=IDENTITY,
        capability_version="v1alpha1",
        target_id=target_id,
        target_kind=target_kind,
        manifest=parse_manifest(manifest_document()),
    )


def packaged_artifact_digest() -> str:
    return artifact_digest()

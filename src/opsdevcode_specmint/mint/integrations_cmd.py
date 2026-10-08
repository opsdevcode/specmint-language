"""mint integrations CLI. Adapter commands remain deprecated aliases."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from opsdevcode_specmint.integration.canonical import canonical_json_bytes
from opsdevcode_specmint.integration.harness import load_kit_fixtures, run_integration_test
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
from opsdevcode_specmint.mint.discovery import (
    add_integration,
    inspect_integration,
    refuse_network_source,
    remove_integration,
    search_integrations,
    verify_integrations,
)
from opsdevcode_specmint.mint.errors import MintError, coded_error
from opsdevcode_specmint.mint.project import load_manifest

_COMMANDS = (
    "list",
    "search",
    "inspect",
    "check",
    "resolve",
    "add",
    "remove",
    "verify",
    "conformance",
    "test",
)

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
    if command == "search":
        payload = search_integrations(
            query=getattr(args, "query", "") or "",
            capability=getattr(args, "capability", "") or "",
            target_kind=getattr(args, "target_kind", "") or "",
        )
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if command == "inspect":
        try:
            payload = inspect_integration(args.identity)
        except MintError as exc:
            found = None
            for item in builtin_registry().manifests():
                if item.adapter_id == args.identity:
                    found = adapter_as_integration(item)
            if found is None:
                raise exc
            payload = found
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if command == "check":
        text = Path(args.manifest).read_text(encoding="utf-8")
        manifest = parse_manifest(json.loads(text))
        stdout.write(canonical_json_bytes(manifest.document).decode("utf-8"))
        return 0
    if command == "resolve":
        return _resolve(args, stdout=stdout)
    if command == "add":
        payload = add_integration(
            Path(args.project),
            identity=getattr(args, "identity", "") or "",
            local=getattr(args, "local", "") or "",
        )
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if command == "remove":
        payload = remove_integration(Path(args.project), args.identity)
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if command == "verify":
        payload = verify_integrations(Path(args.project))
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if command in {"conformance", "test"}:
        return _conformance(args, stdout=stdout)
    raise coded_error(
        "MINT_INTEGRATION",
        "mint integrations accepts " + ", ".join(_COMMANDS),
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
    local = getattr(args, "local", "") or ""
    if local:
        report = _local_conformance(local)
        stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return 0
    server = Path(reference_server_path())
    identity = getattr(args, "integration", None) or IDENTITY
    if identity not in {IDENTITY, str(server), ""}:
        raise coded_error(
            "MINT_INTEGRATION",
            f"conformance reference is {IDENTITY}; pass --local for another integration",
        )
    report = run_integration_test(
        [sys.executable, str(server)],
        artifact_bytes=server.read_bytes(),
        identity=IDENTITY,
        version=VERSION,
    )
    stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


def _local_conformance(raw: str) -> dict[str, Any]:
    refuse_network_source(raw, label="test --local")
    path = Path(raw)
    root = path.parent if path.is_file() else path
    manifest_path = (
        root / "mint-integration.json" if path.is_dir() or path.suffix != ".json" else path
    )
    if path.is_file() and path.name.endswith(".json"):
        manifest_path = path
        root = path.parent
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise coded_error(
            "MINT_INTEGRATION",
            "pass --local to a mint-integration.json file or its directory",
        )
    try:
        manifest = parse_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise coded_error(
            "MINT_INTEGRATION",
            f"{manifest_path.name} must be mint.integration/v0 JSON",
        ) from exc
    server = root / "implementation" / "reference_server.py"
    if server.is_symlink() or not server.is_file():
        raise coded_error(
            "MINT_INTEGRATION",
            "local integration artifact must be implementation/reference_server.py",
        )
    fixtures_dir = root / "fixtures"
    fixtures = load_kit_fixtures(directory=fixtures_dir) if fixtures_dir.is_dir() else None
    return run_integration_test(
        [sys.executable, str(server)],
        artifact_bytes=server.read_bytes(),
        identity=manifest.identity,
        version=manifest.version,
        fixtures=fixtures,
    )


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

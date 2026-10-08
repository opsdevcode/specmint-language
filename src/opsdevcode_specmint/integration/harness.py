"""Conformance harness for integration authors. Drives an explicit executable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from opsdevcode_specmint.integration.canonical import SCHEMA_PROTOCOL
from opsdevcode_specmint.integration.framing import ProtocolError
from opsdevcode_specmint.integration.models import parse_manifest
from opsdevcode_specmint.integration.process import invoke, negotiate_request, phase_request

_FIXTURE_DIR = Path(__file__).with_name("fixtures")
_PHASES = ("observe", "plan", "verify", "evidence")


def load_kit_fixtures(*, directory: Path | None = None) -> dict[str, dict[str, Any]]:
    root = directory or _FIXTURE_DIR
    fixtures: dict[str, dict[str, Any]] = {}
    for phase in _PHASES:
        path = root / f"{phase}.json"
        if not path.is_file():
            raise ProtocolError(
                "MINT_INTEGRATION",
                f"missing conformance fixture {phase}.json",
                kind="invalid",
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ProtocolError(
                "MINT_INTEGRATION",
                f"fixture {phase}.json must be a JSON object",
                kind="invalid",
            )
        fixtures[phase] = raw
    return fixtures


def run_conformance(
    argv: list[str],
    *,
    artifact_bytes: bytes,
    identity: str,
    version: str,
    fixtures: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return run_integration_test(
        argv,
        artifact_bytes=artifact_bytes,
        identity=identity,
        version=version,
        fixtures=fixtures,
    )


def run_integration_test(
    argv: list[str],
    *,
    artifact_bytes: bytes,
    identity: str,
    version: str,
    fixtures: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    digest = "sha256:" + hashlib.sha256(artifact_bytes).hexdigest()
    kit = fixtures or load_kit_fixtures()
    negotiated = invoke(
        argv,
        negotiate_request(),
        artifact_digest=digest,
        artifact_bytes=artifact_bytes,
    )
    if "error" in negotiated:
        raise ProtocolError("MINT_PROTOCOL", "negotiation failed", kind="unsupported")
    described = invoke(
        argv,
        phase_request("describe", {}, identity=identity, version=version),
        artifact_digest=digest,
        artifact_bytes=artifact_bytes,
    )
    if "error" in described:
        raise ProtocolError("MINT_PROTOCOL", "describe failed")
    manifest = parse_manifest(described["result"]["payload"])
    if manifest.identity != identity or manifest.version != version:
        raise ProtocolError("MINT_INTEGRATION", "describe identity mismatch", kind="invalid")
    if manifest.document["artifact"]["digest"] != digest:
        raise ProtocolError("MINT_DIGEST", "artifact digest mismatch", kind="invalid")
    phases: list[str] = ["negotiate", "describe"]
    for phase in _PHASES:
        payload = kit.get(phase, {})
        result = invoke(
            argv,
            phase_request(phase, payload, identity=identity, version=version),
            artifact_digest=digest,
            artifact_bytes=artifact_bytes,
        )
        if "error" in result:
            raise ProtocolError("MINT_PHASE", f"{phase} failed", kind="invalid")
        body = result["result"]["payload"]
        if not isinstance(body, dict):
            raise ProtocolError("MINT_PROTOCOL", f"{phase} payload must be an object")
        phases.append(phase)
    refused = invoke(
        argv,
        phase_request("execute", {}, identity=identity, version=version),
        artifact_digest=digest,
        artifact_bytes=artifact_bytes,
    )
    error = refused.get("error")
    if not isinstance(error, dict) or error.get("code") != "MINT_PHASE":
        raise ProtocolError("MINT_PHASE", "execute must fail closed", kind="unsupported")
    return {
        "artifactDigest": digest,
        "executeRefused": True,
        "identity": identity,
        "ok": True,
        "phases": phases,
        "protocol": SCHEMA_PROTOCOL,
        "version": version,
    }

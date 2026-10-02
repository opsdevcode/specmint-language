"""Conformance harness for integration authors. Drives an explicit executable."""

from __future__ import annotations

import hashlib
from typing import Any

from opsdevcode_specmint.integration.canonical import SCHEMA_PROTOCOL
from opsdevcode_specmint.integration.framing import ProtocolError
from opsdevcode_specmint.integration.models import parse_manifest
from opsdevcode_specmint.integration.process import invoke, negotiate_request, phase_request


def run_conformance(
    argv: list[str],
    *,
    artifact_bytes: bytes,
    identity: str,
    version: str,
) -> dict[str, Any]:
    digest = "sha256:" + hashlib.sha256(artifact_bytes).hexdigest()
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
        "identity": identity,
        "ok": True,
        "protocol": SCHEMA_PROTOCOL,
        "version": version,
    }

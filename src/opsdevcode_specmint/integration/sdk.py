"""Public Mint Integration SDK.

Manifest-first identity plus versioned stdio JSON-RPC (`mint.protocol/v0`).
Fail closed. No compiler, network, or provider SDK imports.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from opsdevcode_specmint.integration.canonical import SCHEMA_PROTOCOL
from opsdevcode_specmint.integration.framing import ProtocolError, decode_line, encode_line
from opsdevcode_specmint.integration.models import IntegrationManifest, parse_manifest
from opsdevcode_specmint.integration.reference_server import handle as handle_reference

ProtocolHandler = Callable[[dict[str, Any]], dict[str, Any]]


def load_manifest_file(path: Path) -> IntegrationManifest:
    """Load and validate a mint.integration/v0 manifest from disk."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(
            "MINT_INTEGRATION",
            "manifest must be mint.integration/v0 JSON",
            kind="invalid",
        ) from exc
    try:
        return parse_manifest(document)
    except ValueError as exc:
        raise ProtocolError("MINT_INTEGRATION", str(exc), kind="invalid") from exc


def handle_protocol_document(
    document: dict[str, Any],
    *,
    handler: ProtocolHandler | None = None,
) -> dict[str, Any]:
    """Handle one mint.protocol/v0 JSON-RPC object. Unknown fields fail closed."""
    worker = handler or handle_reference
    return worker(document)


def decode_protocol_line(raw: bytes) -> dict[str, Any]:
    return decode_line(raw if raw.endswith(b"\n") else raw + b"\n")


def encode_protocol_document(document: dict[str, Any]) -> bytes:
    return encode_line(document)


def serve_stdio(handler: ProtocolHandler | None = None) -> int:
    """Read one NDJSON request from stdin and write one response to stdout."""
    from opsdevcode_specmint.integration.reference_server import serve_stdio as serve_reference

    if handler is None:
        return serve_reference()
    import sys

    raw = sys.stdin.buffer.readline()
    try:
        document = decode_protocol_line(raw)
        response = handle_protocol_document(document, handler=handler)
    except ProtocolError as exc:
        response = {
            "error": {"code": exc.code, "data": {"kind": exc.kind}, "message": str(exc)},
            "id": "",
            "jsonrpc": "2.0",
        }
    sys.stdout.buffer.write(encode_protocol_document(response))
    return 0


__all__ = [
    "SCHEMA_PROTOCOL",
    "ProtocolHandler",
    "decode_protocol_line",
    "encode_protocol_document",
    "handle_protocol_document",
    "load_manifest_file",
    "serve_stdio",
]

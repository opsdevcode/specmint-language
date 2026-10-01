"""Out-of-process mint.protocol/v0 client. Explicit argv, minimal environment."""

from __future__ import annotations

import hashlib
import os
import subprocess
from typing import Any

from opsdevcode_specmint.integration.canonical import SCHEMA_PROTOCOL, content_digest
from opsdevcode_specmint.integration.framing import (
    MAX_MESSAGE_BYTES,
    ProtocolError,
    decode_line,
    encode_line,
    failure,
    parse_response,
    success,
)

MAX_STDERR_BYTES = 8_192
DEFAULT_TIMEOUT_SECONDS = 2.0
_ENV_ALLOWLIST = ("PATH", "LANG", "LC_ALL")


def minimal_environment() -> dict[str, str]:
    env = {key: os.environ[key] for key in _ENV_ALLOWLIST if os.environ.get(key)}
    env["LANG"] = env.get("LANG") or "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def invoke(
    argv: list[str],
    request: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    artifact_digest: str | None = None,
    artifact_bytes: bytes | None = None,
) -> dict[str, Any]:
    if not argv or any(not isinstance(item, str) or item == "" for item in argv):
        raise ProtocolError("MINT_PROTOCOL", "subprocess argv must be explicit non-empty strings")
    if artifact_bytes is not None and artifact_digest is not None:
        actual = "sha256:" + hashlib.sha256(artifact_bytes).hexdigest()
        if actual != artifact_digest:
            raise ProtocolError(
                "MINT_DIGEST", "integration artifact digest mismatch", kind="invalid"
            )
    payload = encode_line(request)
    try:
        completed = subprocess.run(
            argv,
            input=payload,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=minimal_environment(),
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProtocolError(
            "MINT_PROTOCOL",
            "integration process exceeded the timeout and was terminated",
            kind="unavailable",
        ) from exc
    if completed.returncode != 0:
        raise ProtocolError(
            "MINT_PROTOCOL",
            f"integration process exited {completed.returncode}",
            kind="unavailable",
        )
    if len(completed.stderr) > MAX_STDERR_BYTES:
        raise ProtocolError("MINT_PROTOCOL", "integration stderr exceeded the bound")
    stdout = completed.stdout
    if len(stdout) > MAX_MESSAGE_BYTES:
        raise ProtocolError("MINT_PROTOCOL", "integration response exceeds the size bound")
    if stdout.count(b"\n") != 1:
        raise ProtocolError("MINT_PROTOCOL", "stdout pollution or missing protocol message")
    document = decode_line(stdout if stdout.endswith(b"\n") else stdout + b"\n")
    return parse_response(document)


def negotiate_request() -> dict[str, Any]:
    return {
        "id": "negotiate",
        "jsonrpc": "2.0",
        "method": "negotiate",
        "params": {"protocolVersions": [SCHEMA_PROTOCOL], "schema": "mint.protocol.negotiate/v0"},
    }


def phase_request(
    phase: str, payload: dict[str, Any], *, identity: str, version: str
) -> dict[str, Any]:
    return {
        "id": phase,
        "jsonrpc": "2.0",
        "method": "phase",
        "params": {
            "integration": {"identity": identity, "version": version},
            "payload": payload,
            "phase": phase,
            "protocol": SCHEMA_PROTOCOL,
            "schema": "mint.protocol.request/v0",
        },
    }


def result_digest(result: dict[str, Any]) -> str:
    return content_digest(result)


__all__ = [
    "failure",
    "invoke",
    "minimal_environment",
    "negotiate_request",
    "phase_request",
    "success",
]

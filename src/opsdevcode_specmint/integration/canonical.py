"""Deterministic JSON and content digests. Stdlib only; no compiler imports."""

from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA_INTEGRATION = "mint.integration/v0"
SCHEMA_PROTOCOL = "mint.protocol/v0"
SCHEMA_REQUEST = "mint.protocol.request/v0"
SCHEMA_RESULT = "mint.protocol.result/v0"
SCHEMA_REALIZATION = "mint.realization/v0"
SCHEMA_OBSERVATION = "mint.observation/v0"
SCHEMA_OPERATION = "mint.operation/v0"
SCHEMA_VERIFICATION = "mint.verification/v0"
SCHEMA_EVIDENCE = "mint.evidence/v0"
PROTOCOL_VERSION = SCHEMA_PROTOCOL

PHASES = (
    "describe",
    "validate",
    "observe",
    "plan",
    "verify",
    "recover",
    "evidence",
    "execute",
)
NONPRIVILEGED_PHASES = (
    "describe",
    "validate",
    "observe",
    "plan",
    "verify",
    "recover",
    "evidence",
)
EXECUTION_SUPPORT = ("none", "fake", "privileged")
SECRET_KEYS = frozenset(
    {
        "access_key",
        "api_key",
        "authorization",
        "credential",
        "password",
        "pat",
        "private_key",
        "secret",
        "token",
    }
)


def canonical_json_bytes(mapping: Any) -> bytes:
    payload = json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"{payload}\n".encode()


def digest_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def content_digest(mapping: Any) -> str:
    return digest_bytes(canonical_json_bytes(mapping))


def reject_unknown(document: dict[str, Any], allowed: frozenset[str], *, label: str) -> None:
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise ValueError(f"{label} contains unknown fields {unknown}")


def reject_secrets(value: Any, *, label: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS:
                raise ValueError(f"{label} contains a secret-shaped field {key}")
            reject_secrets(item, label=label)
    elif isinstance(value, list):
        for item in value:
            reject_secrets(item, label=label)


def reject_absolute_path(text: str, *, label: str) -> None:
    if text.startswith("/") or (len(text) > 2 and text[1] == ":"):
        raise ValueError(f"{label} contains an absolute path")

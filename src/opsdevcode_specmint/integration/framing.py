"""Newline-delimited JSON-RPC framing for mint.protocol/v0."""

from __future__ import annotations

import json
from typing import Any

from opsdevcode_specmint.integration.canonical import reject_secrets, reject_unknown

MAX_MESSAGE_BYTES = 262_144
_REQUEST_KEYS = frozenset({"id", "jsonrpc", "method", "params"})
_RESPONSE_KEYS = frozenset({"id", "jsonrpc", "result"})
_ERROR_RESPONSE_KEYS = frozenset({"error", "id", "jsonrpc"})


class ProtocolError(Exception):
    def __init__(self, code: str, message: str, *, kind: str = "invalid") -> None:
        self.code = code
        self.kind = kind
        super().__init__(message)


def encode_line(document: dict[str, Any]) -> bytes:
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    raw = (payload + "\n").encode()
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ProtocolError("MINT_PROTOCOL", "protocol message exceeds the size bound")
    return raw


def decode_line(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ProtocolError("MINT_PROTOCOL", "protocol message exceeds the size bound")
    if not raw.endswith(b"\n"):
        raise ProtocolError("MINT_PROTOCOL", "protocol message is not newline delimited")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("MINT_PROTOCOL", "malformed protocol JSON") from exc
    if not isinstance(document, dict):
        raise ProtocolError("MINT_PROTOCOL", "protocol message must be a JSON object")
    try:
        reject_secrets(document, label="protocol message")
    except ValueError as exc:
        raise ProtocolError("MINT_PERMISSION", str(exc), kind="invalid") from exc
    return document


def parse_request(document: dict[str, Any]) -> dict[str, Any]:
    reject_unknown(document, _REQUEST_KEYS, label="request")
    if document.get("jsonrpc") != "2.0":
        raise ProtocolError("MINT_PROTOCOL", "jsonrpc must be 2.0", kind="unsupported")
    if not isinstance(document.get("id"), str) or not document["id"]:
        raise ProtocolError("MINT_PROTOCOL", "request id must be a non-empty string")
    if document.get("method") not in {"negotiate", "phase"}:
        raise ProtocolError("MINT_PROTOCOL", "unknown method", kind="unknown")
    params = document.get("params")
    if not isinstance(params, dict):
        raise ProtocolError("MINT_PROTOCOL", "params must be an object")
    return document


def success(request_id: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"id": request_id, "jsonrpc": "2.0", "result": result}


def failure(request_id: str, code: str, message: str, *, kind: str) -> dict[str, Any]:
    return {
        "error": {"code": code, "data": {"kind": kind}, "message": message},
        "id": request_id,
        "jsonrpc": "2.0",
    }


def parse_response(document: dict[str, Any]) -> dict[str, Any]:
    keys = set(document)
    if keys == _RESPONSE_KEYS:
        reject_unknown(document, _RESPONSE_KEYS, label="response")
    elif keys == _ERROR_RESPONSE_KEYS:
        reject_unknown(document, _ERROR_RESPONSE_KEYS, label="response")
    else:
        raise ProtocolError("MINT_PROTOCOL", "response has unknown or missing fields")
    if document.get("jsonrpc") != "2.0":
        raise ProtocolError("MINT_PROTOCOL", "jsonrpc must be 2.0", kind="unsupported")
    return document

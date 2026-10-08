"""JSON and human Mint diagnostics. No TTY guessing; no host paths or secrets."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from opsdevcode_specmint.mint.errors import MintDiagnostic

OUTPUT_JSON = "json"
OUTPUT_HUMAN = "human"
OUTPUT_FORMATS = frozenset({OUTPUT_JSON, OUTPUT_HUMAN})
DEFAULT_OUTPUT_FORMAT = OUTPUT_JSON

_HOST_PATH = re.compile(
    r"(?:(?:/Users|/home|/var|/private/var|/tmp|/opt)/[^\s\"',;]+|[A-Za-z]:\\[^\s\"',;]+)"
)
_SECRET = re.compile(r"(?i)(?:ghp_|gho_|github_pat_|glpat-|xox[baprs]-|sk-|AKIA)[A-Za-z0-9_\-]+")
_CREDENTIAL_FRAGMENT = re.compile(
    r"(?i)\b(?:password|secret|token|private_key|access_key|credential)\b\s*[:=]\s*\S+"
)


def display_path(path: Path | str) -> str:
    """Show a caller-declared relative name; never a host absolute path."""
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return candidate.name or str(candidate)
    return str(candidate)


def sanitize_text(text: str) -> str:
    redacted = _SECRET.sub("<redacted>", text)
    redacted = _CREDENTIAL_FRAGMENT.sub("<redacted>", redacted)
    return _HOST_PATH.sub(lambda match: Path(match.group(0)).name, redacted)


def diagnostic_payload(diagnostic: MintDiagnostic) -> dict[str, Any]:
    start_line = diagnostic.line
    start_column = diagnostic.column
    end_line = diagnostic.end_line
    end_column = diagnostic.end_column
    if start_line is not None and start_column is not None:
        if end_line is None:
            end_line = start_line
        if end_column is None:
            end_column = start_column + 1
    range_payload: dict[str, Any] | None = None
    if start_line is not None and start_column is not None:
        range_payload = {
            "end": {
                "column": end_column,
                "line": end_line,
                "offset": diagnostic.end_offset,
            },
            "start": {
                "column": start_column,
                "line": start_line,
                "offset": diagnostic.start_offset,
            },
        }
    snapshot = diagnostic.snapshot
    return {
        "ok": False,
        "code": diagnostic.code,
        "column": diagnostic.column,
        "line": diagnostic.line,
        "message": sanitize_text(diagnostic.message),
        "range": range_payload,
        "rendered": sanitize_text(render_human(diagnostic)).rstrip("\n"),
        "snapshot": dict(snapshot) if snapshot else None,
        "unit": diagnostic.unit,
    }


def render_human(diagnostic: MintDiagnostic) -> str:
    where = ""
    if diagnostic.line is not None and diagnostic.column is not None:
        end_line = diagnostic.end_line or diagnostic.line
        end_column = diagnostic.end_column or (diagnostic.column + 1)
        span = f"{diagnostic.line}:{diagnostic.column}-{end_line}:{end_column}"
        where = f":{diagnostic.unit}:{span}" if diagnostic.unit else f":{span}"
    lines = [sanitize_text(f"{diagnostic.code}{where}: {diagnostic.message}")]
    if diagnostic.snapshot:
        items = " ".join(f"{key}={diagnostic.snapshot[key]}" for key in sorted(diagnostic.snapshot))
        lines.append(f"  snapshot: {items}")
    return "\n".join(lines) + "\n"


def render_diagnostic(diagnostic: MintDiagnostic, *, output_format: str) -> str:
    fmt = normalize_output_format(output_format)
    if fmt == OUTPUT_HUMAN:
        return render_human(diagnostic)
    return json.dumps(diagnostic_payload(diagnostic), indent=2, sort_keys=True) + "\n"


def render_payload(payload: Mapping[str, Any], *, output_format: str) -> str:
    fmt = normalize_output_format(output_format)
    body = _sanitize_payload(dict(payload))
    if fmt == OUTPUT_HUMAN:
        return _render_human_payload(body)
    return json.dumps(body, indent=2, sort_keys=True) + "\n"


def normalize_output_format(value: str | None) -> str:
    fmt = DEFAULT_OUTPUT_FORMAT if value is None else value
    if fmt not in OUTPUT_FORMATS:
        raise ValueError(
            "set --output-format to json or human; output format is not inferred from the TTY"
        )
    return fmt


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in payload.items():
        out[key] = _sanitize_value(value)
    return out


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return _sanitize_payload(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value]
    return value


def _render_human_payload(payload: Mapping[str, Any]) -> str:
    lines: list[str] = []
    for key in sorted(payload):
        value = payload[key]
        if key == "checks" and isinstance(value, list):
            lines.append("checks:")
            for item in value:
                if not isinstance(item, dict):
                    continue
                status = "skip" if item.get("skipped") else ("ok" if item.get("ok") else "fail")
                ident = str(item.get("id", "check"))
                message = str(item.get("message", ""))
                lines.append(f"  {ident}: {status} — {message}")
            continue
        if key == "templates" and isinstance(value, list):
            lines.append("templates:")
            for item in value:
                if not isinstance(item, dict):
                    continue
                ident = str(item.get("id", ""))
                suffix = " (default)" if item.get("default") else ""
                summary = str(item.get("summary", ""))
                lines.append(f"  {ident}{suffix}: {summary}")
            continue
        if isinstance(value, dict | list):
            lines.append(f"{key}: {json.dumps(value, sort_keys=True)}")
            continue
        rendered = "true" if value is True else "false" if value is False else value
        lines.append(f"{key}: {rendered}")
    return "\n".join(lines) + "\n"

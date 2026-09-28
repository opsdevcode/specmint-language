"""Host identity compile for the public language extract. CUE is not included."""

from __future__ import annotations

import json
from typing import Any

from opsdevcode_specmint.automation import is_automation_document
from opsdevcode_specmint.contracts import reject_unsupported_spec
from opsdevcode_specmint.errors import DocumentParseError


def compile_specification(document: dict[str, Any]) -> dict[str, Any]:
    reject_unsupported_spec(document)
    if not is_automation_document(document) and document.get("kind") != "DeliverySpecification":
        raise DocumentParseError("unsupported document kind for language extract compile")
    closed = json.loads(json.dumps(document, sort_keys=True))
    if not isinstance(closed, dict):
        raise DocumentParseError("compile produced a non-object document")
    return closed


def validate_specification(document: dict[str, Any]) -> dict[str, Any]:
    compiled = compile_specification(document)
    return {
        "valid": True,
        "kind": compiled.get("kind"),
        "api_version": compiled.get("apiVersion"),
        "id": compiled.get("metadata", {}).get("id")
        if isinstance(compiled.get("metadata"), dict)
        else None,
        "issues": [],
    }


def inspect_artifact(document: dict[str, Any]) -> dict[str, Any]:
    compiled = compile_specification(document)
    return {"artifact": compiled}

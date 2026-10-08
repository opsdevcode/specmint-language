from __future__ import annotations

import json
from pathlib import Path

from opsdevcode_specmint.integration.harness import run_integration_test
from opsdevcode_specmint.integration.reference_server import IDENTITY, VERSION, artifact_digest
from opsdevcode_specmint.integration.sdk import (
    handle_protocol_document,
    load_manifest_file,
)
from test_mint_cli import _run

_SERVER = Path(__file__).resolve().parents[1] / "src" / "opsdevcode_specmint" / "integration"
_EXAMPLE = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "integrations"
    / "local-sandbox"
    / "mint-integration.json"
)


def test_load_manifest_file_round_trip() -> None:
    manifest = load_manifest_file(_EXAMPLE)
    assert manifest.identity == IDENTITY
    assert "execute" not in manifest.phases
    assert manifest.execution_support == "fake"


def test_handle_protocol_observe_and_execute_refused() -> None:
    observed = handle_protocol_document(
        {
            "id": "observe",
            "jsonrpc": "2.0",
            "method": "phase",
            "params": {
                "integration": {"identity": IDENTITY, "version": VERSION},
                "payload": {
                    "capability": {"id": IDENTITY, "version": "v1alpha1"},
                    "target": {"id": "fixture-alpha", "kind": "local.sandbox"},
                },
                "phase": "observe",
                "protocol": "mint.protocol/v0",
                "schema": "mint.protocol.request/v0",
            },
        }
    )
    assert observed["result"]["ok"] is True
    assert observed["result"]["payload"]["schema"] == "mint.observation/v0"
    refused = handle_protocol_document(
        {
            "id": "execute",
            "jsonrpc": "2.0",
            "method": "phase",
            "params": {
                "integration": {"identity": IDENTITY, "version": VERSION},
                "payload": {},
                "phase": "execute",
                "protocol": "mint.protocol/v0",
                "schema": "mint.protocol.request/v0",
            },
        }
    )
    assert refused["error"]["code"] == "MINT_PHASE"


def test_unknown_protocol_field_fails_closed() -> None:
    result = handle_protocol_document(
        {
            "extra": True,
            "id": "n",
            "jsonrpc": "2.0",
            "method": "negotiate",
            "params": {},
        }
    )
    assert result["error"]["code"] == "MINT_PROTOCOL"


def test_integrations_test_cli_runs_kit() -> None:
    import sys

    report = run_integration_test(
        [sys.executable, str(_SERVER / "reference_server.py")],
        artifact_bytes=(_SERVER / "reference_server.py").read_bytes(),
        identity=IDENTITY,
        version=VERSION,
    )
    assert report["ok"] is True
    assert report["executeRefused"] is True
    assert report["phases"] == [
        "negotiate",
        "describe",
        "observe",
        "plan",
        "verify",
        "evidence",
    ]
    assert report["artifactDigest"] == artifact_digest()
    code, out, err = _run(["integrations", "test", IDENTITY])
    assert code == 0, err
    body = json.loads(out)
    assert body["ok"] is True
    assert body["executeRefused"] is True
    alias, alias_out, alias_err = _run(["integrations", "conformance", IDENTITY])
    assert alias == 0, alias_err
    assert json.loads(alias_out)["phases"] == body["phases"]


def test_integrations_test_default_identity() -> None:
    code, out, err = _run(["integrations", "test"])
    assert code == 0, err
    body = json.loads(out)
    assert body["identity"] == IDENTITY
    assert "apply" not in _run([])[1].split()

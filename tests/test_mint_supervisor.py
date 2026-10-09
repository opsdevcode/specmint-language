from __future__ import annotations

import sys
from pathlib import Path

from opsdevcode_specmint.integration.reference_server import IDENTITY, VERSION, artifact_digest
from opsdevcode_specmint.integration.supervisor import ProcessSupervisor

SERVER = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "opsdevcode_specmint"
    / "integration"
    / "reference_server.py"
)


def test_supervisor_runs_one_shot_and_returns_idle() -> None:
    supervisor = ProcessSupervisor(
        [sys.executable, str(SERVER)],
        identity=IDENTITY,
        version=VERSION,
        artifact_digest=artifact_digest(),
        artifact_bytes=SERVER.read_bytes(),
    )
    assert supervisor.status().running is False
    assert supervisor.status().message == "idle"
    negotiated = supervisor.negotiate()
    assert "result" in negotiated
    described = supervisor.invoke_phase("describe", {})
    assert described["result"]["payload"]["identity"] == IDENTITY
    status = supervisor.status()
    assert status.running is False
    assert status.pid is None
    assert status.ok is True
    assert status.phase == "describe"
    assert status.last_digest.startswith("sha256:")
    refused = supervisor.invoke_phase("execute", {})
    assert refused["error"]["code"] == "MINT_PHASE"
    assert supervisor.status().ok is False
    assert supervisor.status().running is False
    assert supervisor.status().pid is None


def test_supervisor_requires_explicit_argv() -> None:
    from opsdevcode_specmint.integration.framing import ProtocolError

    try:
        ProcessSupervisor(
            [],
            identity=IDENTITY,
            version=VERSION,
            artifact_digest=artifact_digest(),
        )
    except ProtocolError as exc:
        assert "argv must be explicit" in str(exc)
        return
    raise AssertionError("empty argv must fail closed")

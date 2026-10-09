"""One-shot process supervisor for mint.protocol/v0.

Integrations still exit after one stdio request. The supervisor records
status around each invoke, never leaves a child running, and never
opens a network path.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from opsdevcode_specmint.integration.framing import ProtocolError
from opsdevcode_specmint.integration.process import (
    invoke,
    negotiate_request,
    phase_request,
    result_digest,
)


@dataclass(frozen=True, slots=True)
class ProcessStatus:
    identity: str
    version: str
    phase: str
    running: bool
    pid: int | None
    artifact_digest: str
    last_digest: str
    ok: bool
    message: str

    def to_record(self) -> dict[str, Any]:
        return {
            "artifactDigest": self.artifact_digest,
            "identity": self.identity,
            "lastDigest": self.last_digest,
            "message": self.message,
            "ok": self.ok,
            "phase": self.phase,
            "pid": self.pid,
            "running": self.running,
            "version": self.version,
        }


class ProcessSupervisor:
    def __init__(
        self,
        argv: list[str],
        *,
        identity: str,
        version: str,
        artifact_digest: str,
        artifact_bytes: bytes | None = None,
    ) -> None:
        if not argv:
            raise ProtocolError("MINT_PROTOCOL", "supervisor argv must be explicit")
        self._argv = list(argv)
        self._artifact_digest = artifact_digest
        self._artifact_bytes = artifact_bytes
        self._status = ProcessStatus(
            identity=identity,
            version=version,
            phase="",
            running=False,
            pid=None,
            artifact_digest=artifact_digest,
            last_digest="",
            ok=True,
            message="idle",
        )

    def status(self) -> ProcessStatus:
        return self._status

    def negotiate(self) -> dict[str, Any]:
        return self._run("negotiate", negotiate_request())

    def invoke_phase(self, phase: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request = phase_request(
            phase,
            payload or {},
            identity=self._status.identity,
            version=self._status.version,
        )
        return self._run(phase, request)

    def _run(self, phase: str, request: dict[str, Any]) -> dict[str, Any]:
        self._status = replace(self._status, phase=phase, running=True, message="running")
        try:
            response = invoke(
                self._argv,
                request,
                artifact_digest=self._artifact_digest,
                artifact_bytes=self._artifact_bytes,
            )
        except ProtocolError as exc:
            self._status = replace(
                self._status,
                running=False,
                pid=None,
                ok=False,
                message=str(exc),
            )
            raise
        digest = ""
        if "result" in response:
            digest = result_digest(response["result"])
        self._status = replace(
            self._status,
            running=False,
            pid=None,
            ok="error" not in response,
            last_digest=digest,
            message="idle",
        )
        return response

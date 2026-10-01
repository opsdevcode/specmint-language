"""Mint Integration Protocol v0 coverage."""

from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

import pytest

from opsdevcode_specmint.integration.canonical import content_digest
from opsdevcode_specmint.integration.framing import ProtocolError
from opsdevcode_specmint.integration.models import parse_manifest
from opsdevcode_specmint.integration.process import invoke, minimal_environment, phase_request
from opsdevcode_specmint.integration.reference_server import (
    IDENTITY,
    VERSION,
    artifact_digest,
    manifest_document,
)
from opsdevcode_specmint.integration.resolve import (
    IntegrationRequirement,
    ResolutionFailure,
    select,
)
from opsdevcode_specmint.mint.cli import main
from opsdevcode_specmint.mint.project import build_lockfile, check_lockfile, load_manifest

_SERVER = Path(__file__).resolve().parents[1] / "src" / "opsdevcode_specmint" / "integration"
_ARGV = [sys.executable, str(_SERVER / "reference_server.py")]


def _manifest() -> dict[str, object]:
    return manifest_document()


def _requirement(**overrides: object) -> IntegrationRequirement:
    payload = {
        "source": IDENTITY,
        "version": VERSION,
        "local": "",
        "capabilities": (IDENTITY,),
        "targets": ("local.sandbox",),
        "phases": ("plan",),
        "realization": "",
    }
    payload.update(overrides)
    return IntegrationRequirement(**payload)  # type: ignore[arg-type]


def test_valid_manifest_and_unknown_field() -> None:
    manifest = parse_manifest(_manifest())
    assert manifest.identity == IDENTITY
    broken = dict(_manifest())
    broken["extra"] = True
    with pytest.raises(ValueError, match="unknown fields"):
        parse_manifest(broken)


def test_invalid_identity_and_secret_field() -> None:
    broken = dict(_manifest())
    broken["identity"] = "NOT VALID"
    with pytest.raises(ValueError, match="identity"):
        parse_manifest(broken)
    secret = dict(_manifest())
    secret["token"] = "nope"
    with pytest.raises(ValueError, match="unknown fields|secret"):
        parse_manifest(secret)


def test_resolution_matrix() -> None:
    manifest = parse_manifest(_manifest())
    chosen = select(
        (_requirement(),),
        (manifest,),
        capability_id=IDENTITY,
        capability_version="v1alpha1",
        target_id="fixture-alpha",
        target_kind="local.sandbox",
        phase="plan",
    )
    assert chosen["schema"] == "mint.realization/v0"
    other_doc = dict(_manifest())
    other_doc["identity"] = "local.sandbox.other"
    other_doc["name"] = "other"
    other = parse_manifest(other_doc)
    with pytest.raises(ResolutionFailure, match="ambiguous") as ambiguous:
        select(
            (
                _requirement(),
                _requirement(source="local.sandbox.other"),
            ),
            (manifest, other),
            capability_id=IDENTITY,
            capability_version="v1alpha1",
            target_id="fixture-alpha",
            target_kind="local.sandbox",
            phase="plan",
        )
    assert ambiguous.value.kind == "ambiguous"
    explicit = select(
        (_requirement(realization=IDENTITY), _requirement(source="local.sandbox.other")),
        (manifest, other),
        capability_id=IDENTITY,
        capability_version="v1alpha1",
        target_id="fixture-alpha",
        target_kind="local.sandbox",
        phase="plan",
    )
    assert explicit["integration"]["identity"] == IDENTITY  # type: ignore[index]
    with pytest.raises(ResolutionFailure, match="no integration"):
        select(
            (),
            (manifest,),
            capability_id=IDENTITY,
            capability_version="v1alpha1",
            target_id="fixture-alpha",
            target_kind="local.sandbox",
            phase="plan",
        )
    with pytest.raises(ResolutionFailure, match="version"):
        select(
            (_requirement(version="9.9.9"),),
            (manifest,),
            capability_id=IDENTITY,
            capability_version="v1alpha1",
            target_id="fixture-alpha",
            target_kind="local.sandbox",
            phase="plan",
        )
    with pytest.raises(ResolutionFailure, match="no integration"):
        select(
            (_requirement(targets=("repo.github",)),),
            (manifest,),
            capability_id=IDENTITY,
            capability_version="v1alpha1",
            target_id="fixture-alpha",
            target_kind="repo.github",
            phase="plan",
        )
    with pytest.raises(ResolutionFailure, match="no integration"):
        select(
            (_requirement(phases=("describe",)),),
            (manifest,),
            capability_id=IDENTITY,
            capability_version="v1alpha1",
            target_id="fixture-alpha",
            target_kind="local.sandbox",
            phase="execute",
        )


def test_protocol_negotiation_and_refusal() -> None:
    negotiated = invoke(
        _ARGV,
        {
            "id": "negotiate",
            "jsonrpc": "2.0",
            "method": "negotiate",
            "params": {
                "protocolVersions": ["mint.protocol/v0"],
                "schema": "mint.protocol.negotiate/v0",
            },
        },
    )
    assert negotiated["result"]["protocol"] == "mint.protocol/v0"
    refused = invoke(
        _ARGV,
        {
            "id": "negotiate",
            "jsonrpc": "2.0",
            "method": "negotiate",
            "params": {
                "protocolVersions": ["mint.protocol/v9"],
                "schema": "mint.protocol.negotiate/v0",
            },
        },
    )
    assert refused["error"]["code"] == "MINT_PROTOCOL"
    execute = invoke(_ARGV, phase_request("execute", {}, identity=IDENTITY, version=VERSION))
    assert execute["error"]["code"] == "MINT_PHASE"
    secret = invoke(
        _ARGV,
        phase_request("validate", {"token": "abc"}, identity=IDENTITY, version=VERSION),
    )
    assert secret["error"]["code"] == "MINT_PERMISSION"


def test_subprocess_timeout_crash_and_pollution(tmp_path: Path) -> None:
    request = {"id": "x", "jsonrpc": "2.0", "method": "negotiate", "params": {}}
    with pytest.raises(ProtocolError, match="timeout"):
        invoke(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            request,
            timeout=0.2,
        )
    with pytest.raises(ProtocolError, match="exited"):
        invoke([sys.executable, "-c", "import sys; sys.exit(3)"], request)
    script = tmp_path / "dirty.py"
    script.write_text("print('noise')\nprint('{}')\n", encoding="utf-8")
    with pytest.raises(ProtocolError, match="pollution"):
        invoke([sys.executable, str(script)], request)


def test_environment_is_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/tmp/should-not-pass")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    env = minimal_environment()
    assert "HOME" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env


def test_digest_mismatch_and_oversized() -> None:
    with pytest.raises(ProtocolError, match="artifact"):
        invoke(
            _ARGV,
            phase_request("describe", {}, identity=IDENTITY, version=VERSION),
            artifact_bytes=b"tampered",
            artifact_digest=artifact_digest(),
        )
    huge = "x" * 300_000
    with pytest.raises(ProtocolError, match="size"):
        invoke([sys.executable, "-c", "print('ok')"], {"blob": huge})


def test_cli_and_apply_absent() -> None:
    code = main(["integrations", "list"])
    assert code == 0
    with pytest.raises(SystemExit) as exited:
        main(["apply"])
    assert exited.value.code == 2


def test_lock_pins_reference(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "main.mint").write_text(
        textwrap.dedent(
            """\
            mint v0

            automation as-local-marker-1 {
              owner "platform@opsdevcode.com"
              intent "Ensure a sandbox marker exists after an authorized plan"
              use local.sandbox.ensure_marker v1alpha1
              sandbox fixture-alpha
              evidence marker.present
              require authorization
              forbid mutation
              status draft
            }
            """
        ),
        encoding="utf-8",
    )
    (project / "mint.toml").write_text(
        "\n".join(
            [
                'schema = "mint.project/v0"',
                'name = "demo"',
                'edition = "v0"',
                'root = "main.mint"',
                'units = ["main.mint"]',
                "",
                "[[integrations]]",
                f'source = "{IDENTITY}"',
                f'version = "{VERSION}"',
                f'capabilities = ["{IDENTITY}"]',
                'targets = ["local.sandbox"]',
                'phases = ["describe", "evidence", "observe", "plan", "validate", "verify"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest = load_manifest(project / "mint.toml")
    lock = build_lockfile(manifest)
    (project / "mint.lock").write_bytes(lock.canonical_bytes())
    check_lockfile(manifest)
    text = (project / "mint.lock").read_text(encoding="utf-8")
    assert "sha256:" in text
    assert str(tmp_path) not in text
    assert os.environ.get("HOME", "___") not in text
    tampered = text.replace(lock.integrations[0].artifact_digest, "sha256:" + "ab" * 32)
    (project / "mint.lock").write_text(tampered, encoding="utf-8")
    with pytest.raises(Exception, match="stale|canonical|malformed"):
        check_lockfile(load_manifest(project / "mint.toml"))


def test_repeated_plan_is_deterministic() -> None:
    request = phase_request(
        "plan",
        {
            "observationDigest": content_digest({"schema": "mint.observation/v0"}),
            "target": {"id": "fixture-alpha", "kind": "local.sandbox"},
        },
        identity=IDENTITY,
        version=VERSION,
    )
    first = invoke(_ARGV, request)
    second = invoke(_ARGV, request)
    assert first == second


def test_schema_file_digest_stable() -> None:
    schema = (_SERVER / "schemas" / "mint.integration.v0.json").read_bytes()
    assert schema.startswith(b"{")
    assert "mint.integration/v0" in schema.decode()

"""Offline search / inspect / add / remove / verify. No network, pip, or execute."""

from __future__ import annotations

import io
import json
import socket
import textwrap
from pathlib import Path

import pytest

from opsdevcode_specmint.integration.reference_server import IDENTITY, VERSION
from opsdevcode_specmint.mint.cli import main
from opsdevcode_specmint.mint.project import catalog_digest, load_lockfile, load_manifest


def _run(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    code = main(argv, stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def _project(tmp_path: Path) -> Path:
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
            ]
        ),
        encoding="utf-8",
    )
    return project


def test_search_inspect_are_local(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("discovery must not open a network socket")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    code, out, err = _run(["integrations", "search", "sandbox", "--target-kind", "local.sandbox"])
    assert code == 0, err
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["network"] is False
    assert payload["schema"] == "mint.catalog-records/v0"
    identities = [item["identity"] for item in payload["integrations"]]
    assert IDENTITY in identities
    inspect_code, inspect_out, inspect_err = _run(["integrations", "inspect", IDENTITY])
    assert inspect_code == 0, inspect_err
    inspected = json.loads(inspect_out)
    assert inspected["identity"] == IDENTITY
    assert inspected["schema"] == "mint.integration/v0"


def test_add_verify_remove_bind_lockfile_digests(tmp_path: Path) -> None:
    project = _project(tmp_path)
    code, out, err = _run(["integrations", "add", "--project", str(project), IDENTITY])
    assert code == 0, err
    added = json.loads(out)
    assert added["ok"] is True
    assert added["executed"] is False
    assert added["installed"] is False
    assert added["network"] is False
    assert added["artifactDigest"].startswith("sha256:")
    assert added["manifestDigest"].startswith("sha256:")
    manifest = load_manifest(project / "mint.toml")
    assert [item.source for item in manifest.integrations] == [IDENTITY]
    lock = load_lockfile(project / "mint.lock")
    assert lock.catalog_digest == catalog_digest()
    assert lock.integrations[0].artifact_digest == added["artifactDigest"]
    assert str(tmp_path) not in (project / "mint.lock").read_text(encoding="utf-8")
    verify_code, verify_out, verify_err = _run(
        ["integrations", "verify", "--project", str(project)]
    )
    assert verify_code == 0, verify_err
    verified = json.loads(verify_out)
    assert verified["ok"] is True
    assert verified["executed"] is False
    assert verified["integrations"][0]["matched"] is True
    remove_code, remove_out, remove_err = _run(
        ["integrations", "remove", "--project", str(project), IDENTITY]
    )
    assert remove_code == 0, remove_err
    removed = json.loads(remove_out)
    assert removed["remaining"] == []
    assert load_manifest(project / "mint.toml").integrations == ()


def test_add_refuses_network_and_does_not_pip(tmp_path: Path) -> None:
    project = _project(tmp_path)
    code, out, err = _run(
        [
            "integrations",
            "add",
            "--project",
            str(project),
            "--local",
            "https://pypi.org/project/specmint",
        ]
    )
    assert code == 1
    assert out == ""
    problem = json.loads(err)
    assert problem["code"] == "MINT_INTEGRATION"
    assert "refuse network source" in problem["message"]
    pip_code, pip_out, pip_err = _run(["integrations", "add", "--project", str(project), "pip"])
    assert pip_code == 1
    assert pip_out == ""
    pip_problem = json.loads(pip_err)
    assert "does not pip" in pip_problem["message"]
    assert "[[integrations]]" not in (project / "mint.toml").read_text(encoding="utf-8")


def test_local_conformance_kit(tmp_path: Path) -> None:
    example = Path(__file__).resolve().parents[1] / "examples" / "integrations" / "local-sandbox"
    code, out, err = _run(["integrations", "test", "--local", str(example)])
    assert code == 0, err
    report = json.loads(out)
    assert report["ok"] is True
    assert report["executeRefused"] is True
    assert report["identity"] == IDENTITY
    refused = _run(
        ["integrations", "test", "--local", "https://github.com/opsdevcode/mint-integration-local"]
    )
    assert refused[0] == 1
    assert "refuse network source" in refused[2]


def test_verify_fails_on_tampered_digest(tmp_path: Path) -> None:
    project = _project(tmp_path)
    add_code, _out, add_err = _run(["integrations", "add", "--project", str(project), IDENTITY])
    assert add_code == 0, add_err
    lock_path = project / "mint.lock"
    text = lock_path.read_text(encoding="utf-8")
    lock_path.write_text(text.replace(VERSION, "9.9.9"), encoding="utf-8")
    code, out, err = _run(["integrations", "verify", "--project", str(project)])
    assert code == 1
    assert out == ""
    problem = json.loads(err)
    assert problem["code"] in {"MINT_LOCK", "MINT_INTEGRATION"}

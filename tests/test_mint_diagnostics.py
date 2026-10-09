from __future__ import annotations

import json
from pathlib import Path

import pytest

from opsdevcode_specmint.mint.cli import language_command_names, main
from opsdevcode_specmint.mint.diagnostics import (
    diagnostic_payload,
    display_path,
    render_diagnostic,
    render_payload,
    sanitize_text,
    sarif_log,
)
from opsdevcode_specmint.mint.errors import MintDiagnostic, parse_error
from test_mint_cli import _run


def test_apply_is_unknown() -> None:
    assert "apply" not in language_command_names()
    assert "doctor" in language_command_names()
    assert "init" in language_command_names()


def test_display_path_strips_host_absolute() -> None:
    assert display_path(Path("/Users/example/project/main.mint")) == "main.mint"
    assert display_path("units/main.mint") == "units/main.mint"
    assert display_path(Path("../secret.mint")) == "secret.mint"


def test_sanitize_text_redacts_secrets_and_host_paths() -> None:
    text = sanitize_text("token ghp_abcdefghijklmnopqrstu and /Users/example/.ssh/id_rsa")
    assert "ghp_" not in text
    assert "<redacted>" in text
    assert "/Users/" not in text
    assert "id_rsa" in text


def test_diagnostic_payload_includes_range_and_snapshot() -> None:
    diagnostic = MintDiagnostic(
        code="MINT_SNAPSHOT",
        message="missing repository snapshot for /Users/example/repo.json",
        line=2,
        column=1,
        unit="main.mint",
        end_line=2,
        end_column=8,
        start_offset=10,
        end_offset=17,
        snapshot={"kind": "repo.github", "supplied": 0},
    )
    payload = diagnostic_payload(diagnostic)
    assert payload["range"]["start"] == {"column": 1, "line": 2, "offset": 10}
    assert payload["range"]["end"] == {"column": 8, "line": 2, "offset": 17}
    assert payload["snapshot"] == {"kind": "repo.github", "supplied": 0}
    assert "/Users/" not in payload["message"]
    assert "repo.json" in payload["message"]


def test_human_diagnostic_is_explicit_not_tty_guessed() -> None:
    exc = parse_error(3, 1, "set the language edition to v0", unit="main.mint")
    human = render_diagnostic(exc.diagnostic, output_format="human")
    assert human.startswith("MINT_PARSE:main.mint:3:1-")
    assert "set the language edition to v0" in human
    assert human.endswith("\n")
    dumped = render_diagnostic(exc.diagnostic, output_format="json")
    body = json.loads(dumped)
    assert body["code"] == "MINT_PARSE"
    assert body["range"]["start"]["line"] == 3


def test_default_diagnostic_format_stays_json_when_tty(monkeypatch: object) -> None:
    import sys

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    code, out, err = _run(["check", "-"], stdin="not mint")
    assert code == 1
    assert out == ""
    body = json.loads(err)
    assert body["ok"] is False
    assert body["code"] == "MINT_PARSE"


def test_human_output_format_flag() -> None:
    code, out, err = _run(
        ["--output-format", "human", "check", "-"],
        stdin="not mint",
    )
    assert code == 1
    assert out == ""
    assert err.startswith("MINT_PARSE:")
    assert err.strip()[0] != "{"


def test_main_rejects_unknown_output_format() -> None:
    with pytest.raises(SystemExit):
        main(["--output-format", "pretty", "version"])


def test_sarif_diagnostic_uses_rule_id_and_redacts_paths() -> None:
    diagnostic = MintDiagnostic(
        code="MINT_SNAPSHOT",
        message="missing repository snapshot for /Users/example/repo.json",
        line=2,
        column=1,
        unit="main.mint",
        end_line=2,
        end_column=8,
    )
    body = sarif_log(diagnostic)
    assert body["version"] == "2.1.0"
    run = body["runs"][0]
    assert run["tool"]["driver"]["name"] == "mint"
    assert run["results"][0]["ruleId"] == "MINT_SNAPSHOT"
    assert "/Users/" not in run["results"][0]["message"]["text"]
    assert run["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"] == 2
    dumped = render_diagnostic(diagnostic, output_format="sarif")
    assert json.loads(dumped)["runs"][0]["results"][0]["ruleId"] == "MINT_SNAPSHOT"


def test_empty_sarif_log_has_no_results() -> None:
    body = sarif_log(None)
    assert body["runs"][0]["results"] == []
    assert body["runs"][0]["tool"]["driver"]["rules"] == []


def test_sarif_output_file_on_check_failure(tmp_path: Path) -> None:
    dest = tmp_path / "mint.sarif"
    code, out, err = _run(
        ["--output-format", "sarif", "check", "-", "--sarif-output", str(dest)],
        stdin="not mint",
    )
    assert code == 1
    assert out == ""
    stderr_body = json.loads(err)
    assert stderr_body["version"] == "2.1.0"
    assert stderr_body["runs"][0]["results"][0]["ruleId"] == "MINT_PARSE"
    written = json.loads(dest.read_text(encoding="utf-8"))
    assert written["runs"][0]["results"][0]["ruleId"] == "MINT_PARSE"


def test_sarif_output_file_empty_on_check_success(tmp_path: Path) -> None:
    dest = tmp_path / "mint.sarif"
    project = Path("examples/projects/local-marker")
    code, out, _err = _run(
        ["check", "--project", str(project), "--sarif-output", str(dest)],
    )
    assert code == 0
    assert json.loads(out)["ok"] is True
    written = json.loads(dest.read_text(encoding="utf-8"))
    assert written["runs"][0]["results"] == []


def test_render_payload_refuses_sarif() -> None:
    with pytest.raises(ValueError, match="mint check --sarif-output"):
        render_payload({"ok": True}, output_format="sarif")

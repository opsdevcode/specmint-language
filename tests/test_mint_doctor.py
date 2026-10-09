from __future__ import annotations

import json
from pathlib import Path

from opsdevcode_specmint.mint.doctor import doctor_source_is_offline, run_doctor
from test_mint_cli import _run
from test_mint_project import _write_marker


def test_doctor_offline_without_project() -> None:
    code, out, err = _run(["doctor"])
    assert err == ""
    body = json.loads(out)
    assert code == 0
    assert body["ok"] is True
    assert body["offline"] is True
    assert body["schema"] == "mint.doctor/v0"
    by_id = {item["id"]: item for item in body["checks"]}
    assert by_id["python"]["ok"] is True
    assert by_id["apply-absent"]["ok"] is True
    assert "mint apply is unknown" in by_id["apply-absent"]["message"]
    assert by_id["offline"]["ok"] is True
    assert by_id["project"]["skipped"] is True
    assert by_id["integrations"]["ok"] is True
    assert by_id["supervisor"]["ok"] is True
    assert "no daemon" in by_id["supervisor"]["message"]


def test_doctor_human_format() -> None:
    code, out, err = _run(["doctor", "--output-format", "human"])
    assert code == 0
    assert err == ""
    assert "ok: true" in out
    assert "offline: true" in out
    assert "apply-absent: ok" in out
    assert out.strip()[0] != "{"


def test_doctor_project_compile(tmp_path: Path) -> None:
    _write_marker(tmp_path, name="sample")
    code, out, err = _run(["doctor", "--project", str(tmp_path)])
    assert err == ""
    body = json.loads(out)
    assert code == 0
    by_id = {item["id"]: item for item in body["checks"]}
    assert by_id["project"]["ok"] is True
    assert by_id["project"]["skipped"] is False
    assert by_id["compile"]["ok"] is True
    assert "digest sha256:" in by_id["compile"]["message"]
    assert by_id["lock"]["skipped"] is True


def test_doctor_reports_compile_failure(tmp_path: Path) -> None:
    (tmp_path / "main.mint").write_text("mint v0\n", encoding="utf-8")
    (tmp_path / "mint.toml").write_text(
        (
            'schema = "mint.project/v0"\n'
            'name = "broken"\n'
            'edition = "v0"\n'
            'root = "main.mint"\n'
            'units = ["main.mint"]\n'
        ),
        encoding="utf-8",
    )
    code, out, err = _run(["doctor", "--project", str(tmp_path)])
    assert err == ""
    body = json.loads(out)
    assert code == 1
    assert body["ok"] is False
    by_id = {item["id"]: item for item in body["checks"]}
    assert by_id["compile"]["ok"] is False
    assert "/Users/" not in json.dumps(body)
    assert "ghp_" not in json.dumps(body)


def test_doctor_module_does_not_import_network() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "src/opsdevcode_specmint/mint/doctor.py"
    ).read_text(encoding="utf-8")
    assert doctor_source_is_offline(source)
    report = run_doctor()
    assert report.offline is True


def test_init_list_templates() -> None:
    code, out, err = _run(["init", "--list-templates"])
    assert code == 0
    assert err == ""
    body = json.loads(out)
    ids = [item["id"] for item in body["templates"]]
    assert ids == ["local-marker", "minimal"]
    assert body["templates"][0]["default"] is True


def test_init_minimal_template(tmp_path: Path) -> None:
    target = tmp_path / "tiny"
    code, out, err = _run(["init", str(target), "--name", "tiny", "--template", "minimal"])
    assert code == 0
    assert err == ""
    body = json.loads(out)
    assert body["template"] == "minimal"
    manifest = (target / "mint.toml").read_text(encoding="utf-8")
    assert "profiles.local" not in manifest
    assert (target / "main.mint").is_file()
    check_code, check_out, check_err = _run(["check", "--project", str(target)])
    assert check_code == 0
    assert check_err == ""
    assert json.loads(check_out)["ok"] is True


def test_init_unknown_template(tmp_path: Path) -> None:
    code, out, err = _run(["init", str(tmp_path), "--template", "terraform"])
    assert code == 1
    assert out == ""
    problem = json.loads(err)
    assert problem["code"] == "MINT_TEMPLATE"
    assert "local-marker" in problem["message"]


def test_init_human_format(tmp_path: Path) -> None:
    target = tmp_path / "human"
    code, out, err = _run(["init", str(target), "--name", "human", "--output-format", "human"])
    assert code == 0
    assert err == ""
    assert "ok: true" in out
    assert "template: local-marker" in out
    assert "manifest: mint.toml" in out

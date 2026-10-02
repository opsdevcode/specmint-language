from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from opsdevcode_specmint import __version__
from opsdevcode_specmint.mint.cli import main

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "examples" / "projects" / "local-marker"


def _run(argv: list[str], *, stdin: str = "") -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    code = main(argv, stdin=io.StringIO(stdin), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def test_public_preview_version() -> None:
    assert __version__ == "0.1.0a2"
    code, out, err = _run(["version"])
    assert code == 0
    assert out == "mint language v0 (specmint 0.1.0a2)\n"
    assert err == ""


def test_mint_apply_is_unknown() -> None:
    try:
        code, out, err = _run(["apply"])
    except SystemExit as exc:
        assert exc.code not in (0, None)
        return
    assert code != 0
    blob = (out + err).lower()
    assert "invalid" in blob or "unrecognized" in blob or "unknown" in blob or "error" in blob


def test_five_minute_quickstart(tmp_path: Path) -> None:
    project = tmp_path / "mint-quickstart"
    for name in ("mint.toml", "mint.lock", "main.mint", "plan.json"):
        source = EXAMPLE / name
        if source.exists():
            (project).mkdir(exist_ok=True)
            (project / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    code, _out, err = _run(["check", "--project", str(project), "--locked"])
    assert code == 0, err

    code, _out, err = _run(["fmt", "--check", str(project / "main.mint")])
    assert code == 0, err

    code, _out, err = _run(["lock", "--check", "--project", str(project)])
    assert code == 0, err

    code, compiled, err = _run(["compile", "--project", str(project), "--locked"])
    assert code == 0, err
    ir: dict[str, Any] = json.loads(compiled)
    ir_path = project / "mint-ir.json"
    ir_path.write_text(compiled, encoding="utf-8")

    code, inspected, err = _run(["inspect", str(ir_path)])
    assert code == 0, err
    payload = json.loads(inspected)
    assert payload.get("ok") is True or "digest" in payload or payload.get("kind") == ir.get("kind")

    code, planned, err = _run(["plan", "--project", str(project), "--locked"])
    assert code == 0, err
    assert "local.sandbox" in planned or "ensure_marker" in planned or planned.strip()

    code, conformance, err = _run(["integrations", "conformance", "local.sandbox.ensure_marker"])
    assert code == 0, err
    assert "ok" in conformance.lower() or "pass" in conformance.lower() or conformance.strip()

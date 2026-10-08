from __future__ import annotations

import io
import json
import os
import re
from pathlib import Path
from typing import Any

from opsdevcode_specmint import __version__
from opsdevcode_specmint.mint.cli import main
from opsdevcode_specmint.mint.fmt import format_source
from opsdevcode_specmint.mint.templates import TEMPLATES

REPO = Path(__file__).resolve().parents[1]
QUICKSTART = (REPO / "docs" / "quickstart.md").read_text(encoding="utf-8")
EXAMPLE = REPO / "examples" / "projects" / "local-marker"
_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)


def _run(argv: list[str], *, stdin: str = "") -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    code = main(argv, stdin=io.StringIO(stdin), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def _language_loop_commands() -> list[str]:
    fences = _FENCE.findall(QUICKSTART)
    assert len(fences) >= 2
    return [
        line.strip()
        for line in fences[1].splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_public_preview_version() -> None:
    code, out, err = _run(["version"])
    assert code == 0
    assert out == f"mint language v0 (specmint {__version__})\n"
    assert err == ""


def test_init_templates_are_fmt_canonical() -> None:
    for item in TEMPLATES:
        assert format_source(item.mint_source) == item.mint_source, item.template_id


def test_mint_apply_is_unknown() -> None:
    try:
        code, out, err = _run(["apply"])
    except SystemExit as exc:
        assert exc.code not in (0, None)
        return
    assert code != 0
    blob = (out + err).lower()
    assert "invalid" in blob or "unrecognized" in blob or "unknown" in blob or "error" in blob


def test_quickstart_copy_names_ten_minutes_and_native_terms() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    index = (REPO / "docs" / "index.md").read_text(encoding="utf-8")
    assert "## Ten-minute quickstart" in readme
    assert "Ten-minute quickstart" in index
    assert QUICKSTART.startswith("# Ten-minute Mint quickstart")
    assert "mint apply" in QUICKSTART
    assert "mint init" in QUICKSTART
    assert "mint doctor" in QUICKSTART
    assert "mint integrations test" in QUICKSTART
    lowered = QUICKSTART.lower()
    assert "observation" in lowered or "observe" in lowered
    assert "evidence" in QUICKSTART
    assert "Marketplace and Open VSX are deferred" in QUICKSTART
    assert "1.0" not in QUICKSTART or "not 1.0" in QUICKSTART.lower() or "before 1.0" in QUICKSTART
    for banned in ("terraform apply", "mint apply exists", "VSCE_PAT"):
        assert banned not in QUICKSTART


def test_documented_quickstart_commands(tmp_path: Path) -> None:
    previous = Path.cwd()
    os.chdir(tmp_path)
    try:
        cwd = tmp_path
        ran_mint = 0
        for raw in _language_loop_commands():
            line, _, redirected = raw.partition(">")
            argv = line.strip().split()
            dest = redirected.strip() if redirected else None
            if argv[:1] == ["cd"]:
                cwd = (cwd / argv[1]).resolve()
                os.chdir(cwd)
                continue
            assert argv[0] == "mint", raw
            code, out, err = _run(argv[1:])
            assert code == 0, f"{raw}\n{err}"
            ran_mint += 1
            if dest:
                (cwd / dest).write_text(out, encoding="utf-8")
        assert ran_mint >= 8
        ir = json.loads((cwd / "mint-ir.json").read_text(encoding="utf-8"))
        assert ir.get("kind") == "MintIR" or "digest" in ir or "apiVersion" in ir
    finally:
        os.chdir(previous)


def test_example_local_marker_still_plans(tmp_path: Path) -> None:
    project = tmp_path / "mint-quickstart"
    project.mkdir()
    for name in ("mint.toml", "mint.lock", "main.mint"):
        (project / name).write_text((EXAMPLE / name).read_text(encoding="utf-8"), encoding="utf-8")
    code, planned, err = _run(["plan", "--project", str(project), "--locked"])
    assert code == 0, err
    body: dict[str, Any] = json.loads(planned)
    assert "local.sandbox" in planned or body.get("ok") is True


def test_example_readme_uses_integrations() -> None:
    text = (EXAMPLE / "README.md").read_text(encoding="utf-8")
    assert "mint integrations test" in text
    assert "mint integrations inspect" in text
    assert "mint adapters inspect" not in text
    assert "mint apply" not in text


def test_ci_runs_documented_quickstart() -> None:
    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "Documented quickstart" in ci
    assert "tests/test_quickstart.py" in ci


def test_compatibility_policy_keeps_release_please_and_github_first() -> None:
    text = (REPO / "docs" / "compatibility.md").read_text(encoding="utf-8")
    assert "Release Please owns prerelease tags" in text
    assert "gh release create" in text
    assert "Marketplace" in text
    assert "Open VSX" in text
    assert "mint apply" in text
    assert "pipx install specmint==" not in text

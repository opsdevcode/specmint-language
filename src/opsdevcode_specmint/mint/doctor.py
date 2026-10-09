"""Offline mint doctor. No sockets, providers, or apply."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opsdevcode_specmint import __version__
from opsdevcode_specmint.mint.compile import compile_program
from opsdevcode_specmint.mint.errors import MintError
from opsdevcode_specmint.mint.project import (
    MANIFEST_NAME,
    discover_manifest,
    load_manifest,
    load_project_units,
)

DOCTOR_SCHEMA = "mint.doctor/v0"
_APPLY = "apply"


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    id: str
    ok: bool
    skipped: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "message": self.message,
            "ok": self.ok,
            "skipped": self.skipped,
        }


@dataclass(frozen=True, slots=True)
class DoctorReport:
    ok: bool
    offline: bool
    schema: str
    checks: tuple[DoctorCheck, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": [item.to_dict() for item in self.checks],
            "offline": self.offline,
            "ok": self.ok,
            "schema": self.schema,
        }


def run_doctor(*, project: Path | None = None, cwd: Path | None = None) -> DoctorReport:
    start = cwd or Path.cwd()
    checks = (
        _python_check(),
        _version_check(),
        _apply_absent_check(),
        _offline_check(),
        *_project_checks(start=start, project=project),
        _integrations_check(),
        _supervisor_check(),
    )
    ok = all(item.ok or item.skipped for item in checks)
    return DoctorReport(ok=ok, offline=True, schema=DOCTOR_SCHEMA, checks=checks)


def doctor_source_is_offline(source: str) -> bool:
    tree = ast.parse(source)
    forbidden = {"socket", "http", "http.client", "urllib", "urllib.request", "requests"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".", 1)[0] for alias in node.names}
            if imported & forbidden or any(alias.name in forbidden for alias in node.names):
                return False
        if isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if node.module in forbidden or root in {"socket", "http", "urllib", "requests"}:
                return False
    return True


def _python_check() -> DoctorCheck:
    version = sys.version_info
    ok = version[:2] == (3, 12)
    rendered = f"{version.major}.{version.minor}.{version.micro}"
    if ok:
        return DoctorCheck("python", True, False, f"Python {rendered}")
    return DoctorCheck(
        "python",
        False,
        False,
        f"install Python 3.12; this interpreter is {rendered}",
    )


def _version_check() -> DoctorCheck:
    return DoctorCheck("version", True, False, f"mint language v0 (specmint {__version__})")


def _apply_absent_check() -> DoctorCheck:
    from opsdevcode_specmint.mint.cli import language_command_names

    if _APPLY in language_command_names():
        return DoctorCheck("apply-absent", False, False, "mint apply must stay unknown")
    return DoctorCheck("apply-absent", True, False, "mint apply is unknown")


def _offline_check() -> DoctorCheck:
    source = Path(__file__).read_text(encoding="utf-8")
    if not doctor_source_is_offline(source):
        return DoctorCheck("offline", False, False, "doctor must not import network libraries")
    return DoctorCheck("offline", True, False, "doctor is offline; no sockets or providers")


def _integrations_check() -> DoctorCheck:
    from opsdevcode_specmint.integration.reference_server import IDENTITY

    return DoctorCheck(
        "integrations",
        True,
        False,
        f"reference integration {IDENTITY} is packaged",
    )


def _supervisor_check() -> DoctorCheck:
    return DoctorCheck(
        "supervisor",
        True,
        False,
        "process supervisor is one-shot stdio; no daemon",
    )


def _project_checks(*, start: Path, project: Path | None) -> tuple[DoctorCheck, ...]:
    if project is None:
        candidate = start / MANIFEST_NAME
        if not candidate.is_file():
            return (
                DoctorCheck("project", True, True, f"no {MANIFEST_NAME} in this directory"),
                DoctorCheck("lock", True, True, "skipped; no project"),
                DoctorCheck("compile", True, True, "skipped; no project"),
            )
        project = candidate
    try:
        manifest_path = discover_manifest(Path(project))
    except MintError as exc:
        return (
            DoctorCheck("project", False, False, exc.diagnostic.message),
            DoctorCheck("lock", False, True, "skipped; project did not load"),
            DoctorCheck("compile", False, True, "skipped; project did not load"),
        )
    try:
        manifest = load_manifest(manifest_path)
    except MintError as exc:
        return (
            DoctorCheck("project", False, False, exc.diagnostic.message),
            DoctorCheck("lock", False, True, "skipped; project did not load"),
            DoctorCheck("compile", False, True, "skipped; project did not load"),
        )
    project_check = DoctorCheck(
        "project",
        True,
        False,
        f"{MANIFEST_NAME} name={manifest.name} edition={manifest.edition}",
    )
    lock_check = _lock_check(manifest.lock_path)
    compile_check = _compile_check(manifest)
    return (project_check, lock_check, compile_check)


def _lock_check(lock_path: Path) -> DoctorCheck:
    if not lock_path.is_file():
        return DoctorCheck(
            "lock",
            True,
            True,
            f"{lock_path.name} absent; run mint lock --project DIR when you want a lock",
        )
    return DoctorCheck("lock", True, False, f"{lock_path.name} present")


def _compile_check(manifest: Any) -> DoctorCheck:
    try:
        program = load_project_units(manifest)
        result = compile_program(
            root=program.root, units=program.units, extensions=program.extensions
        )
    except MintError as exc:
        return DoctorCheck("compile", False, False, exc.diagnostic.message)
    if not result.ok or result.digest is None:
        message = result.diagnostic.message if result.diagnostic else "compile failed"
        return DoctorCheck("compile", False, False, message)
    return DoctorCheck("compile", True, False, f"digest {result.digest}")

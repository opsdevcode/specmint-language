from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

from opsdevcode_specmint import __version__

REPO = Path(__file__).resolve().parents[1]


def test_sdist_and_wheel_install_isolated(tmp_path: Path) -> None:
    builder = tmp_path / "builder"
    subprocess.run(
        ["python3", "-m", "venv", str(builder)],
        check=True,
        capture_output=True,
        text=True,
    )
    py = builder / "bin" / "python"
    subprocess.run(
        [str(py), "-m", "pip", "install", "--disable-pip-version-check", "build==1.2.2"],
        check=True,
        capture_output=True,
        text=True,
    )
    outdir = tmp_path / "dist"
    outdir.mkdir()
    built = subprocess.run(
        [str(py), "-m", "build", str(REPO), "--sdist", "--wheel", "--outdir", str(outdir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    sdist = next(outdir.glob("*.tar.gz"))
    wheel = next(outdir.glob("*.whl"))
    assert f"specmint-{__version__}" in sdist.name
    assert f"specmint-{__version__}" in wheel.name

    for artifact in (sdist, wheel):
        isolated = tmp_path / f"iso-{artifact.suffixes[0].strip('.')}"
        subprocess.run(["python3", "-m", "venv", str(isolated)], check=True, capture_output=True)
        iso_py = isolated / "bin" / "python"
        install = subprocess.run(
            [str(iso_py), "-m", "pip", "install", "--disable-pip-version-check", str(artifact)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert install.returncode == 0, install.stderr
        version = subprocess.run(
            [str(isolated / "bin" / "mint"), "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert version.returncode == 0, version.stderr
        assert version.stdout == f"mint language v0 (specmint {__version__})\n"
        help_out = subprocess.run(
            [str(isolated / "bin" / "mint"), "apply"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert help_out.returncode != 0

    with tarfile.open(sdist) as archive:
        names = archive.getnames()
    joined = "\n".join(names)
    assert "cue/" not in joined
    assert "platform/service.py" not in joined


def test_pipx_and_uv_install_from_wheel(tmp_path: Path) -> None:
    pipx = shutil.which("pipx")
    uv = shutil.which("uv")
    if pipx is None and uv is None:
        pytest.skip("pipx and uv are not on PATH in this environment")

    builder = tmp_path / "builder"
    subprocess.run(["python3", "-m", "venv", str(builder)], check=True, capture_output=True)
    py = builder / "bin" / "python"
    subprocess.run(
        [str(py), "-m", "pip", "install", "--disable-pip-version-check", "build==1.2.2"],
        check=True,
        capture_output=True,
        text=True,
    )
    outdir = tmp_path / "dist"
    outdir.mkdir()
    built = subprocess.run(
        [str(py), "-m", "build", str(REPO), "--wheel", "--outdir", str(outdir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    wheel = next(outdir.glob("*.whl"))
    env = os.environ.copy()
    env["PIPX_HOME"] = str(tmp_path / "pipx-home")
    env["PIPX_BIN_DIR"] = str(tmp_path / "pipx-bin")
    env["UV_TOOL_DIR"] = str(tmp_path / "uv-tools")
    env["UV_TOOL_BIN_DIR"] = str(tmp_path / "uv-bin")

    if pipx is not None:
        (tmp_path / "pipx-bin").mkdir()
        installed = subprocess.run(
            [pipx, "install", str(wheel)],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert installed.returncode == 0, installed.stderr or installed.stdout
        mint = tmp_path / "pipx-bin" / "mint"
        version = subprocess.run(
            [str(mint), "version"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert version.returncode == 0, version.stderr
        assert "specmint 0.1.0a2" in version.stdout
        subprocess.run([pipx, "uninstall", "specmint"], check=False, env=env, capture_output=True)

    if uv is not None:
        (tmp_path / "uv-bin").mkdir()
        installed = subprocess.run(
            [uv, "tool", "install", str(wheel)],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert installed.returncode == 0, installed.stderr or installed.stdout
        mint = tmp_path / "uv-bin" / "mint"
        version = subprocess.run(
            [str(mint), "version"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert version.returncode == 0, version.stderr
        assert "specmint 0.1.0a2" in version.stdout
        subprocess.run(
            [uv, "tool", "uninstall", "specmint"],
            check=False,
            env=env,
            capture_output=True,
        )


def test_vsix_manifest_matches_alpha2(tmp_path: Path) -> None:
    vsce = shutil.which("npx")
    if vsce is None:
        pytest.skip("npx is required to package the VSIX")
    editors = REPO / "editors" / "vscode"
    packed = subprocess.run(
        [
            "npx",
            "--yes",
            "@vscode/vsce",
            "package",
            "--no-git-tag-version",
            "--no-update-package-json",
        ],
        cwd=editors,
        capture_output=True,
        text=True,
        check=False,
    )
    vsix = next(editors.glob("*.vsix"), None)
    if packed.returncode != 0 or vsix is None:
        pytest.skip(f"vsce package skipped: {packed.stderr[-400:]}")
    dest = tmp_path / vsix.name
    dest.write_bytes(vsix.read_bytes())
    vsix.unlink()
    with zipfile.ZipFile(dest) as archive:
        raw = archive.read("extension/package.json")
    package = json.loads(raw.decode("utf-8"))
    assert package["version"] == "0.1.0-alpha.2"
    assert package["publisher"] == "opsdevcode"
    assert package["name"] == "mint-language"
    assert package["license"] == "Apache-2.0"

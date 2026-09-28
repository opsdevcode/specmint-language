from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not (REPO / "dist").exists(), reason="dist built in release")
def test_placeholder() -> None:
    assert True


def test_sdist_omits_cue_and_platform(tmp_path: Path) -> None:
    import subprocess
    import venv

    builder = tmp_path / "builder"
    venv.create(builder, with_pip=True, symlinks=True)
    py = builder / "bin" / "python"
    install = subprocess.run(
        [str(py), "-m", "pip", "install", "--disable-pip-version-check", "build==1.2.2"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, install.stderr
    outdir = tmp_path / "dist"
    outdir.mkdir()
    built = subprocess.run(
        [str(py), "-m", "build", str(REPO), "--sdist", "--outdir", str(outdir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    sdist = next(outdir.glob("*.tar.gz"))
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
    joined = "\n".join(names)
    assert "cue/" not in joined
    assert "platform/service.py" not in joined
    assert any(name.endswith("specification/mint/v0/language.md") for name in names)

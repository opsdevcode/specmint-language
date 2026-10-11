from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCKERFILE = (REPO / "Dockerfile").read_text(encoding="utf-8")
NGINX = (REPO / "nginx" / "default.conf").read_text(encoding="utf-8")
CI = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def test_site_image_uses_existing_generator() -> None:
    assert "scripts/build_docs_site.py --out /site --include-tag-snapshots" in DOCKERFILE
    assert "nginxinc/nginx-unprivileged:1.27-alpine" in DOCKERFILE
    assert ":latest" not in DOCKERFILE
    assert "pages reverse" not in DOCKERFILE.lower()


def test_site_image_healthz_and_static_root() -> None:
    assert "listen 8080" in NGINX
    assert "location = /healthz" in NGINX
    assert "try_files $uri $uri/ $uri.html =404" in NGINX


def test_ci_publishes_sha_not_latest() -> None:
    assert "ghcr.io/opsdevcode/mint:${{ github.sha }}" in CI
    assert "ghcr.io/opsdevcode/mint:latest" not in CI
    assert "docker build -t ghcr.io/opsdevcode/mint:" in CI
    assert '<pre tabindex="0">' in CI

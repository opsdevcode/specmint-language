"""Offline mint init templates. Data only; no network or provider SDKs."""

from __future__ import annotations

from dataclasses import dataclass

from opsdevcode_specmint.mint.errors import coded_error

DEFAULT_TEMPLATE = "local-marker"

_LOCAL_MARKER_MINT = """\
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

_MINIMAL_MINT = """\
mint v0
automation as-local-marker-1 {
  owner "platform@opsdevcode.com"
  intent "Compile a local sandbox marker plan"
  use local.sandbox.ensure_marker v1alpha1
  sandbox fixture-alpha
  evidence marker.present
  require authorization
  forbid mutation
  status draft
}
"""


@dataclass(frozen=True, slots=True)
class InitTemplate:
    template_id: str
    summary: str
    default: bool
    mint_source: str
    manifest_profiles: str


TEMPLATES: tuple[InitTemplate, ...] = (
    InitTemplate(
        template_id="local-marker",
        summary="Local sandbox marker with a local profile target",
        default=True,
        mint_source=_LOCAL_MARKER_MINT,
        manifest_profiles='[profiles.local]\ntargets = ["fixture-alpha"]\n',
    ),
    InitTemplate(
        template_id="minimal",
        summary="Single-unit local sandbox marker without extra profiles",
        default=False,
        mint_source=_MINIMAL_MINT,
        manifest_profiles="",
    ),
)

_BY_ID = {item.template_id: item for item in TEMPLATES}


def list_template_payload() -> dict[str, object]:
    return {
        "ok": True,
        "templates": [
            {
                "default": item.default,
                "id": item.template_id,
                "summary": item.summary,
            }
            for item in TEMPLATES
        ],
    }


def load_template(template_id: str | None) -> InitTemplate:
    ident = template_id if template_id else DEFAULT_TEMPLATE
    found = _BY_ID.get(ident)
    if found is None:
        known = ", ".join(item.template_id for item in TEMPLATES)
        raise coded_error(
            "MINT_TEMPLATE",
            f"unknown init template {ident}; pass --template {known}",
        )
    return found

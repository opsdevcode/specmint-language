from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PKG = _ROOT / "editors" / "vscode" / "package.json"
_GRAMMAR = _ROOT / "editors" / "vscode" / "syntaxes" / "mint.tmLanguage.json"
_EXT = _ROOT / "editors" / "vscode" / "src" / "extension.js"


def test_extension_is_public_and_untrusted_opt_out() -> None:
    package = json.loads(_PKG.read_text(encoding="utf-8"))
    assert package.get("private") is not True
    assert package["license"] == "Apache-2.0"
    assert package["publisher"] == "opsdevcode"
    assert package["name"] == "mint-language"
    assert package["version"] == "0.1.0-alpha.2"
    assert package.get("publishConfig") is None
    assert package["capabilities"]["untrustedWorkspaces"]["supported"] is False
    assert package["dependencies"]["vscode-languageclient"] == "9.0.1"
    lock = json.loads(
        (_ROOT / "editors" / "vscode" / "package-lock.json").read_text(encoding="utf-8")
    )
    assert lock["packages"]["node_modules/vscode-languageclient"]["version"] == "9.0.1"


def test_textmate_grammar_is_lexical_only() -> None:
    grammar = json.loads(_GRAMMAR.read_text(encoding="utf-8"))
    blob = json.dumps(grammar)
    assert "comment.line" in blob
    assert "string.quoted" in blob
    assert "compile_program" not in blob
    assert "namespace resolution" not in blob.lower()


def test_extension_uses_stdio_and_checks_trust() -> None:
    source = _EXT.read_text(encoding="utf-8")
    assert "TransportKind.stdio" in source
    assert "isTrusted" in source
    assert "listen(" not in source
    assert "telemetry" not in source.lower()
    assert "http://" not in source

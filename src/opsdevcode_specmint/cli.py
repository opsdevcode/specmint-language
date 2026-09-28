"""Public CLI: mint language plus a thin specmint alias. No serve, execute, or apply."""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO, Any, TextIO

from opsdevcode_specmint import __version__
from opsdevcode_specmint.compiler import inspect_artifact, validate_specification
from opsdevcode_specmint.errors import SpecProblem
from opsdevcode_specmint.parse import decode_body, decode_path, media_type_for_format


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: IO[bytes] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.show_version or args.command == "version":
        out.write(f"specmint {__version__}\n")
        return 0
    if args.command is None:
        parser.print_help(out)
        return 0
    try:
        if args.command == "mint":
            from opsdevcode_specmint.mint.cli import main as mint_main

            raw_in = b"" if stdin is None else stdin.read()
            text = raw_in.decode("utf-8") if isinstance(raw_in, bytes | bytearray) else str(raw_in)
            return mint_main(list(args.mint_args), stdin=io.StringIO(text), stdout=out, stderr=err)
        document = _load_document(args.path, stdin=stdin, format=getattr(args, "format", None))
        if args.command == "validate":
            payload = validate_specification(document)
        elif args.command == "compile":
            from opsdevcode_specmint.compiler import compile_specification

            payload = compile_specification(document)
        else:
            payload = inspect_artifact(document)
        out.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    except SpecProblem as exc:
        err.write(json.dumps(exc.as_dict(), indent=2, sort_keys=True) + "\n")
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specmint")
    parser.add_argument("--version", action="store_true", dest="show_version")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("version")
    mint = sub.add_parser("mint")
    mint.add_argument("mint_args", nargs=argparse.REMAINDER)
    for name in ("validate", "compile", "inspect"):
        cmd = sub.add_parser(name)
        cmd.add_argument("path", nargs="?", default="-")
        cmd.add_argument("--format", choices=("json", "yaml", "markdown", "mint"))
    return parser


def _load_document(path: str, *, stdin: IO[bytes] | None, format: str | None) -> dict[str, Any]:
    if path == "-":
        raw = b"" if stdin is None else stdin.read()
        media = media_type_for_format(format) if format else "application/json"
        body = raw if isinstance(raw, bytes | bytearray) else str(raw).encode()
        return decode_body(body, media)
    return decode_path(Path(path), format=format)

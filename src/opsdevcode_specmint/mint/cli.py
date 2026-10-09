"""Offline Mint language CLI. MintIR and plan artifacts; no apply or network."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO, Any, TextIO

from opsdevcode_specmint import __version__
from opsdevcode_specmint.mint.adapters.output import write_artifact_set
from opsdevcode_specmint.mint.adapters.plan import plan_mint_ir
from opsdevcode_specmint.mint.adapters.registry import builtin_registry
from opsdevcode_specmint.mint.adapters.snapshot import load_snapshot_file, snapshot_canonical_bytes
from opsdevcode_specmint.mint.compile import compile_program
from opsdevcode_specmint.mint.diagnostics import (
    DEFAULT_OUTPUT_FORMAT,
    display_path,
    render_diagnostic,
    render_payload,
)
from opsdevcode_specmint.mint.doctor import run_doctor
from opsdevcode_specmint.mint.errors import MintError, coded_error
from opsdevcode_specmint.mint.fmt import format_source
from opsdevcode_specmint.mint.inputs import (
    DeclaredProgram,
    as_mint_error,
    load_declared_graph,
    load_declared_paths,
)
from opsdevcode_specmint.mint.inspect_ir import inspect_mint_ir
from opsdevcode_specmint.mint.integrations_cmd import deprecation_notice, run_integrations
from opsdevcode_specmint.mint.lsp.server import serve_stdio
from opsdevcode_specmint.mint.parser import parse_mint_text
from opsdevcode_specmint.mint.project import (
    MANIFEST_NAME,
    ProjectManifest,
    apply_profile,
    build_lockfile,
    check_lockfile,
    discover_manifest,
    init_project,
    load_locked_program,
    load_manifest,
    load_project_units,
    write_lockfile,
)
from opsdevcode_specmint.mint.templates import DEFAULT_TEMPLATE, list_template_payload

_LANGUAGE_EDITION = "v0"


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: IO[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    in_stream = stdin or sys.stdin
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    output_format = getattr(args, "output_format", DEFAULT_OUTPUT_FORMAT)
    if args.show_version or args.command == "version":
        out.write(_version_line())
        return 0
    if args.command is None:
        parser.print_help(out)
        return 0
    try:
        return _dispatch(args, stdin=in_stream, stdout=out, stderr=err)
    except MintError as exc:
        err.write(render_diagnostic(exc.diagnostic, output_format=output_format))
        return 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        err.write(render_diagnostic(as_mint_error(exc).diagnostic, output_format=output_format))
        return 1


def _dispatch(args: argparse.Namespace, *, stdin: IO[str], stdout: TextIO, stderr: TextIO) -> int:
    if args.command == "lsp":
        return serve_stdio()
    if args.command == "doctor":
        return _run_doctor(args, stdout=stdout)
    if args.command == "integrations":
        return run_integrations(args, stdout=stdout, stderr=stderr)
    if args.command == "adapters":
        code = _run_adapters(args, stdout=stdout)
        stderr.write(deprecation_notice("mint adapters " + str(args.adapters_command)) + "\n")
        return code
    if args.command == "repository":
        return _run_repository(args, stdout=stdout)
    if args.command == "inspect":
        document = _load_json(args.path, stdin=stdin)
        payload = inspect_mint_ir(document)
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if args.command == "fmt":
        return _run_fmt(args, stdin=stdin, stdout=stdout)
    if args.command == "convert":
        return _run_convert(args, stdin=stdin, stdout=stdout)
    if args.command == "init":
        return _run_init(args, stdout=stdout)
    if args.command == "lock":
        return _run_lock(args, stdout=stdout)
    if args.command == "project":
        if args.project_command != "check":
            raise coded_error(
                "MINT_PROJECT",
                "mint project accepts check; run mint project check --project DIR",
            )
        args.command = "check"
        args.paths = []
        args.graph = None
        args.locked = True
    program = _load_program(args, stdin=stdin)
    result = compile_program(root=program.root, units=program.units, extensions=program.extensions)
    if not result.ok or result.ir is None:
        diagnostic = result.diagnostic
        if diagnostic is None:
            raise as_mint_error(RuntimeError("compile failed without a diagnostic"))
        raise MintError(diagnostic)
    profile = getattr(args, "profile", None)
    if profile:
        apply_profile(_load_manifest(args), profile, result.ir)
    if args.command == "check":
        stdout.write(
            json.dumps({"ok": True, "digest": result.digest}, indent=2, sort_keys=True) + "\n"
        )
        return 0
    if args.command == "plan":
        snapshot_paths = tuple(sorted(getattr(args, "snapshots", None) or []))
        snapshots = tuple(load_snapshot_file(Path(item)) for item in snapshot_paths)
        planned = plan_mint_ir(
            result.ir, adapter_id=getattr(args, "adapter", None), snapshots=snapshots
        )
        artifacts_dir = getattr(args, "artifacts", None)
        if artifacts_dir:
            write_artifact_set(planned.artifacts, Path(artifacts_dir))
        output = getattr(args, "output", None)
        plan_bytes = planned.canonical_bytes()
        if output:
            _write_bytes_confined(Path(output), plan_bytes)
        stdout.write(plan_bytes.decode("utf-8"))
        return 0
    stdout.write(result.ir.canonical_bytes().decode("utf-8"))
    return 0


def _run_adapters(args: argparse.Namespace, *, stdout: TextIO) -> int:
    registry = builtin_registry()
    command = args.adapters_command
    if command == "list":
        payload = {
            "ok": True,
            "registry": "builtin",
            "adapters": [item.to_canonical_dict() for item in registry.manifests()],
        }
        stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if command == "inspect":
        manifest = registry.inspect(args.adapter_id)
        stdout.write(json.dumps(manifest.to_canonical_dict(), indent=2, sort_keys=True) + "\n")
        return 0
    raise coded_error(
        "MINT_ADAPTER",
        "mint adapters accepts list or inspect; run mint adapters list",
    )


def _run_repository(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if args.repository_command != "snapshot" or args.snapshot_command != "check":
        raise coded_error(
            "MINT_SNAPSHOT",
            "mint repository accepts snapshot check; "
            "run mint repository snapshot check SNAPSHOT.json",
        )
    snapshot = load_snapshot_file(Path(args.snapshot_path))
    stdout.write(snapshot_canonical_bytes(snapshot).decode("utf-8"))
    return 0


def _write_bytes_confined(destination: Path, payload: bytes) -> None:
    raw = str(destination)
    if raw in {"", "-"} or (not Path(raw).is_absolute() and ".." in Path(raw).parts):
        raise coded_error(
            "MINT_PATH",
            f"set --output to a confined file path; refuse {raw}",
        )
    dest = destination if destination.is_absolute() else Path.cwd() / destination
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f"{dest.name}.tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, dest)


def _run_convert(args: argparse.Namespace, *, stdin: IO[str], stdout: TextIO) -> int:
    from opsdevcode_specmint.mint.convert import (
        ConversionItem,
        convert_path,
        convert_project,
        convert_text,
        resolve_input_format,
        write_report,
    )

    preview = bool(args.preview)
    check = bool(args.check)
    replace = bool(args.replace)
    report_path = Path(args.report) if args.report else None
    if args.project and not args.input:
        report, _writes = convert_project(Path(args.project), preview=preview, replace=replace)
        if not report.ok:
            if report_path is not None and not preview:
                write_report(report_path, report)
            stdout.write(report.canonical_bytes().decode("utf-8"))
            raise coded_error(
                "MINT_CONVERT",
                "partial project conversion failed; see the migration report",
            )
        if report_path is not None and not preview:
            write_report(report_path, report)
        stdout.write(report.canonical_bytes().decode("utf-8"))
        return 0
    if not args.input:
        raise coded_error(
            "MINT_CONVERT",
            "pass INPUT or --project DIR; stdin uses - and requires --from",
        )
    fmt = resolve_input_format(path=args.input, from_format=args.from_format)
    if args.input == "-":
        source = stdin.read()
        unit = convert_text(source, format=fmt, unit_id="root", logical_source="-")
        item = ConversionItem(
            source="-",
            format=unit.format,
            destination=args.output or "-",
            status="checked" if check else "converted",
            source_digest=unit.source_digest,
            mint_digest=unit.mint_digest,
            ir_digest=unit.ir_digest,
            lossy=unit.lossy,
            excluded=unit.excluded,
        )
        if args.output:
            dest = Path(args.output)
            _write_converted(dest, unit, replace=replace, check=check, preview=preview)
        elif not check and not preview:
            stdout.write(unit.mint_source)
        _maybe_write_report(report_path, item, preview=preview)
        return 0
    path = Path(args.input)
    dest = Path(args.output) if args.output else path.with_suffix(".mint")
    unit, item = convert_path(
        path,
        format=fmt,
        destination=dest,
        replace=replace,
        check=check,
        preview=preview,
        write=bool(args.output) and not check and not preview,
    )
    if args.output:
        _write_converted(dest, unit, replace=replace, check=check, preview=preview)
    elif not check and not preview:
        stdout.write(unit.mint_source)
    _maybe_write_report(report_path, item, preview=preview)
    return 0


def _write_converted(
    dest: Path,
    unit: Any,
    *,
    replace: bool,
    check: bool,
    preview: bool,
) -> None:
    if check or preview:
        return
    if dest.exists() and not replace:
        raise coded_error(
            "MINT_CONVERT",
            f"refuse existing destination {dest.name}; pass --replace to replace safely",
        )
    if dest.is_symlink() or dest.parent.is_symlink():
        raise coded_error("MINT_CONVERT", "refuse symlink destination or unsafe parent")
    if ".." in dest.parts:
        raise coded_error("MINT_CONVERT", "unsafe path; no parent traversal")
    tmp = dest.with_name(f"{dest.name}.tmp")
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(unit.mint_source, encoding="utf-8")
        os.replace(tmp, dest)
    except OSError:
        if tmp.exists():
            tmp.unlink()
        raise


def _maybe_write_report(report_path: Path | None, item: Any, *, preview: bool) -> None:
    from opsdevcode_specmint.mint.convert import MigrationReport, write_report

    if report_path is None or preview:
        return
    report = MigrationReport(ok=True, items=(item,), preview=preview)
    write_report(report_path, report)


def _run_fmt(args: argparse.Namespace, *, stdin: IO[str], stdout: TextIO) -> int:
    paths: list[str] = list(args.paths)
    write = bool(args.write)
    check = bool(args.check)
    if write and check:
        raise as_mint_error(RuntimeError("use --write or --check, not both"))
    if not paths or paths == ["-"]:
        source = stdin.read()
        formatted = format_source(source, unit_id="root")
        if check and formatted != source:
            raise as_mint_error(RuntimeError("stdin is not formatted; run mint fmt"))
        if not write:
            stdout.write(formatted)
        return 0
    changed = False
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            raise as_mint_error(
                RuntimeError(
                    f"missing Mint input {display_path(path)}; pass an existing declared file"
                )
            )
        source = path.read_text(encoding="utf-8")
        formatted = format_source(source, unit_id=path.name)
        parse_mint_text(formatted, unit_id=path.name)
        if formatted != source:
            changed = True
            if write:
                path.write_text(formatted, encoding="utf-8")
        if not write and not check:
            if len(paths) > 1:
                stdout.write(f"// {path.name}\n")
            stdout.write(formatted)
    if check and changed:
        raise as_mint_error(RuntimeError("Mint sources are not formatted; run mint fmt --write"))
    return 0


def _run_init(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if args.list_templates:
        stdout.write(render_payload(list_template_payload(), output_format=args.output_format))
        return 0
    directory = Path(args.directory) if args.directory else Path.cwd()
    template = args.template or DEFAULT_TEMPLATE
    manifest = init_project(directory, name=args.name, template=template)
    stdout.write(
        render_payload(
            {
                "manifest": MANIFEST_NAME,
                "name": manifest.name,
                "ok": True,
                "root": manifest.root,
                "template": template,
            },
            output_format=args.output_format,
        )
    )
    return 0


def _run_doctor(args: argparse.Namespace, *, stdout: TextIO) -> int:
    project = Path(args.project) if args.project else None
    report = run_doctor(project=project)
    stdout.write(render_payload(report.to_dict(), output_format=args.output_format))
    return 0 if report.ok else 1


def _run_lock(args: argparse.Namespace, *, stdout: TextIO) -> int:
    manifest = _load_manifest(args)
    if args.check:
        lockfile = check_lockfile(manifest)
    else:
        lockfile = build_lockfile(manifest)
        write_lockfile(manifest, lockfile)
    stdout.write(
        json.dumps(
            {
                "digest": lockfile.ir_digest,
                "integrations": [
                    {
                        "artifactDigest": item.artifact_digest,
                        "identity": item.identity,
                        "manifestDigest": item.manifest_digest,
                        "version": item.version,
                    }
                    for item in lockfile.integrations
                ],
                "lock": manifest.lock_path.name,
                "ok": True,
                "updated": not args.check,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return 0


def _load_manifest(args: argparse.Namespace) -> ProjectManifest:
    start = Path(args.project) if getattr(args, "project", None) else Path.cwd()
    return load_manifest(discover_manifest(start))


def _load_program(args: argparse.Namespace, *, stdin: IO[str]) -> DeclaredProgram:
    paths = tuple(Path(item) for item in getattr(args, "paths", []) or [])
    graph = getattr(args, "graph", None)
    project = getattr(args, "project", None)
    profile = getattr(args, "profile", None)
    locked = bool(getattr(args, "locked", False))
    if (paths or graph) and (project or profile):
        raise coded_error(
            "MINT_PROJECT",
            "use standalone paths/--graph or --project, not both",
        )
    if locked and (paths or graph):
        raise coded_error(
            "MINT_LOCK",
            "pass --locked with --project; standalone paths are not lock-checked",
        )
    if graph:
        return load_declared_graph(Path(graph))
    if paths:
        stdin_text = stdin.read() if any(str(item) == "-" for item in paths) else None
        return load_declared_paths(paths, root=args.root, stdin_text=stdin_text)
    manifest = _load_manifest(args)
    if locked:
        return load_locked_program(manifest)
    return load_project_units(manifest)


def _load_json(path_arg: str, *, stdin: IO[str]) -> dict[str, Any]:
    if path_arg == "-":
        raw = stdin.read()
    else:
        path = Path(path_arg)
        if not path.is_file():
            raise as_mint_error(
                RuntimeError(f"missing MintIR file {display_path(path)}; pass an existing file")
            )
        raw = path.read_text(encoding="utf-8")
    document = json.loads(raw)
    if not isinstance(document, dict):
        raise as_mint_error(RuntimeError("MintIR inspect input must be a JSON object"))
    return document


def _version_line() -> str:
    return f"mint language {_LANGUAGE_EDITION} (specmint {__version__})\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mint",
        description=(
            "Check, compile, convert, doctor, format, lock, inspect, plan, and serve Mint LSP "
            "offline."
        ),
    )
    parser.add_argument(
        "--version",
        action="store_true",
        dest="show_version",
        help="Print the Mint language edition and SpecMint service version",
    )
    parser.add_argument(
        "--output-format",
        choices=("json", "human"),
        default=DEFAULT_OUTPUT_FORMAT,
        dest="output_format",
        help="json or human for diagnostics and first-run output; not inferred from the TTY",
    )
    sub = parser.add_subparsers(dest="command")
    check = sub.add_parser("check", help="Type-check and catalog-check declared Mint units")
    _add_program_args(check)
    compile_cmd = sub.add_parser("compile", help="Emit canonical MintIR")
    _add_program_args(compile_cmd)
    plan_cmd = sub.add_parser("plan", help="Emit a closed MintPlanResult ArtifactSet")
    _add_program_args(plan_cmd)
    plan_cmd.add_argument(
        "--adapter",
        help="Optional builtin adapter id; default routes from verb and target kind",
    )
    plan_cmd.add_argument(
        "--artifacts",
        help="Write ArtifactSet files atomically under a confined directory",
    )
    plan_cmd.add_argument(
        "--snapshot",
        action="append",
        dest="snapshots",
        help="Explicit mint.repository-snapshot/v0 JSON; required for repo.github targets",
    )
    plan_cmd.add_argument(
        "--output",
        help="Write the MintPlanResult JSON to a confined file; stdout still receives the plan",
    )
    integrations_cmd = sub.add_parser(
        "integrations",
        help="Search, inspect, pin, verify, and test Mint integrations",
    )
    integrations_sub = integrations_cmd.add_subparsers(dest="integrations_command")
    integrations_sub.add_parser("list", help="List builtin integration identities")
    search_integration = integrations_sub.add_parser(
        "search", help="Search local catalog records without network"
    )
    search_integration.add_argument("query", nargs="?", default="", help="Substring filter")
    search_integration.add_argument("--capability", default="", help="Capability id filter")
    search_integration.add_argument("--target-kind", default="", help="Target kind filter")
    inspect_integration = integrations_sub.add_parser("inspect", help="Inspect one integration")
    inspect_integration.add_argument("identity")
    check_integration = integrations_sub.add_parser("check", help="Validate a manifest file")
    check_integration.add_argument("manifest")
    resolve_integration = integrations_sub.add_parser("resolve", help="Resolve one realization")
    resolve_integration.add_argument("--project", required=True)
    resolve_integration.add_argument("--capability", required=True)
    resolve_integration.add_argument("--capability-version", required=True)
    resolve_integration.add_argument("--target", required=True)
    resolve_integration.add_argument("--target-kind", required=True)
    resolve_integration.add_argument("--phase", required=True)
    add_integration = integrations_sub.add_parser(
        "add",
        help="Pin a local, packaged, or github-catalog integration; never pip or execute",
    )
    add_integration.add_argument("identity", nargs="?", default="", help="Packaged identity")
    add_integration.add_argument("--project", required=True)
    add_integration.add_argument(
        "--local",
        default="",
        help="Project-relative mint.integration/v0 path; never a URL",
    )
    remove_integration = integrations_sub.add_parser("remove", help="Unpin one project integration")
    remove_integration.add_argument("identity")
    remove_integration.add_argument("--project", required=True)
    verify_integration = integrations_sub.add_parser(
        "verify", help="Recompute lockfile integration digests without executing"
    )
    verify_integration.add_argument("--project", required=True)
    status_integration = integrations_sub.add_parser(
        "status", help="Show pinned integration process status without executing"
    )
    status_integration.add_argument("--project", required=True)
    update_integration = integrations_sub.add_parser(
        "update", help="Refresh lockfile pins from packaged or local sources"
    )
    update_integration.add_argument("--project", required=True)
    conformance = integrations_sub.add_parser("conformance", help="Alias of mint integrations test")
    conformance.add_argument("integration", nargs="?", default="")
    conformance.add_argument(
        "--local",
        default="",
        help="Local integration directory or mint-integration.json; never a URL",
    )
    test_cmd = integrations_sub.add_parser(
        "test", help="Run the observe/plan/verify/evidence conformance kit"
    )
    test_cmd.add_argument(
        "integration",
        nargs="?",
        help="Integration identity (default: local.sandbox.ensure_marker)",
    )
    test_cmd.add_argument(
        "--local",
        default="",
        help="Local integration directory or mint-integration.json; never a URL",
    )
    adapters_cmd = sub.add_parser("adapters", help="Deprecated alias of mint integrations")
    adapters_sub = adapters_cmd.add_subparsers(dest="adapters_command")
    adapters_sub.add_parser("list", help="Print builtin AdapterManifest documents")
    inspect_adapter = adapters_sub.add_parser("inspect", help="Print one builtin AdapterManifest")
    inspect_adapter.add_argument("adapter_id", help="Builtin adapter id")
    repository_cmd = sub.add_parser("repository", help="Validate supplied repository snapshots")
    repository_sub = repository_cmd.add_subparsers(dest="repository_command")
    snapshot_cmd = repository_sub.add_parser("snapshot", help="Snapshot contracts")
    snapshot_sub = snapshot_cmd.add_subparsers(dest="snapshot_command")
    snapshot_check = snapshot_sub.add_parser("check", help="Validate a snapshot without fetching")
    snapshot_check.add_argument("snapshot_path", help="mint.repository-snapshot/v0 JSON path")
    convert_cmd = sub.add_parser(
        "convert",
        help="Convert legacy JSON/YAML/Markdown authoring to canonical Mint",
    )
    convert_cmd.add_argument("input", nargs="?", help="Legacy path, or - for stdin")
    convert_cmd.add_argument(
        "--from",
        dest="from_format",
        help="json, yaml, markdown, or mint; required for stdin",
    )
    convert_cmd.add_argument(
        "--format",
        dest="from_format",
        help="Alias of --from (product CLI spelling)",
    )
    convert_cmd.add_argument("--output", help="Write Mint to this path; never the input path")
    convert_cmd.add_argument(
        "--check",
        action="store_true",
        help="Convert and verify equivalence without writing Mint",
    )
    convert_cmd.add_argument("--report", help="Write mint.migration-report/v0 JSON")
    convert_cmd.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing regular .mint destination",
    )
    convert_cmd.add_argument(
        "--preview",
        action="store_true",
        help="Inventory and map a project; write nothing",
    )
    _add_project_arg(convert_cmd)
    fmt = sub.add_parser("fmt", help="Reprint Mint source with stable trivia")
    fmt.add_argument("paths", nargs="*", help="Mint paths, or omit / - for stdin")
    fmt.add_argument("--write", action="store_true", help="Rewrite files in place")
    fmt.add_argument("--check", action="store_true", help="Exit 1 when formatting would change")
    inspect_cmd = sub.add_parser("inspect", help="Recheck a MintIR document digest")
    inspect_cmd.add_argument("path", help="MintIR JSON path, or - for stdin")
    init_cmd = sub.add_parser("init", help="Write mint.toml and a starter unit from a template")
    init_cmd.add_argument("directory", nargs="?", help="Project directory (default: cwd)")
    init_cmd.add_argument("--name", help="Project name (lowercase DNS-label)")
    init_cmd.add_argument(
        "--template",
        help=f"Init template id (default: {DEFAULT_TEMPLATE})",
    )
    init_cmd.add_argument(
        "--list-templates",
        action="store_true",
        help="Print available init templates and exit",
    )
    _add_output_format_arg(init_cmd)
    doctor_cmd = sub.add_parser("doctor", help="Run offline first-run diagnostics")
    _add_project_arg(doctor_cmd)
    _add_output_format_arg(doctor_cmd)
    lock_cmd = sub.add_parser("lock", help="Write canonical mint.lock from mint.toml")
    lock_cmd.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when mint.lock is missing or stale",
    )
    _add_project_arg(lock_cmd)
    project_cmd = sub.add_parser("project", help="Operate on a mint.toml project")
    project_sub = project_cmd.add_subparsers(dest="project_command")
    project_check = project_sub.add_parser(
        "check", help="Lock-check and compile a mint.toml project"
    )
    _add_project_arg(project_check)
    project_check.add_argument("--profile", help="Named profile of declared targets")
    project_check.add_argument(
        "--locked",
        action="store_true",
        help="Require mint.lock (default for mint project check)",
    )
    sub.add_parser(
        "lsp",
        help="Run the compiler-backed language server on stdio (no network listener)",
    )
    sub.add_parser("version", help="Print the Mint language edition")
    return parser


def _add_program_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("paths", nargs="*", help="Declared .mint files, or - for stdin")
    parser.add_argument("--root", help="Logical root unit id (filename of the root unit)")
    parser.add_argument(
        "--graph",
        help="Declared graph.json next to its units; no directory search",
    )
    parser.add_argument("--profile", help="Named profile of declared targets (project mode)")
    parser.add_argument(
        "--locked",
        action="store_true",
        help="Require mint.lock; only valid with --project",
    )
    _add_project_arg(parser)


def _add_project_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project",
        help="Directory or mint.toml path used to discover the project manifest",
    )


def _add_output_format_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-format",
        choices=("json", "human"),
        default=DEFAULT_OUTPUT_FORMAT,
        dest="output_format",
        help="json or human; not inferred from the TTY",
    )


def language_command_names() -> frozenset[str]:
    parser = _build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if action.dest == "command" and isinstance(choices, dict):
            return frozenset(str(name) for name in choices)
    return frozenset()

"""Deterministic Mint project manifest and lockfile. Offline; no registries."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opsdevcode_specmint.mint.catalog import sorted_catalog_ids
from opsdevcode_specmint.mint.compile import SourceUnit, compile_program
from opsdevcode_specmint.mint.errors import MintError, coded_error
from opsdevcode_specmint.mint.inputs import DeclaredProgram, extension_from_dict
from opsdevcode_specmint.mint.ir import MintIR, canonical_json_bytes
from opsdevcode_specmint.mint.templates import DEFAULT_TEMPLATE, load_template

PROJECT_SCHEMA = "mint.project/v0"
LOCK_SCHEMA = "mint.lock/v0"
MANIFEST_NAME = "mint.toml"
LOCK_NAME = "mint.lock"
_NAME = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_EDITIONS = frozenset({"v0", "v1alpha1"})
_CREDENTIAL_KEYS = frozenset(
    {
        "access_key",
        "credential",
        "password",
        "private_key",
        "secret",
        "token",
    }
)


@dataclass(frozen=True, slots=True)
class ProjectProfile:
    name: str
    targets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectIntegration:
    source: str
    version: str
    local: str
    capabilities: tuple[str, ...]
    targets: tuple[str, ...]
    phases: tuple[str, ...]
    realization: str


@dataclass(frozen=True, slots=True)
class LockedIntegration:
    identity: str
    version: str
    protocol: str
    manifest_digest: str
    artifact_digest: str
    schema_digests: tuple[tuple[str, str], ...]
    capabilities: tuple[tuple[str, str], ...]
    target_kinds: tuple[str, ...]
    phases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectManifest:
    schema: str
    name: str
    edition: str
    root: str
    units: tuple[str, ...]
    catalogs: tuple[str, ...]
    extension_paths: tuple[str, ...]
    profiles: tuple[ProjectProfile, ...]
    directory: Path
    integrations: tuple[ProjectIntegration, ...] = ()

    @property
    def path(self) -> Path:
        return self.directory / MANIFEST_NAME

    @property
    def lock_path(self) -> Path:
        return self.directory / LOCK_NAME

    def profile(self, name: str) -> ProjectProfile:
        for item in self.profiles:
            if item.name == name:
                return item
        raise coded_error(
            "MINT_PROFILE",
            f"unknown profile {name}; declare it under [profiles.{name}] in {MANIFEST_NAME}",
        )


@dataclass(frozen=True, slots=True)
class Lockfile:
    schema: str
    name: str
    edition: str
    root: str
    ir_digest: str
    catalog_digest: str
    units: tuple[tuple[str, str], ...]
    extensions: tuple[tuple[str, str, str], ...]
    integrations: tuple[LockedIntegration, ...] = ()

    def to_canonical_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "catalogDigest": self.catalog_digest,
            "edition": self.edition,
            "extensions": [
                {"digest": digest, "namespace": namespace, "version": version}
                for namespace, version, digest in self.extensions
            ],
            "irDigest": self.ir_digest,
            "name": self.name,
            "root": self.root,
            "schema": self.schema,
            "units": [{"digest": digest, "path": path} for path, digest in self.units],
        }
        if self.integrations:
            document["integrations"] = [
                {
                    "artifactDigest": item.artifact_digest,
                    "capabilities": [
                        {"id": capability_id, "version": capability_version}
                        for capability_id, capability_version in item.capabilities
                    ],
                    "identity": item.identity,
                    "manifestDigest": item.manifest_digest,
                    "phases": list(item.phases),
                    "protocol": item.protocol,
                    "schemaDigests": [
                        {"digest": digest, "identity": identity}
                        for identity, digest in item.schema_digests
                    ],
                    "targetKinds": list(item.target_kinds),
                    "version": item.version,
                }
                for item in self.integrations
            ]
        return document

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_canonical_dict())


def closed_catalog_document() -> dict[str, Any]:
    return {"ids": list(sorted_catalog_ids()), "version": "v0"}


def catalog_digest() -> str:
    return _digest_bytes(canonical_json_bytes(closed_catalog_document()))


def discover_manifest(start: Path) -> Path:
    current = start.expanduser()
    if not current.exists():
        raise coded_error(
            "MINT_PROJECT",
            "missing start path; pass an existing directory to mint --project",
        )
    resolved = current.resolve()
    if resolved.is_file():
        resolved = resolved.parent
    for directory in (resolved, *resolved.parents):
        candidate = directory / MANIFEST_NAME
        if candidate.is_file():
            return candidate
    raise coded_error(
        "MINT_PROJECT",
        f"missing {MANIFEST_NAME} under this directory; run mint init or pass --project",
    )


def load_manifest(path: Path) -> ProjectManifest:
    if not path.is_file():
        raise coded_error(
            "MINT_PROJECT",
            f"missing {MANIFEST_NAME}; run mint init or pass --project to a "
            f"{MANIFEST_NAME} directory",
        )
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise coded_error("MINT_PROJECT", f"fix {MANIFEST_NAME}: {exc}") from exc
    if not isinstance(raw, dict):
        raise coded_error("MINT_PROJECT", f"set {MANIFEST_NAME} to a TOML table")
    allowed = {
        "schema",
        "name",
        "edition",
        "root",
        "units",
        "catalogs",
        "extensions",
        "profiles",
        "integrations",
    }
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise coded_error(
            "MINT_PROJECT",
            f"remove unknown keys {unknown} from {MANIFEST_NAME}; schema is {PROJECT_SCHEMA}",
        )
    schema = str(raw.get("schema", ""))
    if schema != PROJECT_SCHEMA:
        raise coded_error(
            "MINT_PROJECT",
            f"set {MANIFEST_NAME} schema to {PROJECT_SCHEMA}; got {schema or 'empty'}",
        )
    name = str(raw.get("name", ""))
    if not _NAME.fullmatch(name):
        raise coded_error(
            "MINT_PROJECT",
            f"set {MANIFEST_NAME} name to a lowercase DNS-label like local-marker",
        )
    edition = str(raw.get("edition", ""))
    if edition not in _EDITIONS:
        raise coded_error(
            "MINT_PROJECT",
            f"set {MANIFEST_NAME} edition to v0; got {edition or 'empty'}",
        )
    root = _declared_relative(str(raw.get("root", "")), suffix=".mint")
    units_raw = raw.get("units")
    if not isinstance(units_raw, list) or not units_raw:
        raise coded_error(
            "MINT_PROJECT",
            f"set {MANIFEST_NAME} units to a non-empty list of project-relative .mint paths",
        )
    units = tuple(_declared_relative(str(item), suffix=".mint") for item in units_raw)
    if root not in units:
        raise coded_error("MINT_PROJECT", f"include root {root} in {MANIFEST_NAME} units")
    _reject_duplicates(units, "unit")
    catalogs_raw = raw.get("catalogs", [])
    if catalogs_raw and not isinstance(catalogs_raw, list):
        raise coded_error(
            "MINT_PROJECT", f"set {MANIFEST_NAME} catalogs to a list of relative JSON paths"
        )
    catalogs = tuple(_declared_relative(str(item), suffix=".json") for item in catalogs_raw or [])
    extensions_raw = raw.get("extensions", [])
    if extensions_raw and not isinstance(extensions_raw, list):
        raise coded_error(
            "MINT_PROJECT", f"set {MANIFEST_NAME} extensions to a list of tables with path"
        )
    extension_paths = tuple(_extension_path(item) for item in extensions_raw or [])
    profiles = _load_profiles(raw.get("profiles", {}))
    integrations = _load_integrations(raw.get("integrations", []))
    return ProjectManifest(
        schema=schema,
        name=name,
        edition=edition,
        root=root,
        units=units,
        catalogs=catalogs,
        extension_paths=extension_paths,
        profiles=profiles,
        directory=path.parent.resolve(),
        integrations=integrations,
    )


def init_project(
    directory: Path,
    *,
    name: str | None = None,
    template: str | None = None,
) -> ProjectManifest:
    target = directory.expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / MANIFEST_NAME
    if manifest_path.is_file():
        raise coded_error(
            "MINT_PROJECT",
            f"{MANIFEST_NAME} already exists; keep it or choose another directory",
        )
    project_name = name or _default_name(target)
    if not _NAME.fullmatch(project_name):
        raise coded_error(
            "MINT_PROJECT",
            "set project name to a lowercase DNS-label like local-marker",
        )
    chosen = load_template(template or DEFAULT_TEMPLATE)
    unit = "main.mint"
    profile_block = f"\n{chosen.manifest_profiles}" if chosen.manifest_profiles else ""
    text = (
        f'schema = "{PROJECT_SCHEMA}"\n'
        f'name = "{project_name}"\n'
        f'edition = "v0"\n'
        f'root = "{unit}"\n'
        f'units = ["{unit}"]\n'
        f"{profile_block}"
    )
    _atomic_write_text(manifest_path, text)
    starter = target / unit
    if not starter.exists():
        _atomic_write_text(starter, chosen.mint_source)
    return load_manifest(manifest_path)


def build_lockfile(manifest: ProjectManifest) -> Lockfile:
    program = load_project_units(manifest)
    _assert_catalog_files(manifest)
    result = compile_program(root=program.root, units=program.units, extensions=program.extensions)
    if not result.ok or result.digest is None:
        if result.diagnostic is None:
            raise coded_error("MINT_STATIC", "compile failed without a diagnostic")
        raise MintError(result.diagnostic)
    units = tuple(sorted((unit.unit_id, _digest_text(unit.source)) for unit in program.units))
    extensions = tuple(sorted(_extension_lock_entries(manifest)))
    integrations = _integration_lock_entries(manifest)
    return Lockfile(
        schema=LOCK_SCHEMA,
        name=manifest.name,
        edition=manifest.edition,
        root=manifest.root,
        ir_digest=result.digest,
        catalog_digest=catalog_digest(),
        units=units,
        extensions=extensions,
        integrations=integrations,
    )


def write_lockfile(manifest: ProjectManifest, lockfile: Lockfile) -> None:
    _atomic_write_bytes(manifest.lock_path, lockfile.canonical_bytes())


def render_manifest(manifest: ProjectManifest) -> str:
    lines = [
        f'schema = "{manifest.schema}"',
        f'name = "{manifest.name}"',
        f'edition = "{manifest.edition}"',
        f'root = "{manifest.root}"',
        f"units = {_toml_string_array(manifest.units)}",
    ]
    if manifest.catalogs:
        lines.append(f"catalogs = {_toml_string_array(manifest.catalogs)}")
    for relative in manifest.extension_paths:
        lines.extend(["", "[[extensions]]", f'path = "{relative}"'])
    for profile in manifest.profiles:
        lines.extend(
            [
                "",
                f"[profiles.{profile.name}]",
                f"targets = {_toml_string_array(profile.targets)}",
            ]
        )
    for item in manifest.integrations:
        lines.extend(
            [
                "",
                "[[integrations]]",
                f'source = "{item.source}"',
                f'version = "{item.version}"',
            ]
        )
        if item.local:
            lines.append(f'local = "{item.local}"')
        lines.extend(
            [
                f"capabilities = {_toml_string_array(item.capabilities)}",
                f"targets = {_toml_string_array(item.targets)}",
                f"phases = {_toml_string_array(item.phases)}",
            ]
        )
        if item.realization:
            lines.append(f'realization = "{item.realization}"')
    return "\n".join(lines) + "\n"


def write_manifest(manifest: ProjectManifest) -> None:
    _atomic_write_text(manifest.path, render_manifest(manifest))


def _toml_string_array(items: tuple[str, ...]) -> str:
    return "[" + ", ".join(f'"{item}"' for item in items) + "]"


def load_lockfile(path: Path) -> Lockfile:
    if not path.is_file():
        raise coded_error(
            "MINT_LOCK",
            f"missing {path}; run mint lock in the project directory",
        )
    raw = path.read_text(encoding="utf-8")
    try:
        document = json.loads(raw)
    except ValueError as exc:
        raise coded_error(
            "MINT_LOCK",
            f"malformed {path.name}: invalid JSON; rewrite it with mint lock",
        ) from exc
    if not isinstance(document, dict):
        raise coded_error("MINT_LOCK", f"malformed {path.name}: set mint.lock to a JSON object")
    units_raw = document.get("units")
    extensions_raw = document.get("extensions")
    if not isinstance(units_raw, list) or (
        extensions_raw is not None and not isinstance(extensions_raw, list)
    ):
        raise coded_error(
            "MINT_LOCK", f"malformed {path.name}: units and extensions must be arrays"
        )
    try:
        expected = Lockfile(
            schema=str(document.get("schema", "")),
            name=str(document.get("name", "")),
            edition=str(document.get("edition", "")),
            root=str(document.get("root", "")),
            ir_digest=str(document.get("irDigest", "")),
            catalog_digest=str(document.get("catalogDigest", "")),
            units=tuple(
                (_declared_relative(str(item["path"]), suffix=".mint"), str(item["digest"]))
                for item in units_raw
            ),
            extensions=tuple(
                (str(item["namespace"]), str(item["version"]), str(item["digest"]))
                for item in extensions_raw or []
            ),
            integrations=_locked_integrations(document.get("integrations", [])),
        )
    except (KeyError, TypeError) as exc:
        raise coded_error(
            "MINT_LOCK",
            f"malformed {path.name}: each unit needs path and digest",
        ) from exc
    if expected.schema != LOCK_SCHEMA:
        raise coded_error(
            "MINT_LOCK",
            f"malformed {LOCK_NAME}: schema must be {LOCK_SCHEMA}; "
            f"got {expected.schema or 'empty'}",
        )
    if raw.encode("utf-8") != expected.canonical_bytes():
        raise coded_error(
            "MINT_LOCK",
            f"malformed {path.name}: stored JSON is not canonical; rewrite it with mint lock",
        )
    return expected


def check_lockfile(manifest: ProjectManifest) -> Lockfile:
    on_disk = load_lockfile(manifest.lock_path)
    computed = build_lockfile(manifest)
    if computed.catalog_digest != on_disk.catalog_digest:
        raise coded_error(
            "MINT_CATALOG",
            "catalog digest does not match mint.lock; run mint lock after catalog changes",
        )
    if computed.extensions != on_disk.extensions:
        raise coded_error(
            "MINT_EXTENSION",
            "extension digest does not match mint.lock; run mint lock after extension changes",
        )
    if computed.canonical_bytes() != on_disk.canonical_bytes():
        raise coded_error(
            "MINT_LOCK",
            f"{manifest.lock_path.name} is stale; run mint lock to refresh hashes",
        )
    return on_disk


def load_locked_program(manifest: ProjectManifest) -> DeclaredProgram:
    check_lockfile(manifest)
    return load_project_units(manifest)


def load_project_units(manifest: ProjectManifest) -> DeclaredProgram:
    _assert_catalog_files(manifest)
    units = tuple(
        SourceUnit(
            relative, _contained_file(manifest.directory, relative).read_text(encoding="utf-8")
        )
        for relative in manifest.units
    )
    extensions = tuple(
        extension_from_dict(
            json.loads(_contained_file(manifest.directory, relative).read_text(encoding="utf-8"))
        )
        for relative in manifest.extension_paths
    )
    return DeclaredProgram(
        root=manifest.root,
        units=units,
        extensions=extensions,
        origin=str(manifest.path),
    )


def apply_profile(manifest: ProjectManifest, name: str, ir: MintIR) -> None:
    profile = manifest.profile(name)
    declared = {str(item.get("id")) for item in ir.targets}
    missing = [target for target in profile.targets if target not in declared]
    if missing:
        raise coded_error(
            "MINT_PROFILE",
            f"profile {name} lists undeclared targets {missing}; use ids from the program",
        )


def _load_profiles(raw: object) -> tuple[ProjectProfile, ...]:
    if not raw:
        return ()
    if not isinstance(raw, dict):
        raise coded_error(
            "MINT_PROFILE", f"set {MANIFEST_NAME} profiles to a table of named profiles"
        )
    profiles: list[ProjectProfile] = []
    for name, body in raw.items():
        if not isinstance(body, dict):
            raise coded_error("MINT_PROFILE", f"set [profiles.{name}] to a table with targets")
        credential = sorted(
            key
            for key in body
            if str(key).lower() in _CREDENTIAL_KEYS or "secret" in str(key).lower()
        )
        if credential:
            raise coded_error(
                "MINT_PROFILE",
                f"remove credentials {credential} from [profiles.{name}]; "
                "profiles declare targets only",
            )
        unknown = sorted(set(body) - {"targets"})
        if unknown:
            raise coded_error(
                "MINT_PROFILE",
                f"remove unknown keys {unknown} from [profiles.{name}]; only targets are allowed",
            )
        targets_raw = body.get("targets", [])
        if not isinstance(targets_raw, list) or not targets_raw:
            raise coded_error(
                "MINT_PROFILE",
                f"set [profiles.{name}] targets to a non-empty list of declared target ids",
            )
        targets = tuple(str(item) for item in targets_raw)
        profiles.append(ProjectProfile(name=str(name), targets=targets))
    return tuple(sorted(profiles, key=lambda item: item.name))


def _load_integrations(raw: object) -> tuple[ProjectIntegration, ...]:
    if raw in (None, []):
        return ()
    if not isinstance(raw, list):
        raise coded_error("MINT_INTEGRATION", "set integrations to an array of tables")
    items: list[ProjectIntegration] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise coded_error("MINT_INTEGRATION", "each integration requirement must be a table")
        allowed = {
            "source",
            "version",
            "local",
            "capabilities",
            "targets",
            "phases",
            "realization",
        }
        unknown = sorted(set(entry) - allowed)
        if unknown:
            raise coded_error(
                "MINT_INTEGRATION",
                f"remove unknown integration keys {unknown}",
            )
        _reject_secret_keys(entry)
        source = str(entry.get("source", ""))
        version = str(entry.get("version", ""))
        local = str(entry.get("local", ""))
        if local:
            local = _declared_relative(local, suffix=".json")
        capabilities = tuple(str(item) for item in entry.get("capabilities", []))
        targets = tuple(str(item) for item in entry.get("targets", []))
        phases = tuple(str(item) for item in entry.get("phases", []))
        if not source or not version or not capabilities or not targets or not phases:
            raise coded_error(
                "MINT_INTEGRATION",
                "integration requirements need source, version, capabilities, targets, and phases",
            )
        items.append(
            ProjectIntegration(
                source=source,
                version=version,
                local=local,
                capabilities=capabilities,
                targets=targets,
                phases=phases,
                realization=str(entry.get("realization", "")),
            )
        )
    identities = [item.source for item in items]
    _reject_duplicates(tuple(identities), "integration")
    return tuple(sorted(items, key=lambda item: item.source))


def _integration_lock_entries(manifest: ProjectManifest) -> tuple[LockedIntegration, ...]:
    if not manifest.integrations:
        return ()
    from opsdevcode_specmint.integration.models import parse_manifest
    from opsdevcode_specmint.integration.reference_server import artifact_digest, manifest_document

    pinned: list[LockedIntegration] = []
    for requirement in manifest.integrations:
        if requirement.local:
            loaded = _contained_file(manifest.directory, requirement.local)
            text = loaded.read_text(encoding="utf-8")
            manifest_doc = parse_manifest(json.loads(text)).document
            artifact_file = manifest.directory / requirement.local
            artifact_file = artifact_file.parent / "implementation" / "reference_server.py"
            if artifact_file.is_symlink() or not artifact_file.is_file():
                raise coded_error(
                    "MINT_INTEGRATION",
                    "local integration artifact must be implementation/reference_server.py",
                )
            resolved = artifact_file.resolve()
            try:
                resolved.relative_to(manifest.directory.resolve())
            except ValueError:
                raise coded_error(
                    "MINT_PATH",
                    "local integration artifact escapes the project",
                ) from None
            pinned_artifact = _digest_bytes(artifact_file.read_bytes())
        else:
            if requirement.source != "local.sandbox.ensure_marker":
                raise coded_error(
                    "MINT_INTEGRATION",
                    f"missing local manifest for {requirement.source}; registry deferred",
                )
            manifest_doc = manifest_document()
            pinned_artifact = artifact_digest()
        identity_ok = manifest_doc["identity"] == requirement.source
        version_ok = manifest_doc["version"] == requirement.version
        if not identity_ok or not version_ok:
            raise coded_error(
                "MINT_INTEGRATION",
                f"integration {requirement.source} does not match the required version",
            )
        if manifest_doc["artifact"]["digest"] != pinned_artifact:
            raise coded_error(
                "MINT_DIGEST",
                f"artifact digest mismatch for {requirement.source}",
            )
        pinned.append(
            LockedIntegration(
                identity=str(manifest_doc["identity"]),
                version=str(manifest_doc["version"]),
                protocol="mint.protocol/v0",
                manifest_digest=_digest_bytes(canonical_json_bytes(manifest_doc)),
                artifact_digest=pinned_artifact,
                schema_digests=(("mint.integration/v0", _schema_digest()),),
                capabilities=tuple(
                    (str(item["id"]), str(item["version"])) for item in manifest_doc["capabilities"]
                ),
                target_kinds=tuple(manifest_doc["targetKinds"]),
                phases=tuple(manifest_doc["phases"]),
            )
        )
    return tuple(pinned)


def _schema_digest() -> str:
    schema_path = (
        Path(__file__).resolve().parents[1] / "integration" / "schemas" / "mint.integration.v0.json"
    )
    return _digest_bytes(schema_path.read_bytes())


def _locked_integrations(raw: object) -> tuple[LockedIntegration, ...]:
    if raw in (None, []):
        return ()
    if not isinstance(raw, list):
        raise coded_error("MINT_LOCK", "mint.lock integrations must be an array")
    items: list[LockedIntegration] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise coded_error("MINT_LOCK", "each locked integration must be an object")
        try:
            items.append(
                LockedIntegration(
                    identity=str(entry["identity"]),
                    version=str(entry["version"]),
                    protocol=str(entry["protocol"]),
                    manifest_digest=str(entry["manifestDigest"]),
                    artifact_digest=str(entry["artifactDigest"]),
                    schema_digests=tuple(
                        (str(item["identity"]), str(item["digest"]))
                        for item in entry["schemaDigests"]
                    ),
                    capabilities=tuple(
                        (str(item["id"]), str(item["version"])) for item in entry["capabilities"]
                    ),
                    target_kinds=tuple(str(item) for item in entry["targetKinds"]),
                    phases=tuple(str(item) for item in entry["phases"]),
                )
            )
        except (KeyError, TypeError) as exc:
            raise coded_error(
                "MINT_LOCK",
                "locked integration is missing identity, version, or digests",
            ) from exc
    return tuple(items)


def _reject_secret_keys(raw: dict[str, Any]) -> None:
    for key in raw:
        lowered = str(key).lower()
        secretish = {"pat", "api_key", "authorization"}
        if lowered in _CREDENTIAL_KEYS or lowered in secretish:
            raise coded_error(
                "MINT_PERMISSION",
                f"remove secret-shaped field {key} from the integration requirement",
            )


def _extension_path(raw: object) -> str:
    if not isinstance(raw, dict) or "path" not in raw:
        raise coded_error("MINT_PROJECT", 'set each [[extensions]] entry to { path = "file.json" }')
    extra = sorted(set(raw) - {"path"})
    if extra:
        raise coded_error(
            "MINT_PROJECT", f"remove unknown extension keys {extra}; use a local JSON path"
        )
    return _declared_relative(str(raw["path"]), suffix=".json")


def _extension_lock_entries(manifest: ProjectManifest) -> tuple[tuple[str, str, str], ...]:
    items: list[tuple[str, str, str]] = []
    for relative in manifest.extension_paths:
        text = _contained_file(manifest.directory, relative).read_text(encoding="utf-8")
        extension = extension_from_dict(json.loads(text))
        items.append((extension.namespace, extension.version, _digest_text(text)))
    return tuple(items)


def _assert_catalog_files(manifest: ProjectManifest) -> None:
    expected = closed_catalog_document()
    for relative in manifest.catalogs:
        text = _contained_file(manifest.directory, relative).read_text(encoding="utf-8")
        try:
            document = json.loads(text)
        except ValueError as exc:
            raise coded_error("MINT_CATALOG", f"fix {relative}: invalid catalog JSON") from exc
        if document != expected:
            raise coded_error(
                "MINT_CATALOG",
                f"{relative} does not match the closed v0 catalog; "
                "copy ids from the language catalog",
            )


def _declared_relative(raw: str, *, suffix: str) -> str:
    text = raw.strip().replace("\\", "/")
    if not text.endswith(suffix):
        raise coded_error(
            "MINT_PATH",
            f"set path {raw!r} to a project-relative {suffix} file",
        )
    candidate = Path(text)
    if candidate.is_absolute() or candidate.anchor:
        raise coded_error(
            "MINT_PATH",
            f"path {raw} must be project-relative; do not use absolute paths",
        )
    if ".." in candidate.parts or any(part == "." for part in candidate.parts):
        raise coded_error(
            "MINT_PATH",
            f"path {raw} must stay inside the project; do not use parent or . segments",
        )
    return candidate.as_posix()


def _contained_file(base: Path, relative: str) -> Path:
    declared = base / Path(relative)
    if declared.is_symlink():
        raise coded_error(
            "MINT_PATH",
            f"{relative} is a symlink; declare a real file inside the project",
        )
    path = declared.resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        raise coded_error(
            "MINT_PATH",
            f"{relative} escapes the project directory; use a path under the manifest",
        ) from None
    if not path.is_file():
        raise coded_error(
            "MINT_PROJECT",
            f"missing Mint input {relative}; add the declared file under the project",
        )
    return path


def _reject_duplicates(items: tuple[str, ...], kind: str) -> None:
    seen: set[str] = set()
    for item in items:
        if item in seen:
            raise coded_error(
                "MINT_PROJECT",
                f"list each {kind} once in {MANIFEST_NAME}; drop duplicate {item}",
            )
        seen.add(item)


def _default_name(directory: Path) -> str:
    raw = directory.name.strip().lower().replace("_", "-")
    cleaned = re.sub(r"[^a-z0-9-]+", "", raw)
    if _NAME.fullmatch(cleaned):
        return cleaned
    return "local-marker"


def _digest_text(source: str) -> str:
    return _digest_bytes(source.encode("utf-8"))


def _digest_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"))


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    tmp = path.with_name(f"{path.name}.tmp")
    try:
        tmp.write_bytes(payload)
        os.replace(tmp, path)
    except OSError:
        if tmp.exists():
            tmp.unlink()
        raise

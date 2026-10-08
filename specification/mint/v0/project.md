# Mint project model v0

A Mint project is a directory with `mint.toml` (manifest) and `mint.lock`
(canonical JSON lockfile). Compilation stays `compile_program`. The
project layer discovers declared local units, pins catalog and
extension digests, and refuses to compile when the lock is missing,
malformed, or stale.

This is not a package registry, git submodule, or SDK install path.

## mint.toml

```toml
schema = "mint.project/v0"
name = "minimal"
edition = "v0"
root = "main.mint"
units = ["main.mint"]
catalogs = ["catalogs/v0.json"]

[[extensions]]
path = "extensions/sample.json"

[profiles.local]
targets = ["fixture-alpha"]
```

| Field | Rule |
| --- | --- |
| `schema` | Exactly `mint.project/v0` |
| `name` | Lowercase DNS-label |
| `edition` | `v0` or compatibility `v1alpha1` |
| `root` | One of `units` |
| `units` | Project-relative `.mint` paths |
| `catalogs` | Optional snapshots that must match the closed v0 catalog |
| `extensions` | Optional local JSON files (`path` only) |
| `profiles` | Named lists of declared target ids; no credentials |
| `integrations` | Optional requirements: source, version, local, capabilities, targets, phases, realization |

Unknown keys are errors. Units are listed; Mint does not glob or search
parent trees for source files. Walking parents is used only to find
`mint.toml`. Absolute paths, `..`, `.` segments, and symlinks are
`MINT_PATH`.

## mint.lock

Canonical JSON (`sort_keys`, compact separators, trailing newline). No
absolute paths, timestamps, UUIDs, user names, or environment values.

Fields: `schema` (`mint.lock/v0`), `name`, `edition`, `root`,
`catalogDigest`, `irDigest`, `units` (`path` + `digest`), `extensions`
(`namespace` + `version` + `digest`).

When `[[integrations]]` is present, `mint.lock` also binds each
`identity` with `manifestDigest`, `artifactDigest`, `schemaDigests`,
capabilities, target kinds, and phases. `mint integrations add` writes
that pin. `mint integrations verify` recomputes it. Sources that look
like URLs, Git remotes, or PyPI names are refused.

`mint lock --check` fail-closed:

| Condition | Code |
| --- | --- |
| missing lock | `MINT_LOCK` |
| invalid / non-canonical JSON | `MINT_LOCK` (malformed) |
| source hashes drifted | `MINT_LOCK` (stale) |
| closed catalog digest drifted | `MINT_CATALOG` |
| extension file digest drifted | `MINT_EXTENSION` |

Writes use a sibling `.tmp` file and `os.replace`.

## CLI

Standalone: explicit `.mint` paths or `--graph`. Project: `--project`
and/or `mint project check`. Do not mix paths/`--graph` with
`--project`/`--profile`. `--locked` is valid only in project mode.

| Command | Behavior |
| --- | --- |
| `mint init [dir]` | Write `mint.toml`, `main.mint`, `[profiles.local]` |
| `mint lock` | Compile declared units and write `mint.lock` |
| `mint lock --check` | Exit 1 when missing, malformed, or stale |
| `mint check --project DIR [--profile NAME] [--locked]` | Locked `compile_program` |
| `mint compile --project DIR [--profile NAME] [--locked]` | Emit canonical MintIR |
| `mint project check --project DIR` | Same as locked project check |
| `specmint mint project check --project DIR` | Product CLI forwards to `mint` |
| `mint plan` | Route compiled `MintIR` through builtin adapters |
| `mint integrations search` | Filter local `mint.catalog-records/v0`; no network |
| `mint integrations inspect` | Print a packaged, catalog, or builtin identity |
| `mint integrations add --project DIR [IDENTITY] [--local PATH]` | Pin and bind lockfile digests; never pip or execute |
| `mint integrations remove --project DIR IDENTITY` | Unpin and refresh `mint.lock` |
| `mint integrations verify --project DIR` | Recompute pinned digests; do not execute |
| `mint integrations test` | Observe/plan/verify/evidence conformance kit |
| `mint adapters` | Deprecated alias of `mint integrations` |
| `mint lsp` | Stdio language server over `compile_program` |

`--profile` checks that listed target ids exist on the compiled IR. It
does not inject credentials or live state.

## Diagnostics

JSON on stderr, exit `1`. Families: `MINT_PROJECT`, `MINT_LOCK`,
`MINT_PATH`, `MINT_PROFILE`, `MINT_CATALOG`, `MINT_EXTENSION`,
`MINT_ADAPTER`, `MINT_ROUTE`, `MINT_PLAN`, `MINT_ACCOUNTING`,
`MINT_SNAPSHOT`, `MINT_IDENTITY`, plus existing compiler codes (`MINT_PARSE`, `MINT_STATIC`,
…).

## Examples

`examples/projects/{minimal,modules,repository-governance,repository-managed-file,repave-platform-repo,cross-platform,extensions}`
each ship `mint.toml`, `mint.lock`, source, catalog snapshot, expected
`MintIR`, and a README. The extensions example adds local extension JSON.

## Boundaries

Offline. No registries, clones, downloads, credentials, live-state,
apply, exec, or hidden environment inputs. LICENSE remains
`LicenseRef-Proprietary`. Not production-ready.

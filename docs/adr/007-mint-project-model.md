# ADR 007: Deterministic Mint project manifest and lockfile

**Status:** Accepted
**Date:** 2026-09-20

## Decision

Mint projects are local directories with a versioned `mint.toml`
manifest and a canonical `mint.lock` JSON lockfile. Compilation still
goes through `compile_program`. The project layer does not add a second
compiler, a registry, or network resolution.

`mint.toml` declares relative unit paths, optional catalog snapshots,
optional local extension JSON, and named profiles of declared target
ids. Profiles never carry credentials. `mint.lock` pins UTF-8 file
digests, the closed-catalog digest, extension file digests, and the
resulting `MintIR` digest.

`mint check` / `mint compile --project`, `mint project check`, and
`specmint mint project check` require a matching lock. Standalone
declared paths stay a separate CLI mode and cannot be combined with
`--project` or `--locked`.

Lock bytes contain no absolute paths, timestamps, UUIDs, or environment
values. Unit and catalog/extension files must stay inside the project
realpath; symlinks are rejected. Writes are atomic (`os.replace` of a
sibling `.tmp` file). Catalog or extension digest drift fail-closed.

## Consequences

- `mint init`, `mint lock [--check]`, and `mint project check` join the
  offline language CLI.
- The product CLI may forward `specmint mint …` to that language CLI.
- Explicit paths and `graph.json` remain valid declared inputs.
- Finding `mint.toml` may walk parent directories; unit loading never
  searches undeclared files.
- SpecMint CUE, apply, and publication stay out of this path.

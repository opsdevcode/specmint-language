# Build a Mint integration

Public preview. Not production-ready. Not 1.0.

This tutorial authors a local Mint integration, checks it, and pins it.
It does not apply anything. There is no `mint apply`. There is no live
GitHub or cloud mutation.

## Layout

```
mint-integration.json
implementation/reference_server.py
fixtures/{observe,plan,verify,evidence}.json
schemas/
tests/
README.md
```

Replacement markers for a new repository live in the
`mint-integration-template` tree. Instantiate them before conformance:

```
python scripts/instantiate.py --out /tmp/my-mint-integration
```

## Protocol

Speak `mint.protocol/v0` over stdio JSON-RPC. Implement `describe`,
`validate`, `observe`, `plan`, `verify`, and `evidence`. Refuse
`execute`. Planning support never grants execution authority. SpecMint
owns the governed lifecycle.

Public SDK entry points are in ADR 019: `load_manifest_file` and
versioned stdio JSON-RPC.

## Check and test

```
mint integrations check mint-integration.json
mint integrations test --local .
```

`mint integrations test` without `--local` still drives the packaged
`local.sandbox.ensure_marker` reference. `--local` never accepts a URL.

## Pin in a project

```
mint integrations search sandbox
mint integrations inspect local.sandbox.ensure_marker
mint integrations add --project . --local mint-integration.json
mint integrations verify --project .
```

`add` writes `[[integrations]]` and binds `manifestDigest` plus
`artifactDigest` in `mint.lock`. It does not pip, pipx, or execute the
integration. `remove` unpins.

## Catalog records

`mint.catalog-records/v0` is local data. Packaged records name
`local.sandbox.ensure_marker` 0.1.0 (in-tree) and `repo.github.plan`
0.1.0. `mint integrations add` still does not pip; pin a standalone
tree with `--local`.

Standalone public artifacts (GitHub prereleases, not PyPI, not
`latest`):

- `mint-integration-local` `v0.2.0-alpha.1`
  wheel `sha256:591e1b3ebdd7e4f9373996e0cdeafa62d8fea39d2640ded8270ff2e59c68094d`
- `mint-integration-github` `v0.2.0-alpha.1`
  wheel `sha256:3c864b4f5e7298a0a2f52d0680cb5c3eb8ea57a8195e7d9ba628fe3b7b6e60da`
- `mint-integration-template` `v0.2.0-alpha.1` (not a Python package)

## Will not appear here

- `mint apply`
- live GitHub, cloud, or Marketplace publication
- a hosted registry
- `latest` tags

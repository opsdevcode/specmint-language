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

`mint.catalog-records/v0` is local data. Packaged `local.sandbox.ensure_marker`
0.1.0 stays in-tree. Standalone integrations are GitHub-first: catalog
`origin` `github` binds the recorded GitHub Release wheel digest and the
tagged `mint-integration.json` digest. `mint integrations add` still does
not pip or download; pin a tree with `--local`, or pin `repo.github.plan`
from the catalog coordinates. There is no `latest` tag and no integration
PyPI.

Install a public wheel only from the GitHub prerelease, then check
`SHA256SUMS` against the catalog:

```
curl -fsSL -O https://github.com/opsdevcode/mint-integration-local/releases/download/v0.2.0-alpha.1/SHA256SUMS
curl -fsSL -O https://github.com/opsdevcode/mint-integration-local/releases/download/v0.2.0-alpha.1/mint_integration_local-0.2.0a1-py3-none-any.whl
shasum -a 256 -c SHA256SUMS
pip install ./mint_integration_local-0.2.0a1-py3-none-any.whl
```

Recorded coordinates:

- `mint-integration-local` `v0.2.0-alpha.1`
  wheel `sha256:591e1b3ebdd7e4f9373996e0cdeafa62d8fea39d2640ded8270ff2e59c68094d`
  manifest `sha256:cde4adf9e5f4c9e0b127cd11e6e977d25857d4a72602702ffe8a57223b05100e`
- `mint-integration-github` `v0.2.0-alpha.1`
  wheel `sha256:3c864b4f5e7298a0a2f52d0680cb5c3eb8ea57a8195e7d9ba628fe3b7b6e60da`
  manifest `sha256:1b805a915d950c614c99089942252abbe6d846658afa741b28824330feba41f9`
- `mint-integration-template` `v0.2.0-alpha.1` (not a Python package)

## Will not appear here

- `mint apply`
- live GitHub, cloud, or Marketplace publication
- a hosted registry
- `latest` tags

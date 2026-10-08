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

`mint.catalog-records/v0` is local data. Packaged records may name the
in-tree `local.sandbox.ensure_marker` reference. Records for standalone
public integration artifacts are added only after those artifacts exist.

## Will not appear here

- `mint apply`
- live GitHub, cloud, or Marketplace publication
- a hosted registry
- `latest` tags

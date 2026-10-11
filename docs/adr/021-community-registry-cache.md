# ADR 021: Static community registry cache

**Status:** Proposed
**Date:** 2026-10-11

## Decision

`opsdevcode/mint-registry` is a public Git repository of static
`mint.catalog-records/v0` JSON. It is not a hosted service, database, or
credential store.

`mint integrations update --registry PATH` copies a local checkout of
those records into `.mint/catalog-records.json`. `search`, `add`,
`verify`, and `lock` then overlay that cache on packaged records.

- `--registry` is a real local file or `records/v0.json` directory.
- Network-shaped paths stay `MINT_INTEGRATION`.
- `update` still does not pip, install, or execute an integration.
- GitHub Release `commit` is an optional recorded SHA on `release`.

A hosted registry remains deferred. Discovery never installs on search.

## Consequences

- Official `mint-integration-local` and `mint-integration-github`
  coordinates live in both the language package and mint-registry.
- Community records can be cached without changing the compiler.
- ADR 020 still owns the offline pin contract.

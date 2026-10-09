# ADR 020: Offline integration discovery and pinning

**Status:** Accepted
**Date:** 2026-10-08

## Decision

`mint integrations` discovers and pins integrations from local catalog
records (`mint.catalog-records/v0`) and project-relative manifests.

- `search` filters local records. It does not open a network path.
- `inspect` prints a packaged, catalog, or builtin identity.
- `add` writes `[[integrations]]` and binds `manifestDigest` plus
  `artifactDigest` in `mint.lock`. It does not pip, pipx, uv-install,
  clone, or execute the integration.
- `remove` unpins the project requirement and refreshes the lock.
- `verify` recomputes those digests and compares `mint.lock`. It does
  not execute.

Network-shaped sources (`http`, `https`, `git+`, `github.com`, PyPI)
are `MINT_INTEGRATION`. A hosted registry stays deferred. Catalog
records for third-party artifacts are added only after those public
artifacts exist.

Standalone public integrations are GitHub-first. Catalog `origin`
`github` stores the GitHub Release wheel digest and the tagged
`mint-integration.json` digest. `add` may pin those recorded
coordinates without downloading. PyPI is not the integration install
path. There is no `latest` alias.

## Consequences

- Language compile and plan stay offline.
- `mint integrations test` remains the conformance kit, not a side
  effect of `add`.
- Compatibility matrices live in `docs/compatibility.md`.

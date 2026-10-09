# Compatibility policy

Edition `v0` is public preview. Contracts may change before 1.0. This
repository will not claim production stability.

## Matrix

| Surface | Contract | Compatible with |
| --- | --- | --- |
| Language edition | `v0` | MintIR `v0`, `mint.project/v0`, `mint.lock/v0` |
| Language CLI | `specmint` on PyPI | GitHub Releases for VSIX; no `latest` |
| Integration protocol | `mint.protocol/v0` | one-shot stdio JSON-RPC; fail-closed `execute` |
| Process supervisor | pinned executable argv | idle after invoke; no daemon |
| Integration manifest | `mint.integration/v0` | ADR 019 SDK; `mint integrations check` |
| Catalog records | `mint.catalog-records/v0` | local data; packaged or github origin |
| Discovery CLI | `search inspect add remove verify status update test` | lockfile digest bind; no network |
| Local integration | GitHub Release `mint-integration-local` | recorded wheel and manifest digests |
| GitHub integration | GitHub Release `mint-integration-github` | plan-only `mint.repository-snapshot/v0` |
| Adapter alias | `mint.adapter/v0` | lossless plan-only mapping until 0.2.0 |

Pin a language release by Git tag (`v0.x.y-alpha.N`) and artifact
SHA-256. Pin an integration by `manifestDigest` and `artifactDigest` in
`mint.lock`. GitHub Releases are canonical for
`mint-integration-local` and `mint-integration-github`. There is no
`latest` tag, no hosted registry, and no integration PyPI claim.

## Kept in the current public preview

- Canonical MintIR for edition `v0`
- `mint.toml` / `mint.lock` project model
- `mint doctor`, `mint init --template`, and `--output-format json|human`
- Integration Protocol `mint.integration/v0` and `mint.protocol/v0`
- Public SDK entry points in ADR 019 (manifest-first and stdio JSON-RPC)
- Local catalog records (`mint.catalog-records/v0`)
- Offline discovery: `mint integrations search|inspect|add|remove|verify|status|update`
- One-shot process supervisor; `status` is idle with `running=false`
- Lockfile digest bind for pinned integrations (ADR 020)
- `mint integrations test` conformance kit
- `mint.adapter/v0` as a lossless alpha compatibility path
- `mint adapters` as a deprecated alias that emits `MINT_DEPRECATED_ADAPTER`

## Removal window

Adapter-alias removal is eligible at **0.2.0** and only for mappings that
stay lossless. Legacy contracts that are not plan-only with mutation
forbidden are already refused.

## Releases

Release Please owns prerelease tags on `main`. Do not run `git tag` or
`gh release create`. Do not hard-code the next version in docs or
install commands. GitHub Releases remain the VSIX source. Marketplace
and Open VSX publication stay deferred.

## Will not appear in this extract

- `mint apply`
- live provider SDKs
- a hosted integration registry
- integration packages on PyPI
- a Kubernetes snapshot integration
- hidden network on `search`, `add`, `verify`, `status`, or `update`
- `add` or `update` that pip-installs or executes an integration
- a persistent integration daemon
- CUE evaluation of caller-supplied programs
- production-ready or 1.0 claims
- VS Code Marketplace or Open VSX publish jobs
- imports of Repave, Overpass, Toll, Dispatch, or Relay

Pin a release by Git tag (`v0.x.y-alpha.N`) and artifact SHA-256 from
the GitHub prerelease. There is no `latest` tag. The VSIX is that
release asset, not a marketplace listing.

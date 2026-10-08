# Compatibility policy

Edition `v0` is public preview. Contracts may change before 1.0. This
repository will not claim production stability.

## Kept in the current public preview

- Canonical MintIR for edition `v0`
- `mint.toml` / `mint.lock` project model
- `mint doctor`, `mint init --template`, and `--output-format json|human`
- Integration Protocol `mint.integration/v0` and `mint.protocol/v0`
- Public SDK entry points in ADR 019 (manifest-first and stdio JSON-RPC)
- Local catalog records (`mint.catalog-records/v0`)
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
- CUE evaluation of caller-supplied programs
- production-ready or 1.0 claims
- VS Code Marketplace or Open VSX publish jobs

Pin a release by Git tag (`v0.x.y-alpha.N`) and artifact SHA-256 from
the GitHub prerelease. There is no `latest` tag. The VSIX is that
release asset, not a marketplace listing.

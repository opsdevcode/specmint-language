# Compatibility policy

Edition `v0` is public preview. Contracts may change before 1.0. This
repository will not claim production stability.

## Kept in the current alpha.2 preview

- Canonical MintIR for edition `v0`
- `mint.toml` / `mint.lock` project model
- Integration Protocol `mint.integration/v0` and `mint.protocol/v0`
- `mint.adapter/v0` as a lossless alpha compatibility path
- `mint adapters` as a deprecated alias that emits `MINT_DEPRECATED_ADAPTER`

## Removal window

Adapter-alias removal is eligible at **0.2.0** and only for mappings that
stay lossless. Legacy contracts that are not plan-only with mutation
forbidden are already refused.

## Will not appear in this extract

- `mint apply`
- live provider SDKs
- a hosted integration registry
- CUE evaluation of caller-supplied programs
- production-ready or 1.0 claims

Pin a release by Git tag (`v0.1.x-alpha.N`) and artifact SHA-256. There
is no `latest` tag.

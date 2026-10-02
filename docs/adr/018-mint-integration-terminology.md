# ADR 018: Mint integration terminology

**Status:** Accepted
**Date:** 2026-10-01

## Decision

Mint Integration is the canonical public extension term. The normative
words are intent, capability, target, integration, realization,
observation, plan, approval, executor, verification, evidence, and
outcome.

An integration is a public package that connects capabilities to an
external service or implementation. A realization is the resolved
binding of capability, target, and integration. It is a result, not a
downloadable package. SpecMint governs composite lifecycle coherence.
Integrations do not own capability semantics.

Mint is not a Terraform model. There is no resource as the central
abstraction, no provider CRUD lifecycle, no `apply`, and no state file.
Current condition is an observation. Durable history is lifecycle
records, verification, evidence, and outcomes.

`mint.adapter/v0` remains for one alpha compatibility window. `mint
adapters` is a deprecated alias that emits `MINT_DEPRECATED_ADAPTER`.
Removal is eligible at `0.2.0` and only for mappings that stay lossless.
Legacy contracts that are not plan-only with mutation forbidden are
refused.

## Consequences

- New public contracts use `mint.integration/v0` and `mint.protocol/v0`.
- MintIR is unchanged. Project and lock provenance carry integration pins.
- Hosted registry, signing, and OCI delivery are deferred and not claimed.

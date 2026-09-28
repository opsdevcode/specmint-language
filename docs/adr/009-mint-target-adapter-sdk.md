# ADR 009: Plan-only Mint target adapter SDK

**Status:** Accepted
**Date:** 2026-09-21

## Decision

Mint target adapters are a closed, in-process SDK that turns `MintIR`
into a deterministic `MintPlanResult` / `ArtifactSet`. Builtin adapters
are `local.sandbox.ensure_marker` and the plan-only `repo.github`
governance adapters. Planning is a pure function of compiled IR, the
closed catalog digest, the builtin registry, and caller-supplied
repository snapshots. Apply is not a CLI command. Live-state,
credentials, provider SDKs, network, and dynamic plugin loading are out
of scope.

Callers inspect manifests (`mint adapters list|inspect`) and emit
plans (`mint plan`, optional `--artifacts` for confined plan output,
optional `--snapshot` for `repo.github` targets). `mint repository
snapshot check` validates a supplied snapshot. Every required capability
must be accounted by a builtin adapter or planning fails closed.
Operation ids and artifact digests are SHA-256 of canonical content.

## Consequences

- Language compile still ends at `MintIR` via `compile_program`.
- Adapters live under `opsdevcode_specmint.mint.adapters` and stay
  free of CUE, HTTP, and host projection.
- Plan, target-plan, composite-plan, and artifact-set documents use
  distinct schema identities.
- Additional catalog verbs stay unroutable until an explicit builtin
  adapter is added in source.

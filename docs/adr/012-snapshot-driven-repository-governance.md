# ADR 012: Snapshot-driven plan-only repository governance

**Status:** Accepted
**Date:** 2026-09-24

## Decision

GitHub repository governance in SpecMint v0 is a **plan-only** compile
from Mint intent plus **caller-supplied** `mint.repository-snapshot/v0`
documents. SpecMint owns authoring, compile, target binding, desired-vs-actual
comparison, and deterministic plans. It does not authenticate, observe
live GitHub state, call the GitHub API, mutate repositories, retry, or
apply.

The language target kind remains `repo.github` with identity
`owner`/`name`. There is no `github.repository` kind and no URL or
credential identity. Catalog verbs for this adapter are
`repo.settings`, `repo.branch_protection`, `repo.security`, and
`repo.managed_file` (`v1alpha1`).

A plan is not live observation and is not a compliance proof unless the
caller accepts the snapshot's provenance. Incomplete, unknown,
unsupported, or redacted snapshot sections fail closed. Absent fields
are not treated as unknown.

Provider execution (auth, observe, mutate) is deferred to a future
non-Mint owner. `mint apply` remains absent.

## Consequences

- `mint plan --snapshot PATH` is explicit; live fetch is refused.
- `mint repository snapshot check` validates snapshot schema only.
- Operation ids stay SHA-256 of canonical operation bodies.
- LICENSE remains `LicenseRef-Proprietary`. Not production-ready.

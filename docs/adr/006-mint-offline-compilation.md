# ADR 006: Mint compilation is offline and deterministic

**Status:** Accepted
**Date:** 2026-09-20

## Decision

The Mint v0 reference pipeline (parse, module graph, import resolution,
symbol table, reference bind, static/type check, catalog, capabilities,
`MintIR`) is a pure function of declared unit text, logical unit ids,
the closed catalog, and declared extension identities. It does not:

- import or call provider SDKs
- open network connections
- read clocks or process environment as compile inputs
- invoke CUE or the SpecMint product compiler

Canonical `MintIR` bytes and `sha256:` digests are specified. Trivia and
clause order do not change the digest.

## Consequences

- Language modules under `opsdevcode_specmint.mint` except the host
  adapter stay free of `cue_engine`, `compiler`, HTTP, and SDKs.
- Host projection is a separate, deterministic dict mapping.
- Conformance programs pin expected IR and diagnostics.

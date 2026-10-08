# ADR 019: Mint Integration SDK entry points

**Status:** Accepted
**Date:** 2026-10-08

## Decision

The public integration SDK is `opsdevcode_specmint.integration`. Authors
enter through two fail-closed surfaces:

1. **Manifest-first.** `load_manifest_file` reads `mint.integration/v0`
   JSON. Identity, phases, execution support, and artifact digest are
   taken from the manifest. Unknown fields and secret-shaped keys are
   refused.
2. **Versioned stdio JSON.** `mint.protocol/v0` newline-delimited JSON-RPC
   2.0 on stdio. `handle_protocol_document` / `serve_stdio` decode one
   request and encode one response. Stdout is protocol. Stderr is
   diagnostics.

There is no plugin search path, no dynamic import of caller code, and no
HTTP listener. The host invokes an explicit argv. `executionSupport: fake`
never grants `execute` inside the integration process. Execute stays with
the SpecMint lifecycle.

`mint integrations test` runs the conformance kit: negotiate, describe,
observe, plan, verify, evidence, and fail-closed execute. Fixtures are
local JSON records. Catalog capability and target-kind records are local
data files, not a hosted registry.

## Consequences

- `mint.adapter/v0` remains the lossless alpha alias (ADR 018).
- Hosted registry, signing, and OCI delivery stay deferred.
- Language compile and plan stay offline.

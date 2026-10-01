# local.sandbox reference integration

Capability `local.sandbox.ensure_marker` v1alpha1. Targets `local.sandbox`
and `sandbox`. Phases `describe`, `validate`, `observe`, `plan`, `verify`,
and `evidence`. No network and no credentials.

Execution is a privileged phase. This integration declares
`executionSupport: fake` and refuses `execute`. SpecMint's local executor
performs the approved marker write inside an explicit sandbox.

Conformance: `mint integrations conformance local.sandbox.ensure_marker`.

Digests are SHA-256 of canonical JSON or of `reference_server.py` bytes.
Configuration is an empty object. Tokens are refused.

Packaging is the installed `mint-local-sandbox` console script. A hosted
registry is deferred. This integration is not a production service.

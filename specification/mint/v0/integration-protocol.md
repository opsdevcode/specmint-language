# Mint Integration Protocol v0

Normative companion to [ADR 018](../../../docs/adr/018-mint-integration-terminology.md).

## Separation

| Piece | Owns |
| --- | --- |
| Capability definition | The promise Mint and SpecMint understand |
| Integration implementation | How a capability is realized for a service |
| Realization | The binding capability + target + integration |
| Executor | The privileged runtime allowed to perform an approved operation |

Planning support never grants execution authority. `executionSupport`
values are `none`, `fake`, and `privileged`. `fake` records that a
governed fake executor may run. It does not enable execution inside the
integration process.

## Phases

Nonprivileged: `describe`, `validate`, `observe`, `plan`, `verify`,
`recover`, `evidence`. Privileged: `execute`.

A subset is valid. Observation-only, plan-only, verification-only, and
evidence-only integrations are valid. Unsupported phases fail closed.

## Transport

The contract is transport-neutral JSON. The reference transport is
newline-delimited JSON-RPC 2.0 on stdio. Stdout is protocol messages.
Stderr is diagnostics. Unknown fields, unknown protocol versions,
malformed JSON, oversized messages, and secret-shaped fields fail closed.

The host invokes an explicit argv with `shell` false and a minimal
environment. `HOME`, cloud profiles, and credential variables are not
passed. Requests, responses, and stderr are bounded. Timeouts terminate
the process.

## Digests

Canonical JSON is UTF-8, sorted keys, compact separators, and a trailing
newline. Content digests are `sha256:` of those bytes. Schema digests
hash the schema file bytes and are distinct from instance digests.

## Lock and project

`mint.toml` may declare `[[integrations]]` with `source`, `version`,
optional project-relative `local`, `capabilities`, `targets`, `phases`,
and optional `realization`. `mint.lock` pins identity, version, protocol,
manifest digest, artifact digest, schema digests, capability versions,
target kinds, and phases when integrations are declared. Locks without
integrations stay byte-compatible. Hosted registry resolution is deferred.

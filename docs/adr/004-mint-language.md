# ADR 004: Mint Language v1alpha1 frontend

**Status:** Superseded by [ADR 005](005-mint-is-the-language.md)
**Date:** 2026-09-20

## Decision

SpecMint accepts Mint Language `v1alpha1` as an authoring front-end for
automation only. A `.mint` program (or a Markdown `mint` fence) parses
with a token scanner and recursive-descent parser, binds a closed verb
catalog, and lowers to `AutomationSpecification`
`automations.opsdevcode.io/v1alpha1`. Existing CUE close and
`AutomationIntent` projection stay authoritative.

Mint does not add intent fields, policy-bundle evaluation, providers, or
platform mutation. DeliverySpecification remains YAML / JSON / `specmint`
Markdown.

Catalog `v1alpha1` contains `local.sandbox.ensure_marker` only.

## Update

Mint v0 treats that frontend as evidence. The language artifact is
`MintIR`. `v1alpha1` remains a source edition alias. See ADR 005 and
`specification/mint/v0/language.md`.

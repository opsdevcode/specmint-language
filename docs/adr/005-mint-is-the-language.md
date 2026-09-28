# ADR 005: Mint is the language; SpecMint is the host

**Status:** Accepted
**Date:** 2026-09-20

## Decision

Mint is specified as a language with its own edition, grammar, static
rules, closed catalog, and `MintIR` artifact. SpecMint is a product that
may load `.mint` source and project `MintIR` to
`AutomationSpecification`. Product documents are not the language.

PR 11 (`mint v1alpha1` frontend) stays as a compatibility edition and
host load path. It is not the definition of Mint.

Normative text: `specification/mint/v0/`.

## Consequences

- Language compile ends at `MintIR` + digest after module, reference,
  extension, and capability stages.
- SpecMint CUE / `AutomationIntent` stay host steps.
- New SpecMint product features are out of scope for language work.
- Markdown fences and HTTP media types remain host concerns.

# Language

Mint is the language. SpecMint is an optional product that can host Mint.
This page is the public overview. The normative edition is `v0`.

Mint compilation is offline and deterministic. The reference pipeline does
not open sockets, read environment secrets, call provider SDKs, or invoke
CUE. Equal programs produce equal canonical `MintIR` bytes.

## Start here

- [Normative language](../../specification/mint/v0/language.md)
- [Grammar](../../specification/mint/v0/grammar.ebnf)
- [MintIR](../../specification/mint/v0/ir.md)
- [Project and lock](../../specification/mint/v0/project.md)
- [Editor / LSP](../../specification/mint/v0/editor.md)
- [Why Mint is not Terraform](../why-not-terraform.md)
- [Standalone boundary](../standalone.md)

## Commands

`check` `compile` `convert` `doctor` `fmt` `inspect` `init` `lock` `lsp`
`plan` `project` `integrations` `adapters` `repository` `version`

`compile` emits canonical MintIR. `plan` is snapshot-driven and offline.
`mint apply` is not implemented. `mint adapters` is a deprecated alias of
`mint integrations`.

There is no second TypeScript compiler in this extract.

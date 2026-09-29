# Mint language

Mint is an offline, deterministic language for governed automation intent.
This repository is the public language extract: grammar, `MintIR`, reference
compiler, CLI (`mint`), conformance suite, and VS Code extension.

**SpecMint core** is public at
[`opsdevcode/specmint-platform`](https://github.com/opsdevcode/specmint-platform).
This repository is the Mint language extract only. The hosted SpecMint
service stays private. `opsdevcode/specmint` remains internal. There is no
`mint apply` command. There are no live providers or credentials here.

## Install

```bash
pip install specmint
mint version
```

The distribution name is `specmint`. The language executable is `mint`.
A thin `specmint mint …` alias forwards to the same language CLI.

Alpha version: **0.1.0a1** (Git tag `v0.1.0-alpha.1`).

## Language commands

`check` `compile` `convert` `fmt` `inspect` `init` `lock` `lsp` `plan`
`project` `adapters` `repository` `version`

`compile` emits canonical MintIR. `plan` is snapshot-driven and offline.
`mint apply` is not implemented.

## Documentation

- [Language](specification/mint/v0/language.md)
- [MintIR](specification/mint/v0/ir.md)
- [Grammar](specification/mint/v0/grammar.ebnf)
- [Project model](specification/mint/v0/project.md)
- [Editor / LSP](specification/mint/v0/editor.md)
- [Conversion](specification/mint/v0/conversion.md)
- [Adapters](specification/mint/v0/adapters.md)
- [Repository snapshots](specification/mint/v0/repository-snapshot.md)
- [Conformance](specification/mint/v0/conformance/README.md)
- GitHub Pages: https://opsdevcode.github.io/specmint-language/

## VS Code

Publisher id: `opsdevcode.mint-language`. Package a VSIX from `editors/vscode`.
Marketplace publish requires the OpsDevCode publisher; GitHub Releases always
attach the VSIX.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

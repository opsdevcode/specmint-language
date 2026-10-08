# Mint language

Mint is the governed automation language for expressing what an
engineering system should accomplish. SpecMint turns that intent into an
approved, observable, verifiable lifecycle. Integrations connect Mint
capabilities to repositories, clouds, Kubernetes, SaaS platforms, and
internal systems without moving execution authority into the language.

This repository is the public language extract: grammar, `MintIR`,
reference compiler, CLI (`mint`), Integration Protocol v0, conformance
suite, and VS Code extension.

**Public preview / alpha.2 — not production-ready, not 1.0.**

[SpecMint Platform](https://github.com/opsdevcode/specmint-platform) is the
governed runtime. The hosted SpecMint service stays private.
`opsdevcode/specmint` remains internal. There is no `mint apply` command.
There are no live providers or credentials here.

Product page: [opsdevco.de/products/mint](https://opsdevco.de/products/mint)
Docs: [Mint language documentation](https://opsdevcode.github.io/specmint-language/)

## Install

```bash
pipx install specmint
mint version
```

```bash
uv tool install specmint
mint version
```

The distribution name is `specmint`. The language executable is `mint`.
A thin `specmint mint …` alias forwards to the same language CLI.

Pin a GitHub Release tag and artifact SHA-256 when you need a specific
build. There is no `latest` tag.

## Five-minute quickstart

See [docs/quickstart.md](docs/quickstart.md). Copy
`examples/projects/local-marker`, then `check`, `fmt --check`, `lock`,
`compile`, `inspect`, `plan`, and `mint integrations conformance`. SpecMint
begins after that plan: approval, fake/local execution, verification, and
evidence. No credentials. No live mutation.

## Headline: Integration Protocol v0

Mint capabilities remain the promise. Integrations realize capabilities
for targets. A realization is a resolved binding, not a downloadable
package. Planning never grants execution authority.

- [Integration Protocol](specification/mint/v0/integration-protocol.md)
- [Authoring an integration](specification/mint/v0/integration-authoring.md)
- [Trust and permissions](specification/mint/v0/integration-trust.md)
- [ADR 018](docs/adr/018-mint-integration-terminology.md)
- [ADR 019](docs/adr/019-mint-integration-sdk.md)

`mint adapters` is a deprecated alpha alias of `mint integrations`.

## Language commands

`check` `compile` `convert` `doctor` `fmt` `inspect` `init` `lock` `lsp`
`plan` `project` `integrations` `adapters` `repository` `version`

`compile` emits canonical MintIR. `plan` is snapshot-driven and offline.
`mint apply` is not implemented.

## Documentation

- [Language overview](specification/mint/v0/language.md)
- [Why Mint is not Terraform](docs/why-not-terraform.md)
- [Project and lock model](specification/mint/v0/project.md)
- [MintIR](specification/mint/v0/ir.md)
- [Editor / LSP](specification/mint/v0/editor.md)
- [Compatibility policy](docs/compatibility.md)
- [Public roadmap boundaries](docs/roadmap.md)
- [Conformance](specification/mint/v0/conformance/README.md)
- [Security reporting](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Docs index](docs/index.md)

## Editor (VS Code / Cursor)

Publisher id: `opsdevcode.mint-language`. Install the VSIX from the newest
GitHub prerelease. There is no `latest` tag.

[GitHub Releases](https://github.com/opsdevcode/specmint-language/releases)

1. Download `mint-language-*.vsix` and `SHA256SUMS` from that prerelease.
2. Verify the VSIX against `SHA256SUMS` (`sha256sum -c SHA256SUMS`).
3. VS Code: Command Palette → Extensions: Install from VSIX…, or
   `code --install-extension mint-language-*.vsix`
4. Cursor: Command Palette → Extensions: Install from VSIX…, or
   `cursor --install-extension mint-language-*.vsix`

VS Code Marketplace and Open VSX publication is deferred. GitHub Releases
are the canonical VSIX source. The language CLI stays offline; there is
no `mint editor install` and no `mint apply`.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

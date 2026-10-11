# Mint language documentation

Public extract of the Mint language: specification, MintIR, reference
compiler, `mint` CLI, editor, and Integration Protocol v0.

**Public preview / alpha. Not production-ready. Not 1.0.** Canonical
site: <https://mint.opsdevco.de/>. Generated fallback until that host
answers HTTP 200:
<https://opsdevcode.github.io/specmint-language/>.

Mint is a standalone spec language. It does not require SpecMint,
Repave, Overpass, Toll, Dispatch, Relay, or hosted services.

- [Ten-minute quickstart](quickstart.md)
- [Language](site/language.md)
- [Integrations](site/integrations.md)
- [Build a Mint integration (tutorial)](build-an-integration.md)
- [Downloads](site/downloads.md)
- [Community](community.md)
- [Playground](site/playground.md)
- [Optional platform](site/platform.md)
- [GitHub Releases (CLI artifacts and VSIX)](https://github.com/opsdevcode/specmint-language/releases)
- [Normative language](../specification/mint/v0/language.md)
- [Why Mint is not Terraform](why-not-terraform.md)
- [MintIR](../specification/mint/v0/ir.md)
- [Grammar](../specification/mint/v0/grammar.ebnf)
- [Project and lock](../specification/mint/v0/project.md)
- [Editor](../specification/mint/v0/editor.md)
- [Conversion](../specification/mint/v0/conversion.md)
- [Integration Protocol v0](../specification/mint/v0/integration-protocol.md)
- [Building an integration](../specification/mint/v0/integration-authoring.md)
- [Integration trust](../specification/mint/v0/integration-trust.md)
- [Adapters (deprecated alias)](../specification/mint/v0/adapters.md)
- [Repository snapshots](../specification/mint/v0/repository-snapshot.md)
- [Conformance](../specification/mint/v0/conformance/README.md)
- [Compatibility](compatibility.md)
- [Standalone architecture](standalone.md)
- [Roadmap boundaries](roadmap.md)
- [Security](../SECURITY.md)
- [Contributing](../CONTRIBUTING.md)
- [ADR 018: integration terminology](adr/018-mint-integration-terminology.md)
- [ADR 019: integration SDK](adr/019-mint-integration-sdk.md)
- [ADR 020: integration discovery](adr/020-integration-discovery.md)
- [ADR 021: community registry cache](adr/021-community-registry-cache.md)
- [Language source](https://github.com/opsdevcode/specmint-language)
- [SpecMint Platform](https://github.com/opsdevcode/specmint-platform)
- [Product page](https://opsdevco.de/products/mint)

Install the CLI with `pipx install specmint` or `uv tool install specmint`.
Install the editor from the VSIX on GitHub Releases. VS Code Marketplace
and Open VSX publication is deferred. `mint apply` is not part of this
extract. SpecMint is optional. The hosted service stays private.

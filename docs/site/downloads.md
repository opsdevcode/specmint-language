# Downloads

Install the language CLI from PyPI (a mirror of GitHub Release bytes) or pin
a GitHub Release artifact by tag and SHA-256. There is no `latest` tag.

```bash
pipx install specmint
# or: uv tool install specmint
mint version
```

The distribution name is `specmint`. The language executable is `mint`.

[GitHub Releases](https://github.com/opsdevcode/specmint-language/releases)
attach the wheel, sdist, VSIX, `SHA256SUMS`, and SBOM.

## Editor

Publisher id: `opsdevcode.mint-language`. Download `mint-language-*.vsix`
and `SHA256SUMS` from the newest GitHub prerelease. Verify the checksum,
then Command Palette → Extensions: Install from VSIX…. VS Code Marketplace
and Open VSX publication is deferred.

## Integrations

`mint-integration-local` and `mint-integration-github` are GitHub Release
assets, not PyPI packages. See [integrations](integrations.md).

## Release policy

See [releases](../releases.md). Humans do not push release tags. Mint remains
an alpha preview: not production-ready, not 1.0.

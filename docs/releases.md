# Mint releases

Mint releases are derived from Conventional Commits and Semantic Versioning.
Humans and local scripts do not calculate or push release tags.

Org policy (`opsdevcode.release/v0`): GitHub Releases are canonical. PyPI is a mirror of those artifact bytes. Marketplace and Open VSX stay deferred. See https://github.com/opsdevcode/.github/blob/main/docs/github-releases.md.

1. Normal product PR titles and commits use Conventional Commits.
2. Release Please maintains an alpha release PR containing the generated
   version, changelog, Python package version, VS Code extension version, and
   release manifest update.
3. Merging that green release PR is the release approval. Release Please
   creates `vMAJOR.MINOR.PATCH-alpha.N` and a GitHub prerelease.
4. The release event builds and tests the wheel, sdist, and VSIX once; attaches
   those artifacts plus checksums, SBOM, and attestations to the GitHub
   prerelease; and publishes the same Python artifact bytes to PyPI through
   trusted publishing (OIDC). The VSIX stays on the GitHub Release. VS Code
   Marketplace and Open VSX publication is deferred and is not part of this
   workflow. Missing `VSCE_PAT` / `OVSX_PAT` cannot fail a release.

During the alpha channel, the prerelease strategy advances
`0.1.0-alpha.N`. Release notes retain the `fix:`, `feat:`, and breaking-change
categories. Moving to a stable channel requires a separate reviewed change.

The Release Train uses a one-hour GitHub App token scoped to only
`opsdevcode/specmint-language`, with only contents, metadata, and pull request permissions. No PAT or PyPI token is used. The existing PyPI trusted
publisher remains bound to `.github/workflows/release.yml`.

Mint remains an alpha preview: no `latest`, no stable/1.0 claim, and no
`mint apply` command.


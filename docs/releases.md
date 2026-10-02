# Mint releases

Mint releases are derived from Conventional Commits and Semantic Versioning.
Humans and local scripts do not calculate or push release tags.

1. Normal product PR titles and commits use Conventional Commits.
2. Release Please maintains an alpha release PR containing the generated
   version, changelog, Python package version, VS Code extension version, and
   release manifest update.
3. Merging that green release PR is the release approval. Release Please
   creates `vMAJOR.MINOR.PATCH-alpha.N` and a GitHub prerelease.
4. The release event builds and tests the wheel, sdist, and VSIX once; attaches
   checksums, SBOM, and attestations; and publishes those same Python artifact
   bytes to PyPI through trusted publishing.

During the alpha channel, the prerelease strategy advances
`0.1.0-alpha.N`. Release notes retain the `fix:`, `feat:`, and breaking-change
categories. Moving to a stable channel requires a separate reviewed change.

The Release Train uses a one-hour GitHub App token scoped to only
`opsdevcode/specmint-language`, with only contents, issues, metadata, and pull
request permissions. No PAT or PyPI token is used. The existing PyPI trusted
publisher remains bound to `.github/workflows/release.yml`.

Mint remains an alpha preview: no `latest`, no stable/1.0 claim, and no
`mint apply` command.


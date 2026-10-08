# Community governance

Mint integrations are authored in public. This extract does not host a
registry and does not admit Marketplace or Open VSX listings.

## What a contribution is

- A `mint.integration/v0` manifest and a stdio `mint.protocol/v0` server
- Observe / plan / verify / evidence fixtures
- Fail-closed `execute`
- Apache-2.0, no private runtime source, no credentials

## What a contribution is not

- `mint apply`
- A live GitHub, cloud, or SaaS mutation from the language CLI
- A pip install performed by `mint integrations add`
- A catalog record for an artifact that does not yet exist

## Review

Open a pull request against the language extract or a dedicated
integration repository. Required checks stay
`semantic-pull-request` and `commitlint` plus the repository test job.
Squash-merge when those checks are green. Release Please owns tags.

## Trust

See [integration trust](../specification/mint/v0/integration-trust.md).
Official, verified, and community trust levels are future labels, not
implemented services. v0 trusts an explicit local executable whose
artifact digest matches the lock or manifest.

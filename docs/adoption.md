# Fifteen-minute Mint adoption

Public preview. Offline language loop. No `mint apply`. No live mutation.
Pin GitHub Release tags and SHA-256; there is no `latest`.

## Coordinates (Wave 2)

| Surface | Tag | Package |
| --- | --- | --- |
| Language | `v0.7.0-alpha.2` | `specmint==0.7.0a2` |
| GitHub integration | `v0.3.0-alpha.1` | GitHub Release wheel only |
| Local integration | `v0.2.1-alpha.1` | GitHub Release wheel only |

PyPI mirrors the language wheel. Integration wheels are not on PyPI.

## Path A — first-party action (existing repo)

1. Add `.github/workflows/mint.yml` that calls
   `opsdevcode/mint-action` on `pull_request` (not `pull_request_target`).
2. Default `permissions: contents: read`.
3. The action downloads the language GitHub Release wheel and
   `SHA256SUMS`, verifies the digest, then runs `mint check`.
4. After this repository ships `--sarif-output`, upload that file with
   `github/codeql-action/upload-sarif` using `security-events: write` on
   that job only.

See `opsdevcode/mint-action` and `opsdevcode/mint-starter`.

## Path B — starter template

Use [opsdevcode/mint-starter](https://github.com/opsdevcode/mint-starter)
as a GitHub template. It includes a local-marker project, the action
workflow, and a governance snapshot example. The starter may stay
untagged.

## Path C — local CLI

```bash
pipx install specmint==0.7.0a2
mint version
mint init mint-quickstart --name mint-quickstart --template local-marker
cd mint-quickstart
mint doctor --project .
mint check --project . --sarif-output mint.sarif
mint plan --project . --locked
```

`--sarif-output` is in this repository after the SARIF change merges.
Until a following language release, installed `0.7.0a2` still speaks
JSON diagnostics on stderr.

## Governance pull request

Plan repository settings from a supplied snapshot. Do not call GitHub.

```bash
mint plan --project examples/projects/repository-governance --locked \
  --snapshot examples/projects/repository-governance/snapshots/specmint.json
```

Open the plan as a PR. Merge is an owner decision. Execute stays refused.

## Compatibility CI

`.github/workflows/compatibility.yml` downloads the pinned Wave 2
Release wheels, checks `SHA256SUMS`, and runs `mint check` on
`examples/projects/local-marker`. Catalog records may still list an
older github-origin pin until a separate catalog bump.

## Out of scope

- `mint apply`, live providers, Marketplace, GHCR visibility
- integration PyPI, CLI telemetry, hosted SpecMint
- Convergence

# Security

Report vulnerabilities privately via GitHub Security Advisories on
[opsdevcode/specmint-language](https://github.com/opsdevcode/specmint-language).

This extract is offline and fail-closed. Do not send live credentials,
provider tokens, or customer data in issues.

## Public-preview expectations

- No `mint apply` command.
- Integrations may plan; planning never grants execution authority.
- The reference `local.sandbox` integration declares `executionSupport: fake`
  and refuses `execute`.
- Release artifacts (wheel, sdist, VSIX) are built once, checksummed, and
  attached to a GitHub prerelease. Verify `SHA256SUMS` before installing a
  VSIX. Do not trust a `latest` tag; none is published.
- PyPI publishing uses trusted publishing / OIDC only. There is no
  long-lived PyPI token in this repository.

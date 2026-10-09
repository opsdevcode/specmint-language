# Ten-minute Mint quickstart

Public preview. Offline. No credentials. No live mutation. `mint apply`
does not exist.

Install once (Python 3.12):

```bash
pipx install specmint
# or: uv tool install specmint
mint version
```

`mint version` prints the installed language version. Do not pin a
superseded release in this install path.

Editor (optional): download `mint-language-*.vsix` and `SHA256SUMS` from
the newest [GitHub prerelease](https://github.com/opsdevcode/specmint-language/releases)
(not a `latest` tag). Verify the checksum, then Command Palette →
Extensions: Install from VSIX…, or `code --install-extension` /
`cursor --install-extension`. Marketplace and Open VSX are deferred.

Initialize a local-marker project, then run the language loop:

```bash
mint init mint-quickstart --name mint-quickstart --template local-marker
cd mint-quickstart
mint doctor --project .
mint check --project .
mint fmt --check main.mint
mint lock --project .
mint lock --check --project .
mint compile --project . --locked > mint-ir.json
mint inspect mint-ir.json
mint plan --project . --locked
mint integrations test local.sandbox.ensure_marker
```

What each step does:

| Command | Result |
| --- | --- |
| `init` | Write `mint.toml` and `main.mint` from the local-marker template |
| `doctor` | Offline first-run checks; `mint apply` stays unknown |
| `check` | Type-check and catalog-check the declared unit |
| `fmt --check` | Confirm formatting is already canonical |
| `lock` | Write `mint.lock` |
| `lock --check` | Confirm `mint.lock` matches `mint.toml` |
| `compile` | Emit canonical MintIR |
| `inspect` | Recheck the MintIR digest |
| `plan` | Produce a closed plan through the local/fake integration |
| `integrations test` | Observe, plan, verify, evidence; execute fails closed |

Planning does not write a sandbox marker. The integration declares
`executionSupport: fake` and refuses `execute`. The conformance kit covers
observation, plan, verification, and evidence. Catalog records are local
JSON data. There is no hosted registry. Standalone integration wheels
are GitHub Release assets, not PyPI packages.

Discover and pin without network:

```bash
mint integrations search sandbox
mint integrations inspect local.sandbox.ensure_marker
```

`add`, `remove`, `verify`, `status`, and `update` bind or refresh
`mint.lock` digests. They do not pip-install, execute, or leave a
daemon running.

`--output-format json|human|sarif` selects diagnostic and first-run output.
Use `mint check --sarif-output mint.sarif` for GitHub Code Scanning. `init`
and `doctor` stay `json` or `human`. See [adoption.md](adoption.md).
The default is `json`. It is not inferred from the TTY.

## Where SpecMint begins

Mint stops at intent, compilation, realization, and plan. SpecMint
Platform owns approval, fake/local execution, verification, and
evidence. Continue with the
[platform quickstart](https://github.com/opsdevcode/specmint-platform/blob/main/docs/quickstart.md)
from a separate environment. Do not install the platform package over
this language CLI: both expose a `mint` script.

## Does not run

- `mint apply` (unknown command)
- live AWS, Azure, GCP, Kubernetes, GitHub, or SaaS mutation
- a hosted integration registry

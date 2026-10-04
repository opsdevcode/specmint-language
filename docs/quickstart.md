# Five-minute Mint quickstart

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

Copy the checked-in local marker example, then run the language loop:

```bash
cp -R examples/projects/local-marker /tmp/mint-quickstart
cd /tmp/mint-quickstart

mint check --project . --locked
mint fmt --check main.mint
mint lock --check --project .
mint compile --project . --locked > mint-ir.json
mint inspect mint-ir.json
mint plan --project . --locked
mint integrations conformance local.sandbox.ensure_marker
```

What each step does:

| Command | Result |
| --- | --- |
| `check` | Type-check and catalog-check the declared unit |
| `fmt --check` | Confirm formatting is already canonical |
| `lock --check` | Confirm `mint.lock` matches `mint.toml` |
| `compile` | Emit canonical MintIR |
| `inspect` | Recheck the MintIR digest |
| `plan` | Produce a closed plan through the local/fake integration |
| `integrations conformance` | Run the reference `local.sandbox` harness |

Planning does not write a sandbox marker. The integration declares
`executionSupport: fake` and refuses `execute`.

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

# Contributing

Mint is the public language extract. Conventional commits. Python 3.12.

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
make format && make quality && make test
```

## Rules

- Compile stays deterministic and offline.
- Do not add `mint apply`, provider SDKs, or live network calls to
  language-core modules.
- `mint.adapters` is a deprecated alpha alias of `mint integrations`. Keep
  that compatibility window until `0.2.0` (ADR 018).
- Hosted integration registry, signing, and OCI delivery are out of scope.
- Do not claim production readiness or 1.0.

## Documentation

Public docs live under `docs/` and `specification/mint/v0/`. Start with
[the five-minute quickstart](docs/quickstart.md).

## Security

Report vulnerabilities through GitHub Security Advisories. See [SECURITY.md](SECURITY.md).

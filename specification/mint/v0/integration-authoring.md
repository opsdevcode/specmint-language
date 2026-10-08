# Authoring a Mint integration

Reference layout:

```
examples/integrations/local-sandbox/
  mint-integration.json
  schemas/
  implementation/
  fixtures/
  tests/
  README.md
```

`local.sandbox.ensure_marker` `0.1.0` realizes
`local.sandbox.ensure_marker` `v1alpha1` for target kinds `local.sandbox`
and `sandbox`. Supported phases are `describe`, `validate`, `observe`,
`plan`, `verify`, and `evidence`. `execute` is refused. Execution stays
in the SpecMint fake/local executor so the language package does not
mutate the host.

## Conformance

```
mint integrations test local.sandbox.ensure_marker
```

`mint integrations conformance` is an alias. The kit negotiates
`mint.protocol/v0`, checks `describe`, drives `observe`, `plan`,
`verify`, and `evidence` from local fixtures, and requires `execute` to
fail closed. Execution stays in the SpecMint lifecycle.

Discovery stays offline:

```
mint integrations search local.sandbox
mint integrations inspect local.sandbox.ensure_marker
mint integrations add --project . local.sandbox.ensure_marker
mint integrations verify --project .
mint integrations remove --project . local.sandbox.ensure_marker
```

`add` binds `manifestDigest` and `artifactDigest` in `mint.lock`. It
does not pip-install or execute the integration. Pass `--local` only for
a project-relative `mint.integration/v0` file. See
[ADR 020](../../../docs/adr/020-integration-discovery.md).

Public SDK entry points are documented in
[ADR 019](../../../docs/adr/019-mint-integration-sdk.md):
`load_manifest_file` and versioned stdio JSON-RPC.

## Digests

Manifest and protocol documents use canonical JSON. The artifact digest
is SHA-256 of the reference server file bytes. Configuration schemas, when
present, are pinned separately. Credentials are not configuration.

## Packaging

Install the language package and run `mint-local-sandbox` or
`python -m opsdevcode_specmint.integration`. A hosted registry, signed
OCI artifacts, and marketplace admission are deferred. `mint integrations
init` is deferred until a generator can emit a valid manifest without
duplicating the reference server.

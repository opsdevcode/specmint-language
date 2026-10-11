# Integrations

Mint capabilities are the promise. Integrations realize those capabilities
for a target. A realization is a resolved binding, not a downloadable
package and not a live provider session.

Planning never grants execution authority. `execute` is refused in this
extract. There is no `mint apply`. Standalone integration wheels are GitHub
Release assets, not PyPI packages. There is no hosted registry service and
no live AWS, Azure, GCP, Kubernetes, GitHub, or SaaS mutation from `mint`.

## Protocol

- [Integration Protocol v0](../../specification/mint/v0/integration-protocol.md)
- [Trust and permissions](../../specification/mint/v0/integration-trust.md)
- [Authoring (normative)](../../specification/mint/v0/integration-authoring.md)
- [Build an integration (tutorial)](../build-an-integration.md)
- [Community registry cache](../community.md)

## Plan-first loop

```bash
mint integrations search sandbox
mint integrations inspect local.sandbox.ensure_marker
mint integrations test local.sandbox.ensure_marker
```

Cache static records from a local checkout of `opsdevcode/mint-registry`
with `mint integrations update --registry PATH`. Search does not install.
`add` pins digests in `mint.lock`; it does not pip-install or execute.

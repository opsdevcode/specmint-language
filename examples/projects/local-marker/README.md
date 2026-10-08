# local-marker

Single-unit `local.sandbox.ensure_marker` project used by the plan-only
reference integration.

```bash
mint plan --project examples/projects/local-marker --locked
mint integrations inspect local.sandbox.ensure_marker
mint integrations test local.sandbox.ensure_marker
```

`plan.json` is the expected `MintPlanResult`. Planning does not write a
sandbox marker on the target filesystem. `mint plan --artifacts DIR`
writes confined plan output only. Execute fails closed.

Offline local files only. Not a registry package.

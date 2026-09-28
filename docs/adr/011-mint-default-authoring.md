# ADR 011: Mint is the default specification authoring format

**Status:** Accepted
**Date:** 2026-09-21
**Updated:** 2026-09-24

## Decision

Mint is the default **human** authoring format for new SpecMint
specifications. JSON and YAML remain supported **legacy** authoring
inputs when the caller selects them explicitly (file suffix, `--format`,
`--from`, or `Content-Type`). They are not removed in this milestone.

Machine contracts stay JSON: `CompiledIntent`, `AutomationIntent`,
`MintIR`, plans, lockfiles, local approvals, evidence bundles, HTTP
problem payloads, API responses, and `mint.migration-report/v0`.

`mint convert` is the conversion path. It is not a second compiler.
See [specification/mint/v0/conversion.md](../../specification/mint/v0/conversion.md).

### Inventory (this tree)

| Surface | Human spec input | Machine JSON retained |
| --- | --- | --- |
| `specmint validate\|compile` | `.mint` default; `.json`/`.yaml`/`.md` explicit | compiled artifacts |
| `specmint inspect` | compiled artifact `.json` | identity.revision |
| HTTP `/validate` `/compile` | `text/x-mint` default when Content-Type omitted; json/yaml/markdown explicit | compile JSON body |
| HTTP `/inspect` | `application/json` compiled artifact | yes |
| `mint` language CLI | `.mint`, `mint.toml`; `mint convert` for legacy authoring | `mint.lock`, MintIR, plans, migration reports |
| Examples | `examples/projects/**/*.mint` plus `examples/legacy-authoring` | catalogs, expected IR, plan.json |
| Tests | Mint fixtures plus retained JSON/YAML/Markdown | envelopes, intents |
| Local execute | compiled AutomationIntent JSON | approval.json, evidence |

No remaining caller required JSON/YAML as the *only* authoring path.

### External compatibility

External callers that still send explicit JSON/YAML/Markdown authoring
keep working on `specmint validate|compile` and HTTP. Conversion is
opt-in via `mint convert`. DeliverySpecification has no Mint v0
classic encoding and is refused by convert.

### Coverage

Convert covers representable `AutomationSpecification` objects and the
established Markdown form. Multi-unit Mint, extensions, profiles, and
DeliverySpecification are out of scope. Telemetry is not collected;
reports contain logical paths, statuses, digests, and diagnostic codes
only.

### Unsupported / unrepresentable

Unknown formats, sniffed stdin, extra fields, credentials/URLs,
MintIR-as-source, symlink/unsafe paths, ambiguous Markdown, semantic
mismatch.

### Deprecation stages (no calendar)

1. **Default Mint** (this ADR, shipped): explicit legacy still compiles.
2. **Convert available** (this change): first-party authoring prefers Mint.
3. **Warn on legacy authoring** only after convert coverage is complete
   for remaining first-party authoring files and equivalence tests stay
   green.
4. **Remove JSON/YAML/Markdown authoring** only after an evidence window
   with no first-party authoring remaining, convert reports clean, and
   a dedicated decision. Machine JSON is never removed on that path.

There is no removal version or deadline in this ADR.

## Selection

- Path suffix selects format. Unknown suffix fails and names `--format`
  or `--from`.
- Stdin without `--format`/`--from` is Mint for compile/validate.
  `mint convert` stdin requires `--from` and does not sniff.
- HTTP without Content-Type is Mint. JSON, YAML, and Markdown
  bodies are refused (not reinterpreted). `text/plain` and
  `application/octet-stream` are ambiguous and refused.
- Envelopes must set `format` to `mint`, `json`, or `yaml`.

## Consequences

- SpecMint still compiles through the framework-free compiler core.
- MintIR → `mint plan` → `specmint execute` remains the local path.
- There is no `mint apply`.

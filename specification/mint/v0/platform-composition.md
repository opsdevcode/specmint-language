# Mint and SpecMint composition

Mint compiles governed intent (`MintIR`) offline. SpecMint federates
product `opsdevcode.capability-manifest/v1alpha1` documents and runs
composite plan, approval, execution, verification, and evidence against
fake-local providers.

This language repository does not import Overpass, Toll, Dispatch, Repave,
or Relay. It does not call live providers. There is no `mint apply`.

See [`opsdevcode/specmint-platform`](https://github.com/opsdevcode/specmint-platform)
ADR 016.

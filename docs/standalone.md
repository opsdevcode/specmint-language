# Standalone Mint

Mint language is independently usable. This repository does not import
Repave, Overpass, Toll, Dispatch, or Relay. It does not call hosted
control planes. There is no `mint apply`.

SpecMint Platform is a separate runtime. Install it in a separate
environment. Both packages currently expose a `mint` script; do not
install them over each other.

Standalone integration packages
(`mint-integration-local`, `mint-integration-github`) publish GitHub
Release assets. They are not PyPI packages. There is no Kubernetes
snapshot integration in this preview.

See `tests/test_independence.py`.

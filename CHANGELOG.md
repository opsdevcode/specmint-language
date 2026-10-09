# Changelog

## [0.7.0-alpha.2](https://github.com/opsdevcode/specmint-language/compare/v0.6.0-alpha.2...v0.7.0-alpha.2) (2026-10-09)


### Features

* **mint:** add process supervisor status and lock update ([#30](https://github.com/opsdevcode/specmint-language/issues/30)) ([a1adfce](https://github.com/opsdevcode/specmint-language/commit/a1adfcec300850d74c992e2ae94cfbb77944dba9))


### Documentation

* publish wave 2 compatibility matrix and standalone boundary ([#32](https://github.com/opsdevcode/specmint-language/issues/32)) ([a6998ab](https://github.com/opsdevcode/specmint-language/commit/a6998ab00615c4531c29e2940f5578ae62973772))

## [0.6.0-alpha.2](https://github.com/opsdevcode/specmint-language/compare/v0.5.0-alpha.2...v0.6.0-alpha.2) (2026-10-09)


### Features

* **mint:** bind github-first catalog coordinates ([#25](https://github.com/opsdevcode/specmint-language/issues/25)) ([41eddf0](https://github.com/opsdevcode/specmint-language/commit/41eddf0e79bcbf514a9ab83e9e8bdf0453c5d751))

## [0.5.0-alpha.2](https://github.com/opsdevcode/specmint-language/compare/v0.4.0-alpha.2...v0.5.0-alpha.2) (2026-10-09)


### Features

* **mint:** add catalog records for public github integration ([#23](https://github.com/opsdevcode/specmint-language/issues/23)) ([71b88b5](https://github.com/opsdevcode/specmint-language/commit/71b88b52d326284bff2f99fbaf9a434ad817c792))

## [0.4.0-alpha.2](https://github.com/opsdevcode/specmint-language/compare/v0.3.0-alpha.2...v0.4.0-alpha.2) (2026-10-08)


### Features

* **mint:** add offline integration discovery and lockfile pinning ([#20](https://github.com/opsdevcode/specmint-language/issues/20)) ([eadbccd](https://github.com/opsdevcode/specmint-language/commit/eadbccd080fd13ee08d686d729f4e069a6f9823d))


### Documentation

* add integration author tutorial and local test ([#22](https://github.com/opsdevcode/specmint-language/issues/22)) ([9e02c89](https://github.com/opsdevcode/specmint-language/commit/9e02c89235d5129aa280e701a2a9bc1bbb957395))

## [0.3.0-alpha.2](https://github.com/opsdevcode/specmint-language/compare/v0.2.0-alpha.2...v0.3.0-alpha.2) (2026-10-08)


### Features

* **cli:** add doctor, init templates, and human diagnostics ([#16](https://github.com/opsdevcode/specmint-language/issues/16)) ([4e367fa](https://github.com/opsdevcode/specmint-language/commit/4e367fac6d53a488e1dc23bbc4b2bea01838871b))
* **mint:** add integration SDK, catalog records, and test kit ([#18](https://github.com/opsdevcode/specmint-language/issues/18)) ([0e044a9](https://github.com/opsdevcode/specmint-language/commit/0e044a901de43cc548a6da45969c1024854d408a))


### Documentation

* add ten-minute quickstart and release-please guards ([#19](https://github.com/opsdevcode/specmint-language/issues/19)) ([0395d7c](https://github.com/opsdevcode/specmint-language/commit/0395d7cb4e3e8b2821567860b85c2ab2705cef48))

## [0.2.0-alpha.2](https://github.com/opsdevcode/specmint-language/compare/v0.1.1-alpha.2...v0.2.0-alpha.2) (2026-10-04)


### Features

* publish VSIX and host public docs ([#13](https://github.com/opsdevcode/specmint-language/issues/13)) ([de29248](https://github.com/opsdevcode/specmint-language/commit/de2924882296afa50eb1da677ff35c4b4399c7d0))

## [0.1.1-alpha.2](https://github.com/opsdevcode/specmint-language/compare/v0.1.0-alpha.2...v0.1.1-alpha.2) (2026-10-04)


### Bug Fixes

* **release:** derive versioned surfaces automatically ([#12](https://github.com/opsdevcode/specmint-language/issues/12)) ([da9f0d5](https://github.com/opsdevcode/specmint-language/commit/da9f0d5598c9c118f3921815ff38ad0fd1f386da))
* **release:** provide repository context to gh ([#8](https://github.com/opsdevcode/specmint-language/issues/8)) ([ec1f184](https://github.com/opsdevcode/specmint-language/commit/ec1f184f3cff01e23bfabb04861f3c1c8dd4d654))
* **release:** use granted app permissions ([bd8f212](https://github.com/opsdevcode/specmint-language/commit/bd8f212179d9f0a0d0e37488ff894770d8260881))

## 0.1.0-alpha.2

Public-preview language release. Headline capability: **Mint Integration
Protocol v0** (intent, capability, target, integration, realization, plan,
approval, executor, verification, evidence, outcome).

- `pipx install specmint` and `uv tool install specmint` are the documented
  install paths for the `mint` CLI.
- Five-minute quickstart over the checked-in `local-marker` example.
- `mint.adapter/v0` remains the documented alpha compatibility alias.
- `mint apply` is not included. Not production-ready. Not 1.0.

Git tag: `v0.1.0-alpha.2`.

## 0.1.0-alpha.1

First public Mint language extract. Offline compiler, CLI, conformance, and
editor. `mint apply` is not included.

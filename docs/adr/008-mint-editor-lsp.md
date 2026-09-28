# ADR 008: Compiler-backed Mint LSP and private editor

**Status:** Accepted
**Date:** 2026-09-21

## Decision

Mint editor support is a **stdio** language server in this repository
plus a **private** VS Code / Cursor extension under `editors/vscode/`.
The server reuses `parse_mint_text`, `bind_modules`, `compile_program`,
and `format_source`. It does not add a second parser, resolver, or
formatter.

TextMate highlighting is lexical only. Semantic diagnostics, completion,
hover, navigation, find-references, and symbols come from the same
compiler pipeline as `mint check`. References are fqid identity inside
the current `mint.toml` project. Open buffers overlay disk bytes in
memory; the server does not write temp copies.

LSP positions are UTF-16 code units. Project discovery uses
`discover_manifest` (`mint.toml` parent walk). Unit loading stays inside
the project realpath.

The Python server has **no** third-party LSP library. The editor client
pins `vscode-languageclient==9.0.1` (stdio transport only). Security
review: no network listener, no telemetry, no update checks, no
credentials, no apply/deploy. Workspace Trust is required
(`untrustedWorkspaces.supported: false`).

The extension is LicenseRef-Proprietary, `private: true`, and is not
published to a marketplace. Local VSIX packaging is allowed; `*.vsix`
is gitignored.

## Consequences

- `mint lsp` and `specmint mint lsp` speak JSON-RPC on stdio.
- Language modules stay free of HTTP, CUE, and provider SDKs.
- Format-on-save in the editor is `format_source` (existing `mint fmt`).

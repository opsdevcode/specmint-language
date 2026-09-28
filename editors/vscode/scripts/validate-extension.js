"use strict";

const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const pkgPath = path.join(root, "package.json");
const grammarPath = path.join(root, "syntaxes", "mint.tmLanguage.json");
const extPath = path.join(root, "src", "extension.js");
const langPath = path.join(root, "language-configuration.json");

function fail(message) {
  console.error(message);
  process.exit(1);
}

const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
if (pkg.private !== true) {
  fail("package.json private must be true");
}
if (pkg.license !== "LicenseRef-Proprietary") {
  fail("package.json license must stay LicenseRef-Proprietary");
}
if (pkg.capabilities.untrustedWorkspaces.supported !== false) {
  fail("untrusted workspaces must be unsupported");
}
if (pkg.dependencies["vscode-languageclient"] !== "9.0.1") {
  fail("pin vscode-languageclient to 9.0.1");
}
if (JSON.stringify(pkg).includes("marketplace.visualstudio.com")) {
  fail("do not advertise marketplace URLs");
}

const grammar = JSON.parse(fs.readFileSync(grammarPath, "utf8"));
if (grammar.scopeName !== "source.mint") {
  fail("grammar scopeName must be source.mint");
}
const grammarBlob = JSON.stringify(grammar);
if (!grammarBlob.includes("comment.line") || !grammarBlob.includes("string.quoted")) {
  fail("grammar must stay lexical (comment/string)");
}
if (grammarBlob.includes("compile_program")) {
  fail("grammar must not encode compiler semantics");
}

for (const file of [extPath, langPath, path.join(root, "README.md")]) {
  if (!fs.existsSync(file)) {
    fail(`missing ${file}`);
  }
}

const source = fs.readFileSync(extPath, "utf8");
if (!source.includes("TransportKind.stdio")) {
  fail("extension must use stdio transport");
}
if (!source.includes("isTrusted")) {
  fail("extension must honor workspace trust");
}

JSON.parse(fs.readFileSync(langPath, "utf8"));
console.log("mint vscode extension manifest and grammar ok");

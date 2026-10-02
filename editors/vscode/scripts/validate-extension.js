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
if (pkg.private === true) {
  fail("public extract package.json must not set private");
}
if (pkg.license !== "Apache-2.0") {
  fail("package.json license must stay Apache-2.0");
}
if (pkg.publisher !== "opsdevcode" || pkg.name !== "mint-language") {
  fail("extension identity must stay opsdevcode.mint-language");
}
if (pkg.version !== "0.1.0-alpha.2") {
  fail("extension version must match Mint 0.1.0-alpha.2");
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

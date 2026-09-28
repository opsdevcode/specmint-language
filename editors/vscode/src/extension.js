"use strict";

const vscode = require("vscode");
const { LanguageClient, TransportKind } = require("vscode-languageclient/node");

/** @type {LanguageClient | undefined} */
let client;

/**
 * @param {import("vscode").ExtensionContext} context
 */
function activate(context) {
  if (!vscode.workspace.isTrusted) {
    return;
  }
  const config = vscode.workspace.getConfiguration("mint");
  const command = config.get("server.path") || "mint";
  const args = config.get("server.args") || ["lsp"];
  client = new LanguageClient(
    "mintLanguageServer",
    "Mint Language Server",
    {
      command,
      args,
      transport: TransportKind.stdio,
      options: { env: process.env },
    },
    {
      documentSelector: [{ scheme: "file", language: "mint" }],
      synchronize: { fileEvents: vscode.workspace.createFileSystemWatcher("**/*.mint") },
    }
  );
  client.start();
  context.subscriptions.push({
    dispose: () => {
      if (client) {
        client.stop();
      }
    },
  });
}

function deactivate() {
  if (!client) {
    return undefined;
  }
  return client.stop();
}

module.exports = { activate, deactivate };

"use strict";

const globals = {
  require: "readonly",
  module: "readonly",
  process: "readonly",
  __dirname: "readonly",
  console: "readonly",
};

module.exports = [
  {
    files: ["src/extension.js", "scripts/validate-extension.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "commonjs",
      globals,
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
];

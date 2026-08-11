import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier/flat";
import pluginVue from "eslint-plugin-vue";
import globals from "globals";

export default [
  {
    ignores: ["coverage/**", "dist/**", "node_modules/**"]
  },
  js.configs.recommended,
  ...pluginVue.configs["flat/essential"],
  {
    files: ["src/**/*.{js,vue}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.browser
    },
    rules: {
      "no-console": ["error", { allow: ["warn", "error"] }],
      "vue/no-mutating-props": ["error", { shallowOnly: true }]
    }
  },
  {
    files: ["*.config.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.nodeBuiltin
    }
  },
  eslintConfigPrettier
];

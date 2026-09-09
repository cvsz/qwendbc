import test from "node:test";
import assert from "node:assert/strict";

import {
  applyTheme,
  readThemePreference,
  resolveTheme,
  saveThemePreference,
} from "./theme.js";

test("system preference resolves to the current OS theme", () => {
  assert.equal(resolveTheme("system", true), "night");
  assert.equal(resolveTheme("system", false), "day");
});

test("invalid stored theme falls back to system", () => {
  const storage = { getItem: () => "neon" };
  assert.equal(readThemePreference(storage), "system");
});

test("storage failures fall back safely and do not escape", () => {
  const storage = {
    getItem() {
      throw new Error("storage unavailable");
    },
    setItem() {
      throw new Error("storage unavailable");
    },
  };

  assert.equal(readThemePreference(storage), "system");
  assert.doesNotThrow(() => saveThemePreference("night", storage));
});

test("applyTheme updates the root data attribute", () => {
  const root = { dataset: {} };
  assert.equal(applyTheme("night", root, false), "night");
  assert.equal(root.dataset.theme, "night");
});


export const THEME_OPTIONS = Object.freeze(["day", "night", "system"]);
export const THEME_STORAGE_KEY = "qwendbc.theme";

function isThemePreference(value) {
  return THEME_OPTIONS.includes(value);
}

function getDefaultStorage() {
  try {
    return globalThis.localStorage;
  } catch {
    return undefined;
  }
}

function getDefaultRoot() {
  try {
    return globalThis.document?.documentElement;
  } catch {
    return undefined;
  }
}

function getDefaultPrefersDark() {
  try {
    return globalThis.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  } catch {
    return false;
  }
}

export function readThemePreference(storage = getDefaultStorage()) {
  try {
    const preference = storage?.getItem(THEME_STORAGE_KEY);
    return isThemePreference(preference) ? preference : "system";
  } catch {
    return "system";
  }
}

export function saveThemePreference(preference, storage = getDefaultStorage()) {
  const safePreference = isThemePreference(preference) ? preference : "system";
  try {
    storage?.setItem(THEME_STORAGE_KEY, safePreference);
  } catch {
    // Private browsing and hardened browser contexts can reject storage access.
  }
}

export function resolveTheme(preference, prefersDark) {
  return preference === "night" || (preference === "system" && prefersDark)
    ? "night"
    : "day";
}

export function applyTheme(
  preference,
  root = getDefaultRoot(),
  prefersDark = getDefaultPrefersDark(),
) {
  const resolved = resolveTheme(
    isThemePreference(preference) ? preference : "system",
    Boolean(prefersDark),
  );
  if (root?.dataset) root.dataset.theme = resolved;
  return resolved;
}


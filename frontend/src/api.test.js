import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  ApiError,
  fetchHealth,
  fetchModelInfo,
  fetchModels,
  getAccessToken,
  parseCompletion,
  parseSseEvents,
  saveAccessToken,
  unloadModel,
} from "./api.js";

function response(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() {
      return body;
    },
  };
}

test("ControlPanel does not expose unsupported streaming controls or private API requests", () => {
  const source = readFileSync(new URL("./ControlPanel.jsx", import.meta.url), "utf8");

  assert.doesNotMatch(source, /\/model\/streaming/);
  assert.doesNotMatch(source, /function\s+requestJson\b/);
  assert.doesNotMatch(source, /Streaming responses|toggleStreaming/);
});

test("fetchModels uses the API base URL and parses the catalog", async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return response({ object: "list", data: [], providers: [] });
  };

  try {
    const result = await fetchModels();
    assert.deepEqual(result, { object: "list", data: [], providers: [] });
    assert.equal(calls[0].url, "/api/v1/models");
    assert.equal(calls[0].options.method, "GET");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchHealth attaches a session access token without exposing it in errors", async () => {
  const originalFetch = globalThis.fetch;
  const storage = {
    getItem(key) {
    assert.equal(key, "ai-dbc.accessToken");
      return "operator-secret";
    },
  };
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return response({ status: "healthy" });
  };

  try {
    const result = await fetchHealth({ storage });
    assert.deepEqual(result, { status: "healthy" });
    assert.equal(request.url, "/api/v1/health");
    assert.equal(request.options.headers.Authorization, "Bearer operator-secret");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchModelInfo uses bearer auth with the model info URL and GET method", async () => {
  const calls = [];
  const storage = {
    getItem(key) {
      assert.equal(key, "ai-dbc.accessToken");
      return "test-token";
    },
  };
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    return response({ name: "test-model" });
  };

  await fetchModelInfo({ storage, fetchImpl });

  assert.equal(calls[0].url, "/api/v1/model/info");
  assert.equal(calls[0].options.method, "GET");
  assert.equal(calls[0].options.headers.Authorization, "Bearer test-token");
});

test("unloadModel uses bearer auth with the unload URL and POST method", async () => {
  const calls = [];
  const storage = {
    getItem(key) {
      assert.equal(key, "ai-dbc.accessToken");
      return "test-token";
    },
  };
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    return response(null, 204);
  };

  await unloadModel({ storage, fetchImpl });

  assert.equal(calls[0].url, "/api/v1/model/unload");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.headers.Authorization, "Bearer test-token");
});

test("operator access tokens stay in session storage and can be cleared", () => {
  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };

  saveAccessToken("  operator-secret  ", storage);
  assert.equal(getAccessToken(storage), "operator-secret");
  saveAccessToken("", storage);
  assert.equal(getAccessToken(storage), "");
});

test("API errors expose status and a user-safe message only", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    response({ detail: "database password=do-not-expose" }, 500);

  try {
    await assert.rejects(
      () => fetchModels(),
      (error) => {
        assert.ok(error instanceof ApiError);
        assert.equal(error.status, 500);
        assert.match(error.message, /backend is unavailable/i);
        assert.doesNotMatch(error.message, /database|password|do-not-expose/i);
        return true;
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("parseCompletion validates the assistant content shape", () => {
  assert.equal(
    parseCompletion({ choices: [{ message: { content: "answer" } }] }),
    "answer",
  );
  assert.throws(() => parseCompletion({ choices: [] }), /invalid chat response/i);
});

test("parseSseEvents ignores comments and stops at DONE", () => {
  assert.deepEqual(
    [...parseSseEvents(": keepalive\n\ndata: {\"choices\":[]}\n\ndata: [DONE]\n")],
    [{ choices: [] }],
  );
});

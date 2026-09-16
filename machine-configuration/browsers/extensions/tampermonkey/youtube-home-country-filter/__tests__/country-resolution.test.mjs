import assert from "node:assert/strict";
import { test } from "node:test";
import { browser, brazil, unitedStates, unknown } from "./browser-fixture.mjs";

test("resolves country with two anonymous field-filtered requests and reuses it", async () => {
  const page = browser({ userscript: false });
  assert.equal(await page.resolver.lookup(brazil), "Brazil");
  assert.equal(await page.resolver.lookup(brazil), "Brazil");
  assert.equal(page.requests.length, 2);
  for (const request of page.requests) {
    assert.equal(request.credentials, "omit");
    assert.equal(request.body.context.client.hl, "en");
    assert.ok(request.signal instanceof AbortSignal);
    assert.match(request.url, /fields=/);
    assert.doesNotMatch(request.url, /key=/);
  }
  assert.equal(page.requests[0].body.browseId, brazil);
  assert.equal(page.requests[1].body.continuation, brazil);
  assert.match(
    decodeURIComponent(page.requests[1].url),
    /aboutChannelViewModel\(channelId,country\)/,
  );
});

test("refreshes known countries after seven days and restores persisted cache", async () => {
  const page = browser({ userscript: false });
  await page.resolver.lookup(brazil);
  const restored = browser({
    userscript: false,
    storage: Object.fromEntries(page.storage),
  });
  assert.equal(await restored.resolver.lookup(brazil), "Brazil");
  assert.equal(restored.requests.length, 0);
  page.advance(604800001);
  await page.resolver.lookup(brazil);
  assert.equal(page.requests.length, 4);
});

test("missing country stays unknown and is retried after one day", async () => {
  const page = browser({ userscript: false });
  assert.equal(await page.resolver.lookup(unknown), null);
  page.advance(86399999);
  assert.equal(await page.resolver.lookup(unknown), null);
  assert.equal(page.requests.length, 2);
  page.advance(2);
  await page.resolver.lookup(unknown);
  assert.equal(page.requests.length, 4);
});

test("an unrelated channel in an About response cannot classify the requested channel", async () => {
  const page = browser({
    userscript: false,
    fetch: async (body) => ({
      ok: true,
      json: async () =>
        body.browseId
          ? { header: { continuationCommand: { token: "about" } } }
          : { aboutChannelViewModel: { channelId: brazil, country: "Brazil" } },
    }),
  });
  assert.equal(await page.resolver.lookup(unitedStates), null);
  assert.equal(page.resolver.cached(unitedStates), null);
});

test("rate limiting pauses all new lookups for five minutes but still serves cache", async () => {
  const page = browser({
    userscript: false,
    fetch: async () => ({ ok: false, status: 429 }),
  });
  assert.equal(await page.resolver.lookup(brazil), null);
  assert.equal(await page.resolver.lookup(unitedStates), null);
  assert.equal(page.requests.length, 1);
  page.advance(300001);
  await page.resolver.lookup(unitedStates);
  assert.equal(page.requests.length, 2);
});

test("malformed responses and network failures fail open and are briefly cached", async () => {
  for (const fetch of [
    async () => {
      throw new Error("Network unavailable");
    },
    async () => ({ ok: true, json: async () => ({}) }),
    async () => ({
      ok: true,
      json: async () => {
        throw new SyntaxError("Invalid JSON");
      },
    }),
  ]) {
    const page = browser({ userscript: false, fetch });
    assert.equal(await page.resolver.lookup(brazil), null);
    assert.equal(await page.resolver.lookup(brazil), null);
    assert.equal(page.requests.length, 1);
    page.advance(300001);
    await page.resolver.lookup(brazil);
    assert.equal(page.requests.length, 2);
  }
});

test("corrupt or unavailable storage does not prevent filtering", async () => {
  for (const value of [
    "broken",
    "null",
    "{}",
    '[["channel",{"country":{},"expires":9999999}]]',
  ]) {
    const page = browser({
      userscript: false,
      storageDenied: true,
      storage: { "youtube-home-country-cache-v1": value },
    });
    assert.equal(await page.resolver.lookup(brazil), "Brazil");
    assert.equal(page.resolver.cached("channel"), undefined);
  }
});

test("persistent country cache never exceeds 256 channels", async () => {
  const page = browser({ userscript: false });
  for (let index = 0; index < 260; index += 1)
    await page.resolver.lookup(`channel-${index}`);
  const entries = JSON.parse(page.storage.get("youtube-home-country-cache-v1"));
  assert.equal(entries.length, 256);
  assert.equal(page.resolver.cached("channel-0"), undefined);
  assert.equal(page.resolver.cached("channel-259"), null);
});

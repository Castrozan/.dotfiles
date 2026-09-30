import assert from "node:assert/strict";
import { test } from "node:test";
import { Element } from "./element-fixture.mjs";
import { browser, brazil, unitedStates, settle } from "./browser-fixture.mjs";

test("processes visible channel lookups serially", async () => {
  let release;
  let activeRequests = 0;
  let maximumActiveRequests = 0;
  const waiting = new Promise((resolve) => {
    release = resolve;
  });
  const cards = [brazil, unitedStates].map(
    (identifier) => new Element(identifier),
  );
  const page = browser({
    cards,
    fetch: async () => {
      activeRequests += 1;
      maximumActiveRequests = Math.max(maximumActiveRequests, activeRequests);
      await waiting;
      activeRequests -= 1;
      return { ok: false };
    },
  });
  page.visible(...cards);
  await settle();
  assert.equal(page.requests.length, 1);
  release();
  await settle();
  assert.equal(page.requests.length, 2);
  assert.equal(maximumActiveRequests, 1);
});

test("processes arrivals across queue completion", async () => {
  for await (const delay of Array.from({ length: 30 }, (_, index) => index)) {
    const first = new Element(brazil);
    const second = new Element(unitedStates);
    const page = browser({ cards: [first, second] });
    page.visible(first);
    await Array.from({ length: delay }).reduce(
      (waiting) => waiting.then(() => undefined),
      Promise.resolve(),
    );
    page.visible(second);
    await settle();
    assert.equal(
      page.requests.length,
      4,
      `Arrival delayed by ${delay} microtasks`,
    );
  }
});

import assert from "node:assert/strict";
import { test } from "node:test";
import { Element } from "./element-fixture.mjs";
import {
  browser,
  brazil,
  unitedStates,
  unknown,
  marker,
  settle,
} from "./browser-fixture.mjs";

test("filters Brazil only and does not request countries for offscreen cards", async () => {
  const cards = [brazil, unitedStates, unknown].map(
    (identifier) => new Element(identifier),
  );
  const page = browser({ cards });
  await settle();
  assert.equal(page.requests.length, 0);
  page.visible(...cards);
  await settle();
  assert.deepEqual(
    cards.map((card) => card.hasAttribute(marker)),
    [true, false, false],
  );
  assert.equal(page.requests.length, 6);
});

test("repeated channels share lookups and new pagination cards are observed", async () => {
  const first = new Element(brazil);
  const second = new Element(brazil);
  const page = browser({ cards: [first, second] });
  page.visible(first, second);
  await settle();
  assert.equal(page.requests.length, 2);
  const next = new Element(brazil);
  page.home.append(next);
  page.mutate(page.home, [next]);
  assert.ok(page.observed().has(next));
  assert.equal(next.hasAttribute(marker), true);
  assert.equal(page.requests.length, 2);
});

test("recycled cards lose an old channel's hidden state", async () => {
  const card = new Element(brazil);
  const page = browser({ cards: [card] });
  page.visible(card);
  await settle();
  assert.equal(card.hasAttribute(marker), true);
  card.replaceChannel(unitedStates);
  page.mutate(card);
  assert.equal(card.hasAttribute(marker), false);
  await settle();
  assert.equal(card.hasAttribute(marker), false);
});

test("a late country response cannot hide a card reused for another channel", async () => {
  let release;
  const waiting = new Promise((resolve) => {
    release = resolve;
  });
  const card = new Element(brazil);
  const page = browser({
    cards: [card],
    fetch: async (body) => {
      if (body.browseId) await waiting;
      return {
        ok: true,
        json: async () =>
          body.browseId
            ? { continuationCommand: { token: body.browseId } }
            : {
                aboutChannelViewModel: {
                  channelId: body.continuation,
                  country:
                    body.continuation === brazil ? "Brazil" : "United States",
                },
              },
      };
    },
  });
  page.visible(card);
  card.replaceChannel(unitedStates);
  page.mutate(card);
  release();
  await settle();
  assert.equal(card.hasAttribute(marker), false);
});

test("does no work on search or watch and resumes on a cached homepage", async () => {
  const card = new Element(brazil);
  const page = browser({ cards: [card], pathname: "/results" });
  page.visible(card);
  await settle();
  assert.equal(page.requests.length, 0);
  page.navigate("/");
  page.visible(card);
  await settle();
  assert.equal(card.hasAttribute(marker), true);
  page.navigate("/watch");
  assert.equal(
    page.documentElement.hasAttribute("data-youtube-country-home"),
    false,
  );
  assert.equal(page.observed().size, 0);
  page.navigate("/");
  assert.equal(
    page.documentElement.hasAttribute("data-youtube-country-home"),
    true,
  );
  assert.equal(card.hasAttribute(marker), true);
  assert.equal(page.requests.length, 2);
});

test("does not classify playlists, Shorts shelves, or cards without an uploader", async () => {
  const playlist = new Element(brazil);
  playlist.data.content.lockupViewModel.contentType =
    "LOCKUP_CONTENT_TYPE_PLAYLIST";
  const missing = new Element();
  missing.card = true;
  const page = browser({ cards: [playlist, missing] });
  page.visible(playlist, missing);
  await settle();
  assert.equal(page.requests.length, 0);
  assert.equal(playlist.hasAttribute(marker), false);
  assert.equal(missing.hasAttribute(marker), false);
  missing.replaceChannel(brazil);
  page.mutate(missing);
  await settle();
  assert.equal(missing.hasAttribute(marker), true);
});

test("detached cards are released from the viewport observer", () => {
  const card = new Element(brazil);
  const page = browser({ cards: [card] });
  card.isConnected = false;
  page.home.children = [];
  page.mutate(page.home, [], [card]);
  assert.equal(page.observed().has(card), false);
  card.isConnected = true;
  page.home.append(card);
  page.mutate(page.home, [card]);
  assert.equal(page.observed().has(card), true);
});

test("expired country decisions are removed before returning to the homepage", async () => {
  const card = new Element(brazil);
  const page = browser({ cards: [card] });
  page.visible(card);
  await settle();
  assert.equal(card.hasAttribute(marker), true);
  page.navigate("/watch");
  page.advance(604800001);
  page.navigate("/");
  assert.equal(card.hasAttribute(marker), false);
  page.visible(card);
  await settle();
  assert.equal(card.hasAttribute(marker), true);
  assert.equal(page.requests.length, 4);
});

// ==UserScript==
// @name         YouTube Home Country Filter
// @version      1.0.2
// @description  Hide homepage video cards by their channel's declared country. Unknown countries remain visible.
// @author       Minamoto-no-Raikou
// @match        https://www.youtube.com/*
// @run-at       document-end
// @grant        none
// @noframes
// @require      https://raw.githubusercontent.com/Castrozan/.dotfiles/f31e110b59772c3864b64f76a3d4bc10ebcc27d1/machine-configuration/browsers/extensions/tampermonkey/youtube-home-country-filter/channel-country.js
// ==/UserScript==

const blockedCountries = new Set(["BR"]);

(function () {
  "use strict";
  const regionNames = new Intl.DisplayNames(["en"], { type: "region" });
  const blockedNames = new Set(
    [...blockedCountries].map((code) => regionNames.of(code)),
  );
  const marker = "data-youtube-country-hidden";
  const selector = "ytd-rich-item-renderer";
  const pending = new Set();
  let visible = new WeakSet();
  const identities = new WeakMap();
  let home = null;
  let working = false;
  const style = document.createElement("style");
  style.textContent = `html[data-youtube-country-home] ytd-browse[page-subtype="home"] ${selector}[${marker}] { display: none !important; }`;
  document.head.append(style);

  function channelId(card) {
    const model = card.data?.content?.lockupViewModel;
    if (model?.contentType !== "LOCKUP_CONTENT_TYPE_VIDEO") return null;
    const avatar =
      model.metadata?.lockupMetadataViewModel?.image?.decoratedAvatarViewModel;
    const identifier =
      avatar?.rendererContext?.commandContext?.onTap?.innertubeCommand
        ?.browseEndpoint?.browseId;
    return /^UC[\w-]{22}$/.test(identifier) ? identifier : null;
  }

  async function filterCard(card) {
    const identifier = channelId(card);
    if (!isFilterableCard(card, identifier)) return;
    const country = await youtubeChannelCountries.lookup(identifier);
    if (cardStillMatchesIdentifier(card, identifier)) {
      card.toggleAttribute(marker, blockedNames.has(country));
    }
  }

  function isFilterableCard(card, identifier) {
    return Boolean(identifier && card.isConnected && visible.has(card));
  }

  function cardStillMatchesIdentifier(card, identifier) {
    return home?.contains(card) && channelId(card) === identifier;
  }

  async function drain() {
    if (working) return;
    if (!pending.size) return;
    if (!home) return;
    if (location.pathname !== "/") return;
    working = true;
    const card = pending.values().next().value;
    pending.delete(card);
    try {
      await filterCard(card);
    } finally {
      working = false;
      void drain();
    }
  }

  const viewport = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          visible.add(entry.target);
          consider(entry.target);
        } else {
          visible.delete(entry.target);
          pending.delete(entry.target);
        }
      }
      void drain();
    },
    { rootMargin: "500px" },
  );

  function consider(card) {
    if (!home?.contains(card)) return;
    const identifier = channelId(card);
    observeChangedCardIdentity(card, identifier);
    if (!identifier) return;
    applyCachedCountryOrQueue(card, identifier);
  }

  function observeChangedCardIdentity(card, identifier) {
    if (identities.get(card) === identifier) return;
    identities.set(card, identifier);
    card.removeAttribute(marker);
    viewport.observe(card);
  }

  function applyCachedCountryOrQueue(card, identifier) {
    const country = youtubeChannelCountries.cached(identifier);
    if (country !== undefined) {
      card.toggleAttribute(marker, blockedNames.has(country));
    } else {
      card.removeAttribute(marker);
      if (visible.has(card)) pending.add(card);
    }
  }

  function scan(node) {
    if (!(node instanceof Element)) return;
    const card = node.closest(selector);
    if (card) consider(card);
    else node.querySelectorAll(selector).forEach(consider);
  }

  function release(node) {
    if (!(node instanceof Element) || node.isConnected) return;
    const cards = node.matches(selector)
      ? [node]
      : node.querySelectorAll(selector);
    for (const card of cards) {
      viewport.unobserve(card);
      visible.delete(card);
      identities.delete(card);
      pending.delete(card);
    }
  }

  const changes = new MutationObserver((records) => {
    processMutationRecords(records);
    void drain();
  });

  function processMutationRecords(records) {
    const roots = new Set();
    for (const record of records) {
      const owner = record.target.closest?.(selector);
      if (owner) roots.add(owner);
      collectAddedNodeRoots(record.addedNodes, roots);
      record.removedNodes.forEach(release);
    }
    roots.forEach(scan);
  }

  function collectAddedNodeRoots(addedNodes, roots) {
    for (const node of addedNodes) {
      if (node instanceof Element) roots.add(node.closest(selector) || node);
    }
  }

  function navigate() {
    const next =
      location.pathname === "/"
        ? document.querySelector('ytd-browse[page-subtype="home"]')
        : null;
    document.documentElement.toggleAttribute(
      "data-youtube-country-home",
      Boolean(next),
    );
    if (next === home) return;
    changes.disconnect();
    viewport.disconnect();
    visible = new WeakSet();
    pending.clear();
    home = next;
    if (!home) return;
    changes.observe(home, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["href"],
    });
    home.querySelectorAll(selector).forEach((card) => {
      viewport.observe(card);
      consider(card);
    });
  }
  document.addEventListener("yt-navigate-finish", navigate);
  document.addEventListener("yt-page-data-updated", navigate);
  document.addEventListener("yt-navigate-start", () => {
    document.documentElement.toggleAttribute(
      "data-youtube-country-home",
      false,
    );
    changes.disconnect();
    viewport.disconnect();
    visible = new WeakSet();
    pending.clear();
    home = null;
  });
  navigate();
})();

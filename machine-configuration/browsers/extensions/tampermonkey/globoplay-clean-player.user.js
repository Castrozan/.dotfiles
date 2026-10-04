// ==UserScript==
// @name         Globoplay Clean Player
// @version      1.0.0
// @description  Strip Globoplay live channels down to the bare video filling the window: no site header, no media control bar, no channel carousel and its black fade, no Extras side panel, no skip buttons, no ad overlay. Click still toggles play, double click still toggles fullscreen, and keyboard shortcuts keep working. Every other Globoplay page keeps its layout.
// @author       zanoni
// @match        https://globoplay.globo.com/*
// @run-at       document-start
// @grant        GM_addStyle
// ==/UserScript==

(function () {
  "use strict";

  const LIVE_PAGE_ROOT = "html:has(.live-broadcast-view)";

  const hiddenSelectors = [
    ".header-container",
    ".header__placeholder",
    ".media-control",
    ".side-panel-live",
    ".top-navigation",
    ".live-navigation__panel-area",
    "#chatbot-area",
    ".dfp-ad-overlay",
  ];

  const viewportFillingSelectors = [
    ".application-controller__view",
    ".live-broadcast-view",
    ".player-with-broadcasts-navigation",
    ".live-navigation",
    ".live-navigation__player-area",
  ];

  const playerFillingSelectors = [
    ".playkit-player__fullscreen-player",
    ".playkit-player__fullscreen-player-inner",
    ".playkit-player__fullscreen-player-inner > div",
    ".clappr-player__main",
  ];

  function scopedToLivePage(selectors) {
    return selectors
      .map((selector) => `${LIVE_PAGE_ROOT} ${selector}`)
      .join(",\n");
  }

  GM_addStyle(
    [
      `${scopedToLivePage(hiddenSelectors)} { display: none !important; }`,
      `${scopedToLivePage(viewportFillingSelectors)} { height: 100vh !important; margin: 0 !important; padding: 0 !important; top: 0 !important; }`,
      `${scopedToLivePage(playerFillingSelectors)} { width: 100% !important; height: 100% !important; }`,
      `${LIVE_PAGE_ROOT} body { overflow: hidden !important; }`,
    ].join("\n"),
  );
})();

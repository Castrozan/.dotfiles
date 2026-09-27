// ==UserScript==
// @name         GitHub Native Single File Review
// @namespace    https://github.com/Castrozan/.dotfiles
// @version      1.0.0
// @description  Open GitHub pull request changes in native single-file mode while keeping the complete file tree.
// @author       zanoni
// @match        https://github.com/*
// @run-at       document-start
// @grant        window.onurlchange
// @noframes
// ==/UserScript==

(function () {
  "use strict";

  function enableSingleFileReview() {
    const reviewUrl = new URL(window.location.href);

    if (!/^\/[^/]+\/[^/]+\/pull\/\d+\/changes\/?$/.test(reviewUrl.pathname)) {
      return;
    }

    if (reviewUrl.searchParams.get("mode") === "single") return;

    reviewUrl.searchParams.set("mode", "single");
    window.location.replace(reviewUrl.href);
  }

  window.addEventListener("urlchange", enableSingleFileReview);
  enableSingleFileReview();
})();

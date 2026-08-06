// ==UserScript==
// @name         LinkedIn Feed Removal
// @version      1.1.0
// @description  Strip the LinkedIn home feed down to a centered profile card: no post stream, no composer, no sort control, no right rail with puzzles and suggestions, and no premium upsell or shortcut menu in the left rail. The For Business menu and the premium chip leave the top nav on every page. Single post permalinks and every other LinkedIn page keep their content.
// @author       zanoni
// @match        https://www.linkedin.com/*
// @run-at       document-start
// @grant        GM_addStyle
// ==/UserScript==

(function () {
  "use strict";

  const FEED_ROUTE_PATHNAME = /^\/(feed\/?)?$/;
  const FEED_REMOVED_ROOT_CLASS = "linkedin-feed-removed";
  const HIDDEN_SIDEBAR_BLOCK_CLASS = "linkedin-feed-removed-sidebar-block";
  const SIDEBAR_NOISE_LINK_SELECTOR =
    'a[href*="/premium/"], a[href*="/my-items/"]';
  const SIDEBAR_COLUMN_WIDTH = "216px";

  const everyPageCssRules = [
    'header nav:has(button[aria-label="For Business"]) { display: none !important; }',
    'header a:has(svg[id^="premium-chip"]) { display: none !important; }',
  ];

  const feedPageCssRules = [
    `.${FEED_REMOVED_ROOT_CLASS} section[aria-label="Primary content"] { display: none !important; }`,
    `.${FEED_REMOVED_ROOT_CLASS} aside[aria-label="Aside"] { display: none !important; }`,
    `.${FEED_REMOVED_ROOT_CLASS} .${HIDDEN_SIDEBAR_BLOCK_CLASS} { display: none !important; }`,
    `.${FEED_REMOVED_ROOT_CLASS} aside[aria-label="Sidebar"] { grid-column: 1 / -1 !important; justify-self: center !important; width: ${SIDEBAR_COLUMN_WIDTH} !important; }`,
  ];

  let injectedStyle = null;

  function ensureStyle() {
    if (injectedStyle && injectedStyle.isConnected) return;

    injectedStyle = GM_addStyle(
      everyPageCssRules.concat(feedPageCssRules).join("\n"),
    );
  }

  function isFeedRoute() {
    return FEED_ROUTE_PATHNAME.test(location.pathname);
  }

  function sidebarBlockStack(sidebar) {
    let stack = sidebar;

    while (stack.children.length === 1) stack = stack.firstElementChild;

    return stack;
  }

  function hideSidebarNoiseBlocks() {
    const sidebar = document.querySelector('aside[aria-label="Sidebar"]');

    if (!sidebar) return;

    for (const block of sidebarBlockStack(sidebar).children) {
      if (block.querySelector(SIDEBAR_NOISE_LINK_SELECTOR)) {
        block.classList.add(HIDDEN_SIDEBAR_BLOCK_CLASS);
      }
    }
  }

  let pendingFrame = 0;

  function apply() {
    if (pendingFrame) {
      cancelAnimationFrame(pendingFrame);
      pendingFrame = 0;
    }

    const root = document.documentElement;

    if (!root) return;

    ensureStyle();

    const onFeedRoute = isFeedRoute();

    root.classList.toggle(FEED_REMOVED_ROOT_CLASS, onFeedRoute);

    if (onFeedRoute) hideSidebarNoiseBlocks();
  }

  function scheduleApply() {
    if (pendingFrame) return;

    pendingFrame = requestAnimationFrame(apply);
  }

  function watchRouteChanges() {
    const nativePushState = history.pushState;
    const nativeReplaceState = history.replaceState;

    history.pushState = function () {
      const result = nativePushState.apply(this, arguments);
      apply();
      return result;
    };

    history.replaceState = function () {
      const result = nativeReplaceState.apply(this, arguments);
      apply();
      return result;
    };

    window.addEventListener("popstate", apply);
  }

  new MutationObserver(scheduleApply).observe(document, {
    childList: true,
    subtree: true,
  });

  watchRouteChanges();
  apply();
})();

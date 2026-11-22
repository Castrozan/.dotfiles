(function () {
  "use strict";

  const STYLE_ID = "ytweak-style";
  const TABS_ID = "ytweak-tabs";
  let mastheadOrigin = null;

  const cssRules = [
    "ytd-watch-flexy { --ytweak-col: min(1600px, 92vw); }",
    "ytd-app { --ytd-masthead-height: 45px !important; }",
    "#masthead-container.ytd-app, ytd-masthead#masthead, ytd-masthead #background.ytd-masthead, ytd-masthead #container.ytd-masthead { height: 45px !important; min-height: 45px !important; }",
    "ytd-page-manager.ytd-app { margin-top: 45px !important; }",
    "html.ytweak-header-below-video ytd-app { --ytd-masthead-height: 0px !important; }",
    "html.ytweak-header-below-video ytd-page-manager.ytd-app { margin-top: 0 !important; }",
    "html.ytweak-header-below-video #masthead-container.ytd-app { visibility: hidden !important; position: relative !important; inset: auto !important; width: 100% !important; margin: 8px auto 16px !important; transform: none !important; }",
    "html.ytweak-header-below-video #masthead-container.ytd-app:has(+ ytd-watch-metadata) { visibility: visible !important; }",
    "html.ytweak-header-below-video #skip-navigation:not(:focus-within) { clip-path: inset(50%) !important; }",
    "ytd-watch-flexy[theater] #full-bleed-container { height: calc(100vh - 53px) !important; max-height: calc(100vh - 53px) !important; }",
    "html.ytweak-header-below-video ytd-watch-flexy[theater] #full-bleed-container { height: 100vh !important; max-height: 100vh !important; }",
    "ytd-watch-flexy[theater] #columns { display: flex !important; flex-direction: column !important; align-items: center !important; }",
    "ytd-watch-flexy[theater] #primary, ytd-watch-flexy[theater] #primary-inner { width: 100% !important; max-width: var(--ytweak-col) !important; margin: 0 auto !important; }",
    "ytd-watch-flexy[theater] #secondary { width: 100% !important; max-width: var(--ytweak-col) !important; margin: 12px auto 0 !important; padding: 0 !important; }",
    "ytd-watch-flexy[theater] #secondary #related ytd-item-section-renderer > #contents { display: grid !important; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)) !important; gap: 16px 20px !important; }",
    "ytd-watch-flexy[theater] #secondary yt-lockup-view-model { width: 100% !important; max-width: none !important; }",
    "ytd-watch-flexy #comments { display: none !important; }",
    "ytd-watch-flexy.ytweak-comments #comments { display: block !important; width: 100% !important; max-width: var(--ytweak-col) !important; margin: 0 auto !important; }",
    "ytd-watch-flexy.ytweak-comments #secondary { display: none !important; }",
    "#ytweak-tabs { display: flex; gap: 8px; margin: 16px auto 8px; }",
    "#ytweak-tabs button { font: 500 14px/1 Roboto, system-ui, sans-serif; padding: 10px 20px; border-radius: 18px; border: none; cursor: pointer; background: var(--yt-spec-badge-chip-background, #272727); color: var(--yt-spec-text-primary, #f1f1f1); transition: background .15s; }",
    "#ytweak-tabs button.active { background: var(--yt-spec-call-to-action, #3ea6ff); color: #0f0f0f; }",
  ];

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;

    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = cssRules.join("\n");
    (document.head || document.documentElement).appendChild(style);
  }

  function refitPlayer() {
    window.dispatchEvent(new Event("resize"));
  }

  function placeMasthead() {
    const masthead = document.getElementById("masthead-container");
    const metadata = document.querySelector(
      "ytd-watch-flexy ytd-watch-metadata",
    );
    const belowVideo =
      location.pathname === "/watch" && Boolean(metadata?.isConnected);

    if (!masthead) return false;

    mastheadOrigin ??= {
      parent: masthead.parentNode,
      nextSibling: masthead.nextSibling,
    };

    if (belowVideo) {
      if (metadata.previousElementSibling !== masthead)
        metadata.before(masthead);
    } else if (masthead.parentNode !== mastheadOrigin.parent) {
      const nextSibling = mastheadOrigin.nextSibling;
      mastheadOrigin.parent.insertBefore(
        masthead,
        nextSibling?.parentNode === mastheadOrigin.parent ? nextSibling : null,
      );
    }

    return belowVideo;
  }

  function mountTabs() {
    const flexy = document.querySelector("ytd-watch-flexy");
    const comments = document.querySelector("#comments");

    if (!flexy || !comments) return false;

    const existing = document.getElementById(TABS_ID);

    if (existing?.parentElement === comments.parentElement) {
      return true;
    }

    if (existing) existing.remove();

    flexy.classList.remove("ytweak-comments");

    const tabs = document.createElement("div");
    tabs.id = TABS_ID;

    const makeButton = (tab, label, active) => {
      const button = document.createElement("button");
      button.dataset.tab = tab;
      button.textContent = label;

      if (active) button.classList.add("active");

      return button;
    };

    tabs.appendChild(makeButton("suggestions", "Suggestions", true));
    tabs.appendChild(makeButton("comments", "Comments", false));

    tabs.addEventListener("click", (event) => {
      const button = event.target.closest("button");

      if (!button) return;

      flexy.classList.toggle(
        "ytweak-comments",
        button.dataset.tab === "comments",
      );

      tabs
        .querySelectorAll("button")
        .forEach((other) => other.classList.toggle("active", other === button));
    });

    comments.parentElement.insertBefore(tabs, comments);

    return true;
  }

  let pollTimer = null;
  let refitScheduled = false;

  function scheduleRefit() {
    if (refitScheduled) return;

    refitScheduled = true;

    [0, 300, 800, 1500].forEach((delay) => setTimeout(refitPlayer, delay));

    setTimeout(() => {
      refitScheduled = false;
    }, 1600);
  }

  function apply() {
    document.documentElement.classList.toggle(
      "ytweak-header-below-video",
      location.pathname === "/watch",
    );
    ensureStyle();

    if (pollTimer) clearInterval(pollTimer);

    if (location.pathname !== "/watch") {
      placeMasthead();
      return;
    }

    let attempts = 0;

    if (!(mountTabs() && placeMasthead())) {
      pollTimer = setInterval(() => {
        const mounted = mountTabs() && placeMasthead();
        if (mounted || ++attempts > 40) {
          clearInterval(pollTimer);
          pollTimer = null;
          if (!mounted) {
            document.documentElement.classList.remove(
              "ytweak-header-below-video",
            );
          }
        }
      }, 250);
    }

    scheduleRefit();
  }

  function watchTheaterAttribute() {
    const flexy = document.querySelector("ytd-watch-flexy");

    if (!flexy || flexy.__ytweakObserved) return;

    flexy.__ytweakObserved = true;

    new MutationObserver(refitPlayer).observe(flexy, {
      attributes: true,
      attributeFilter: ["theater"],
    });
  }

  window.addEventListener("yt-navigate-finish", () => {
    apply();
    watchTheaterAttribute();
  });

  window.addEventListener("yt-page-data-updated", () => {
    apply();
    watchTheaterAttribute();
  });

  apply();
  watchTheaterAttribute();
})();

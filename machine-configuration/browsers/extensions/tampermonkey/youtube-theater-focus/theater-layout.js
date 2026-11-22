(() => {
  "use strict";

  const TABS_ID = "ytweak-tabs";
  let mastheadOrigin = null;

  function refitPlayer() {
    window.dispatchEvent(new Event("resize"));
  }

  function restoreMasthead(masthead) {
    if (masthead.parentNode === mastheadOrigin.parent) return;

    const nextSibling = mastheadOrigin.nextSibling;
    mastheadOrigin.parent.insertBefore(
      masthead,
      nextSibling?.parentNode === mastheadOrigin.parent ? nextSibling : null,
    );
  }

  function isWatchMetadataConnected(metadata) {
    return location.pathname === "/watch" && Boolean(metadata?.isConnected);
  }

  function placeMasthead() {
    const masthead = document.getElementById("masthead-container");
    const metadata = document.querySelector(
      "ytd-watch-flexy ytd-watch-metadata",
    );
    const belowVideo = isWatchMetadataConnected(metadata);

    if (!masthead) return false;

    mastheadOrigin ??= {
      parent: masthead.parentNode,
      nextSibling: masthead.nextSibling,
    };

    if (belowVideo) {
      if (metadata.previousElementSibling !== masthead)
        metadata.before(masthead);
    } else {
      restoreMasthead(masthead);
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

  function pollForLayout() {
    let attempts = 0;
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

  function apply() {
    document.documentElement.classList.toggle(
      "ytweak-header-below-video",
      location.pathname === "/watch",
    );

    if (pollTimer) clearInterval(pollTimer);

    if (location.pathname !== "/watch") {
      placeMasthead();
      return;
    }

    if (!(mountTabs() && placeMasthead())) {
      pollForLayout();
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

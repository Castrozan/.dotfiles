// ==UserScript==
// @name         YouTube Theater Focus Layout
// @version      1.5.0
// @description  Theater player fills the viewport (title below the fold), header 20% smaller, comments behind a tab, suggestions as a big centered grid, and a page loaded into a hidden tab stays paused until that tab is first shown
// @author       zanoni
// @match        https://www.youtube.com/*
// @run-at       document-start
// @grant        none
// ==/UserScript==
(function () {
  "use strict";
  const nativeMediaPlay = HTMLMediaElement.prototype.play;
  const nativeMediaPause = HTMLMediaElement.prototype.pause;
  let playbackIsHeld =
    document.visibilityState === "hidden" || document.prerendering === true;
  let heldVideo = null;
  let heldVideoWasMuted = false;
  let heldVideoResumePosition = 0;
  let escapedVideoObserver = null;

  function holdVideo(video) {
    if (heldVideo !== video) {
      heldVideo = video;
      heldVideoWasMuted = video.muted;
      heldVideoResumePosition =
        video.played && video.played.length > 0
          ? video.played.start(0)
          : video.currentTime;
    }
    try {
      nativeMediaPause.call(video);
      if (video.currentTime > heldVideoResumePosition + 0.05)
        video.currentTime = heldVideoResumePosition;
    } catch (ignored) {}
  }

  function holdEveryPlayingVideo() {
    const videos = document.getElementsByTagName("video");
    for (let index = 0; index < videos.length; index += 1)
      if (!videos[index].paused) holdVideo(videos[index]);
  }

  function catchEscapedPlayback(event) {
    if (playbackIsHeld && event.target instanceof HTMLMediaElement)
      holdVideo(event.target);
  }

  function releaseHoldWhenShown() {
    if (document.visibilityState === "visible") releaseHold();
  }

  function releaseHoldOnTrustedInteraction(event) {
    if (event.isTrusted) releaseHold();
  }

  const holdListeners = [
    ["play", catchEscapedPlayback, true],
    ["playing", catchEscapedPlayback, true],
    ["visibilitychange", releaseHoldWhenShown, false],
    ["prerenderingchange", releaseHoldWhenShown, false],
    ["pointerdown", releaseHoldOnTrustedInteraction, true],
    ["keydown", releaseHoldOnTrustedInteraction, true],
  ];

  function releaseHold() {
    if (!playbackIsHeld) return;
    playbackIsHeld = false;
    HTMLMediaElement.prototype.play = nativeMediaPlay;
    if (escapedVideoObserver) escapedVideoObserver.disconnect();
    holdListeners.forEach(([type, handler, capture]) =>
      document.removeEventListener(type, handler, capture),
    );
    if (!heldVideo) return;
    heldVideo.muted = heldVideoWasMuted;
    const moviePlayer = document.getElementById("movie_player");
    if (moviePlayer && typeof moviePlayer.playVideo === "function")
      moviePlayer.playVideo();
    else if (heldVideo.paused) nativeMediaPlay.call(heldVideo).catch(() => {});
    heldVideo = null;
  }

  if (playbackIsHeld) {
    HTMLMediaElement.prototype.play = function playHeldUntilTabIsShown() {
      if (!playbackIsHeld) return nativeMediaPlay.apply(this, arguments);
      holdVideo(this);
      return Promise.reject(
        new DOMException("play() held until shown", "NotAllowedError"),
      );
    };
    holdListeners.forEach(([type, handler, capture]) =>
      document.addEventListener(type, handler, capture),
    );
    escapedVideoObserver = new MutationObserver(holdEveryPlayingVideo);
    escapedVideoObserver.observe(document.documentElement || document, {
      childList: true,
      subtree: true,
    });
    holdEveryPlayingVideo();
  }

  const STYLE_ID = "ytweak-style";
  const TABS_ID = "ytweak-tabs";

  const cssRules = [
    "ytd-watch-flexy { --ytweak-col: min(1600px, 92vw); }",
    "ytd-app { --ytd-masthead-height: 45px !important; }",
    "#masthead-container.ytd-app, ytd-masthead#masthead, ytd-masthead #background.ytd-masthead, ytd-masthead #container.ytd-masthead { height: 45px !important; min-height: 45px !important; }",
    "ytd-page-manager.ytd-app { margin-top: 45px !important; }",
    "ytd-watch-flexy[theater] #full-bleed-container { height: calc(100vh - 53px) !important; max-height: calc(100vh - 53px) !important; }",
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

  function mountTabs() {
    const flexy = document.querySelector("ytd-watch-flexy");
    const comments = document.querySelector("#comments");
    if (!flexy || !comments) return false;
    const existing = document.getElementById(TABS_ID);
    if (existing && existing.nextElementSibling === comments) return true;
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
    ensureStyle();
    if (pollTimer) clearInterval(pollTimer);
    let attempts = 0;
    pollTimer = setInterval(() => {
      if (mountTabs() || ++attempts > 40) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    }, 250);
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

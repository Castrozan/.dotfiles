// ==UserScript==
// @name         YouTube No Background Autoplay
// @version      3.0.0
// @description  Stop a watch page from ever starting playback while its tab is unfocused or hidden and has never been viewed (no audio at all); start it when you focus the tab; never re-pause a video you are already watching
// @author       zanoni
// @match        https://www.youtube.com/*
// @run-at       document-start
// @grant        none
// ==/UserScript==
(function () {
  "use strict";

  function isActive() {
    return document.visibilityState === "visible" && document.hasFocus();
  }

  function findVideo() {
    return (
      document.querySelector("video.html5-main-video") ||
      document.querySelector("video")
    );
  }

  let hasBeenActive = isActive();
  let heldVideo = null;

  function shouldBlock() {
    return !hasBeenActive && !isActive();
  }

  const nativePlay = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function play() {
    if (shouldBlock()) {
      heldVideo = this;
      try {
        this.pause();
      } catch (ignored) {}
      return Promise.resolve();
    }
    return nativePlay.apply(this, arguments);
  };

  function release() {
    if (!isActive()) return;
    hasBeenActive = true;
    const video = heldVideo;
    heldVideo = null;
    if (video && video.paused) nativePlay.call(video).catch(() => {});
  }

  document.addEventListener(
    "play",
    (event) => {
      if (
        shouldBlock() &&
        event.target instanceof HTMLMediaElement &&
        !event.target.paused
      ) {
        heldVideo = event.target;
        event.target.pause();
      }
    },
    true,
  );

  document.addEventListener("visibilitychange", release);
  window.addEventListener("focus", release);

  setInterval(() => {
    if (isActive()) {
      release();
      return;
    }
    if (shouldBlock()) {
      const video = heldVideo || findVideo();
      if (video && !video.paused) {
        heldVideo = video;
        video.pause();
      }
    }
  }, 300);
})();

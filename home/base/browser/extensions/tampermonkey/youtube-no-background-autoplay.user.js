// ==UserScript==
// @name         YouTube No Background Autoplay
// @version      1.0.0
// @description  Hold a watch page paused while its tab is hidden; let it play the moment the tab is focused, so background tabs stay silent until visited
// @author       zanoni
// @match        https://www.youtube.com/*
// @run-at       document-start
// @grant        none
// ==/UserScript==
(function () {
  "use strict";

  let releasedForThisVideo = !document.hidden;
  let blockedWhileHidden = false;

  function findVideo() {
    return (
      document.querySelector("video.html5-main-video") ||
      document.querySelector("video")
    );
  }

  function holdPaused(mediaElement) {
    if (releasedForThisVideo || !document.hidden) return;
    if (!(mediaElement instanceof HTMLMediaElement)) return;
    blockedWhileHidden = true;
    mediaElement.pause();
  }

  document.addEventListener(
    "play",
    (event) => {
      holdPaused(event.target);
    },
    true,
  );

  setInterval(() => {
    if (releasedForThisVideo || !document.hidden) return;
    const video = findVideo();
    if (video && !video.paused) holdPaused(video);
  }, 400);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden || releasedForThisVideo) return;
    releasedForThisVideo = true;
    if (!blockedWhileHidden) return;
    const video = findVideo();
    if (video && video.paused) video.play().catch(() => {});
  });

  window.addEventListener("yt-navigate-finish", () => {
    if (document.hidden) {
      releasedForThisVideo = false;
      blockedWhileHidden = false;
    } else {
      releasedForThisVideo = true;
    }
  });
})();

(function () {
  "use strict";

  const nativeMediaPlay = HTMLMediaElement.prototype.play;
  const nativeMediaPause = HTMLMediaElement.prototype.pause;

  // Always arm the hold during startup.
  let playbackIsHeld = true;
  let heldVideo = null;
  let heldVideoWasMuted = false;
  let escapedVideoObserver = null;
  let foregroundEpoch = 0;

  function isActuallyForeground() {
    return (
      document.visibilityState === "visible" &&
      document.prerendering !== true &&
      document.hasFocus()
    );
  }

  function holdVideo(video) {
    if (heldVideo !== video) {
      heldVideo = video;
      heldVideoWasMuted = video.muted;
    }

    try {
      nativeMediaPause.call(video);
    } catch (error_) {}
  }

  function holdEveryPlayingVideo() {
    const videos = document.getElementsByTagName("video");

    for (const video of videos) {
      if (!video.paused) holdVideo(video);
    }
  }

  function catchEscapedPlayback(event) {
    if (playbackIsHeld && event.target instanceof HTMLMediaElement) {
      holdVideo(event.target);
    }
  }

  function foregroundSignal() {
    const epoch = ++foregroundEpoch;

    if (!isActuallyForeground()) return;

    // Require the foreground state to remain stable for two frames.
    requestAnimationFrame(() => {
      if (epoch !== foregroundEpoch || !isActuallyForeground()) return;

      requestAnimationFrame(() => {
        if (epoch === foregroundEpoch && isActuallyForeground()) {
          releaseHold();
        }
      });
    });
  }

  const heldPlay = function playHeldUntilTabIsFocused() {
    if (!playbackIsHeld) {
      return nativeMediaPlay.apply(this, arguments);
    }

    holdVideo(this);

    // Prevent YouTube from treating the hold as an autoplay error.
    return Promise.resolve();
  };

  function releaseHold() {
    if (!playbackIsHeld || !isActuallyForeground()) return;

    playbackIsHeld = false;
    ++foregroundEpoch;

    if (HTMLMediaElement.prototype.play === heldPlay) {
      HTMLMediaElement.prototype.play = nativeMediaPlay;
    }

    escapedVideoObserver?.disconnect();

    document.removeEventListener("play", catchEscapedPlayback, true);
    document.removeEventListener("playing", catchEscapedPlayback, true);
    document.removeEventListener("visibilitychange", foregroundSignal);
    document.removeEventListener("prerenderingchange", foregroundSignal);
    window.removeEventListener("focus", foregroundSignal, true);
    window.removeEventListener("blur", foregroundSignal, true);

    const video = heldVideo;
    heldVideo = null;

    if (!video) return;

    video.muted = heldVideoWasMuted;

    const moviePlayer = document.getElementById("movie_player");

    if (moviePlayer && typeof moviePlayer.playVideo === "function") {
      moviePlayer.playVideo();
    } else if (video.paused) {
      nativeMediaPlay.call(video).catch(() => {});
    }
  }

  HTMLMediaElement.prototype.play = heldPlay;

  document.addEventListener("play", catchEscapedPlayback, true);
  document.addEventListener("playing", catchEscapedPlayback, true);
  document.addEventListener("visibilitychange", foregroundSignal);
  document.addEventListener("prerenderingchange", foregroundSignal);
  window.addEventListener("focus", foregroundSignal, true);
  window.addEventListener("blur", foregroundSignal, true);

  escapedVideoObserver = new MutationObserver(holdEveryPlayingVideo);
  escapedVideoObserver.observe(document.documentElement || document, {
    childList: true,
    subtree: true,
  });

  holdEveryPlayingVideo();
  setTimeout(foregroundSignal, 0);
})();

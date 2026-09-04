{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  miwayomiDockerfilePath = ../../stack/miwayomi.Dockerfile;
  miwayomiDockerfileText =
    if builtins.pathExists miwayomiDockerfilePath then builtins.readFile miwayomiDockerfilePath else "";
  subtitleTracksPatchPath = ../../stack/miwayomi-subtitle-tracks.patch;
  subtitleTracksPatchText =
    if builtins.pathExists subtitleTracksPatchPath then
      builtins.readFile subtitleTracksPatchPath
    else
      "";
  productionSourcesPatchPath = ../../stack/miwayomi-production-sources.patch;
  productionSourcesPatchText =
    if builtins.pathExists productionSourcesPatchPath then
      builtins.readFile productionSourcesPatchPath
    else
      "";

  sidecarSubtitleTracksReachThePlayer =
    lib.hasInfix "COPY miwayomi-subtitle-tracks.patch /tmp/miwayomi-subtitle-tracks.patch" miwayomiDockerfileText
    && lib.hasInfix "RUN git apply /tmp/miwayomi-subtitle-tracks.patch" miwayomiDockerfileText
    && lib.hasInfix "function configureSubtitleTracks(video, subtitleTracks, headersEnc)" subtitleTracksPatchText
    && lib.hasInfix ''video.querySelectorAll("track").forEach((subtitleElement) => subtitleElement.remove());'' subtitleTracksPatchText
    && lib.hasInfix "const seenSubtitleUrls = new Set();" subtitleTracksPatchText
    && lib.hasInfix ''subtitleElement.kind = "subtitles";'' subtitleTracksPatchText
    && lib.hasInfix ''subtitleElement.track.mode = "disabled";'' subtitleTracksPatchText
    && !(lib.hasInfix "subtitleElement.default =" subtitleTracksPatchText)
    && lib.hasInfix "     video.src = proxyBase;\n   }\n+  configureSubtitleTracks(video, v.subtitleTracks || [], headersEnc);\n }" subtitleTracksPatchText;
  productionSourcesExcludeTestFixtures =
    lib.hasInfix "COPY miwayomi-production-sources.patch /tmp/miwayomi-production-sources.patch" miwayomiDockerfileText
    && lib.hasInfix "RUN git apply /tmp/miwayomi-production-sources.patch" miwayomiDockerfileText
    && lib.hasInfix "-import miwayomi.builtin.DemoSource" productionSourcesPatchText
    && lib.hasInfix "-import miwayomi.builtin.MockCfSource" productionSourcesPatchText
    && lib.hasInfix "-    Injekt.get<MangaSourceManager>().register(DemoSource())" productionSourcesPatchText
    && lib.hasInfix "-    Injekt.get<MangaSourceManager>().register(MockCfSource())" productionSourcesPatchText;
in
{
  chise-miwayomi-player-renders-sidecar-subtitles =
    mkEvalCheck "chise-miwayomi-player-renders-sidecar-subtitles" sidecarSubtitleTracksReachThePlayer
      "Miwayomi must translate extension-provided sidecar VTT tracks into native browser subtitle tracks through its same-origin proxy";

  chise-miwayomi-production-sources-exclude-test-fixtures =
    mkEvalCheck "chise-miwayomi-production-sources-exclude-test-fixtures"
      productionSourcesExcludeTestFixtures
      "Miwayomi must not register upstream's Demo and MockCF development fixtures as production manga sources";
}

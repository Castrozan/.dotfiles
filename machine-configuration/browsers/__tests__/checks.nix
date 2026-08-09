{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../firefox/firefox-home-manager.nix
    ../chrome/chrome-global-linux-home-manager.nix
  ];

  chromeBrokenHardwareVideoDecodingWorkaround =
    import ../chrome/broken-hardware-video-decoding/chrome-broken-hardware-video-decoding-workaround.nix
      {
        inherit pkgs;
        chromePackage = pkgs.hello;
      };
in
{
  domain-browser-firefox-enabled =
    mkEvalCheck "domain-browser-firefox-enabled" cfg.programs.firefox.enable
      "firefox should be enabled";

  domain-browser-chrome-desktop-entry = mkEvalCheck "domain-browser-chrome-desktop-entry" (
    cfg.xdg.dataFile ? "applications/chrome-global.desktop"
  ) "chrome desktop entry should be in XDG_DATA_HOME";

  domain-browser-chrome-no-remote-debugging-flag =
    let
      desktopSource = cfg.xdg.dataFile."applications/chrome-global.desktop".source or "";
    in
    mkEvalCheck "domain-browser-chrome-no-remote-debugging-flag"
      (!lib.hasInfix "--remote-debugging-port" (builtins.toString desktopSource))
      "chrome-global desktop entry should not have --remote-debugging-port (bare Chrome for autoConnect stealth)";

  domain-browser-chrome-disables-accelerated-video-decode =
    mkEvalCheck "domain-browser-chrome-disables-accelerated-video-decode"
      (builtins.elem "--disable-accelerated-video-decode" chromeBrokenHardwareVideoDecodingWorkaround.flagsThatStopChromeAdvertisingCodecsItCannotDecode)
      "Chrome must launch with --disable-accelerated-video-decode. VA-API decode fails to initialize its frame pool on this hybrid NVIDIA/AMD laptop, so every codec already falls back to software, but Chrome keeps answering canPlayType('video/mp4; codecs=\"hvc1\"') with 'probably'. Jellyfin builds its device profile from that answer, direct-plays HEVC files instead of transcoding them, and the browser stalls forever on PIPELINE_ERROR_DECODE with nothing shown to the user. --disable-features=PlatformHEVCDecoderSupport and --disable-features=VaapiVideoDecoder both leave the false claim in place; only this flag clears it";

  domain-browser-chrome-launcher-uses-hardware-video-decoding-workaround =
    mkEvalCheck "domain-browser-chrome-launcher-uses-hardware-video-decoding-workaround"
      (lib.any (
        package: (lib.getName package) == "google-chrome-without-broken-hardware-video-decoding"
      ) cfg.home.packages)
      "The chrome-global launcher must ship the wrapped Chrome rather than latest.google-chrome directly, so the flag reaches every entry point that resolves google-chrome-stable on PATH instead of only the desktop entry";
}

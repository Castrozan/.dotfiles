{ pkgs, ... }:
let
  browser = pkgs.writeShellScriptBin "chromium" ''
    printf '%s\n' "$@"
  '';
  arguments = {
    pkgs = pkgs // {
      chromium = browser;
    };
    nodejs = pkgs.nodejs_22;
  };
  standard = import ../opencli-jobs.nix arguments;
  muted = import ../opencli-jobs.nix (arguments // { muteAudio = true; });
in
pkgs.lib.optionalAttrs pkgs.stdenv.isLinux {
  browser-opencli-mute-is-opt-in = pkgs.runCommand "browser-opencli-mute-is-opt-in" { } ''
    standard_browser=$(${pkgs.gnused}/bin/sed -n 's/^export OPENCLI_BROWSER=//p' ${standard.runner}/bin/opencli-run)
    muted_browser=$(${pkgs.gnused}/bin/sed -n 's/^export OPENCLI_BROWSER=//p' ${muted.runner}/bin/opencli-run)
    test "$standard_browser" = ${browser}/bin/chromium
    "$standard_browser" '--user-data-dir=profile with spaces' --headless=new about:blank > standard
    "$muted_browser" '--user-data-dir=profile with spaces' --headless=new about:blank > muted
    printf '%s\n' --mute-audio > expected
    cat standard >> expected
    cmp muted expected
    touch "$out"
  '';
}

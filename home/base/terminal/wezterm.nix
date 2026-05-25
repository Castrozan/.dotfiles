{
  pkgs,
  inputs,
  isNixOS,
  latest,
  ...
}:
let
  nixglWrap = import ../../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  weztermAfterNixGL = nixglWrap.wrapWithNixGLIntel {
    package = latest.wezterm;
    binaries = [
      "wezterm"
      "wezterm-gui"
    ];
  };

  weztermBundledBinariesForDarwinAppLaunchers = pkgs.symlinkJoin {
    name = "wezterm-darwin-app-bundle";
    paths = [ weztermAfterNixGL ];
    postBuild = ''
      darwinAppBundleContentsMacOS="$out/Applications/WezTerm.app/Contents/MacOS"
      mkdir -p "$darwinAppBundleContentsMacOS"
      for darwinAppBundleExecutable in wezterm wezterm-gui wezterm-mux-server strip-ansi-escapes wezterm.sh; do
        ln -s "${latest.wezterm}/Applications/WezTerm.app/$darwinAppBundleExecutable" \
          "$darwinAppBundleContentsMacOS/$darwinAppBundleExecutable"
      done
    '';
  };

  weztermPackage =
    if pkgs.stdenv.hostPlatform.isDarwin then
      weztermBundledBinariesForDarwinAppLaunchers
    else
      weztermAfterNixGL;
in
{
  home.file.".config/wezterm/wallpaper.png".source = ../../../static/wallpaper.png;

  programs.wezterm = {
    enable = true;
    package = weztermPackage;
    extraConfig = builtins.readFile ../../../.config/wezterm/wezterm.lua;
  };
}

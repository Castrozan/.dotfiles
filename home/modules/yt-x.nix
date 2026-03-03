{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  mpvWrappedWithNixGL = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.mpv;
    binaries = [ "mpv" ];
  };
in
{
  home.packages = [
    inputs.yt-x.packages.${pkgs.stdenv.hostPlatform.system}.default
    mpvWrappedWithNixGL
    pkgs.yt-dlp
    pkgs.jq
    pkgs.fzf
    pkgs.ffmpeg
    pkgs.gum
  ];
}

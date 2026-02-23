{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  mpvPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.mpv;
    binaries = [ "mpv" ];
  };
in
{
  home.packages = [
    pkgs.ani-cli
    mpvPackage
    pkgs.mpv-handler
    pkgs.mpvc
    pkgs.mpv-shim-default-shaders
  ];

  programs.fish.shellAliases = {
    ani-cli = "ani-cli --no-detach";
  };

  home.file.".config/mpv/mpv.conf".text = ''
    vo=kitty
    video-sync=display-resample
    interpolation=no
    tscale=oversample
    ao=pulse
    hwdec=no
    cache=yes
    cache-secs=60
  '';
}

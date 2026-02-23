{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  flameshotPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.flameshot;
    binaries = [ "flameshot" ];
  };
in
{
  services.flameshot = {
    enable = true;
    package = flameshotPackage;
  };
}

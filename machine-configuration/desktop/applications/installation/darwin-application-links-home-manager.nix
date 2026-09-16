{ lib, pkgs, ... }:
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    targets.darwin = {
      copyApps.enable = false;
      linkApps.enable = true;
    };
  };
}

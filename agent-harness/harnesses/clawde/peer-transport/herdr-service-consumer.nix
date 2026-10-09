{ lib, pkgs, ... }:
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
    systemd.user.services.clawde.Unit = {
      Wants = [ "herdr.service" ];
      After = [ "herdr.service" ];
    };
  };
}

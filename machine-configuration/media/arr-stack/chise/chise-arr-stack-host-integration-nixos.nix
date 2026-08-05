{ lib, ... }:
let
  machineIdentityMapPath = ../../../../private-configuration/machines.nix;
  chiseTailnetBindAddress =
    if builtins.pathExists machineIdentityMapPath then
      (import machineIdentityMapPath).chise.tailscaleIp
    else
      null;
in
{
  networking.hosts = lib.optionalAttrs (chiseTailnetBindAddress != null) {
    "${chiseTailnetBindAddress}" = [ "arr" ];
  };

  hardware.nvidia-container-toolkit.enable = true;
}

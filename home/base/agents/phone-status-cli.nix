{ pkgs, ... }:
let
  phoneStatusScriptSource = ../../../agents/commands/scripts/phone-status.sh;

  phoneStatusCli = pkgs.writeShellScriptBin "phone-status" ''
    set -Eeuo pipefail

    export PATH="${pkgs.openssh}/bin:${pkgs.coreutils}/bin:''${PATH:+:$PATH}"
    exec ${pkgs.bash}/bin/bash "${phoneStatusScriptSource}" "$@"
  '';
in
{
  home.packages = [ phoneStatusCli ];
}

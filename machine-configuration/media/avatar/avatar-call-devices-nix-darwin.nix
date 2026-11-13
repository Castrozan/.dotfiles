{ lib, pkgs, ... }:
let
  driver =
    channel:
    "${
      pkgs.blackhole.override { inherit channel; }
    }/Library/Audio/Plug-Ins/HAL/BlackHole${channel}.driver";
in
{
  homebrew.casks = [ "obs" ];
  system.activationScripts.postActivation.text = lib.mkAfter ''
    ${pkgs.python312}/bin/python3 ${./scripts/conversation/remote_seat/install_call_audio_drivers.py} ${driver "2ch"} ${driver "16ch"} || echo "Installing the avatar's call audio drivers failed; continuing activation" >&2
  '';
}

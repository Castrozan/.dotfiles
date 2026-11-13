{ lib, pkgs, ... }:
let
  sharedPlugInFactory = "e395c745-4eea-4d94-bb92-46224221047c";
  callSpeakerPlugInFactory = "05aefe08-00d9-4e93-9951-5d19dc1aa184";
  driverBundle = package: channel: "${package}/Library/Audio/Plug-Ins/HAL/BlackHole${channel}.driver";
  callMicrophone = pkgs.blackhole.override { channel = "2ch"; };
  callSpeaker = (pkgs.blackhole.override { channel = "16ch"; }).overrideAttrs (previous: {
    postPatch = (previous.postPatch or "") + ''
      substituteInPlace BlackHole/BlackHole.plist --replace-fail ${sharedPlugInFactory} ${callSpeakerPlugInFactory}
    '';
  });
in
{
  homebrew.casks = [ "obs" ];
  system.activationScripts.postActivation.text = lib.mkAfter ''
    ${pkgs.python312}/bin/python3 ${./scripts/conversation/remote_seat/install_call_audio_drivers.py} ${driverBundle callMicrophone "2ch"} ${driverBundle callSpeaker "16ch"} || echo "Installing the avatar's call audio drivers failed; continuing activation" >&2
  '';
}

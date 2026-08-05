{ pkgs, ... }:
let
  homeAssistantHostSshAlias = "chise";

  remoteHomeAssistantBinaryNames = [
    "ha-light"
    "ha-light-scene-cycle"
    "ha-ac-toggle"
  ];

  makeRemoteHomeAssistantWrapper =
    remoteBinaryName:
    pkgs.writeShellApplication {
      name = remoteBinaryName;
      runtimeInputs = [ pkgs.openssh ];
      text = ''
        exec ssh ${homeAssistantHostSshAlias} -- ${remoteBinaryName} "$@"
      '';
    };
in
{
  home.packages = map makeRemoteHomeAssistantWrapper remoteHomeAssistantBinaryNames;
}

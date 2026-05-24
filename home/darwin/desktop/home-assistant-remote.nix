{ pkgs, ... }:
let
  remoteSshHostAlias = "nixos";

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
        exec ssh ${remoteSshHostAlias} -- ${remoteBinaryName} "$@"
      '';
    };
in
{
  home.packages = map makeRemoteHomeAssistantWrapper remoteHomeAssistantBinaryNames;
}

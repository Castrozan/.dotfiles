{
  config,
  lib,
  pkgs,
  inputs,
  ...
}:
let
  a2aTransportSource = import ./a2a-source.nix { inherit pkgs inputs; };
in
{
  config = lib.mkIf (config.clawde.agents != { }) {
    systemd.user.services = lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      clawde-a2a.Service.Environment = lib.mkAfter [ "PYTHONPATH=${a2aTransportSource}" ];
    };
    launchd.agents = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      clawde-a2a.config.EnvironmentVariables.PYTHONPATH = lib.mkForce "${a2aTransportSource}";
    };
  };
}

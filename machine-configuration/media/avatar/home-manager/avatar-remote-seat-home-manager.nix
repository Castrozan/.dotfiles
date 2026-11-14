{
  pkgs,
  lib,
  inputs,
  isNixOS,
  ...
}:
let
  programs = import ../avatar-programs.nix { inherit pkgs lib inputs; };
in
{
  config = lib.mkIf isNixOS {
    systemd.user.services.avatar-remote-seat = {
      Unit.Description = "Avatar microphone and voice lent by another machine";
      Service = {
        ExecStart = toString programs.remoteSeat;
        ExecStopPost = "${pkgs.systemd}/bin/systemctl --user --no-block stop avatar-conversation.target avatar-listener.service";
      };
    };
  };
}

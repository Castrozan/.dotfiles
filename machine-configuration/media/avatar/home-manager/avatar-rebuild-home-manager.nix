{ lib, isNixOS, ... }:
let
  keepRunningThroughRebuild =
    names:
    lib.genAttrs names (_: {
      Unit.X-SwitchMethod = "keep-old";
    });
in
{
  config = lib.mkIf isNixOS {
    systemd.user.targets = keepRunningThroughRebuild [
      "avatar"
      "avatar-conversation"
    ];
    systemd.user.services = keepRunningThroughRebuild [
      "avatar-audio"
      "avatar-browser"
      "avatar-camera"
      "avatar-control-server"
      "avatar-listener"
      "avatar-live"
      "avatar-remote-seat"
      "avatar-renderer"
      "avatar-room-microphone"
      "avatar-transcriber"
    ];
  };
}

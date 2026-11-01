{
  config,
  inputs,
  pkgs,
  latest,
  lib,
  ...
}:
let
  hexDictationNotifier = pkgs.writeShellApplication {
    name = "hex-dictation-notifier";
    runtimeInputs = with pkgs; [
      coreutils
      libnotify
      systemd
    ];
    text = ''
      exec ${pkgs.python312}/bin/python3 ${./scripts/hex_dictation_notifier.py} "$@"
    '';
  };
in
{
  imports = [ inputs.hex.homeManagerModules.hex ];

  programs.hex = {
    enable = true;
    # Hex's parser needs Rust >= 1.97; retain host libraries for Vulkan.
    package = inputs.hex.packages.${pkgs.stdenv.hostPlatform.system}.default.override {
      rustPlatform = pkgs.makeRustPlatform {
        inherit (latest) cargo rustc;
      };
    };
    autostart = true;
    shortcut = "control+option+space";
    model = "parakeet_v3";
    language = "en";
    settings = (builtins.fromJSON (builtins.readFile ./hex-settings.json)) // {
      # Follow the system-selected microphone, including a Bluetooth headset.
      avoid_bluetooth_microphone = false;
    };
  };

  systemd.user.services.hex-dictation-notifier = {
    Unit = {
      Description = "Desktop notifications for Hex dictation";
      After = [ "hex.service" ];
      PartOf = [ "graphical-session.target" ];
    };
    Service = {
      ExecStart = "${lib.getExe hexDictationNotifier} ${config.xdg.dataHome}/hex/logs/live.ndjson";
      Restart = "on-failure";
      RestartSec = 5;
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };

  # Hyprland registers portal shortcuts without assigning their preferred keys.
  xdg.configFile."hypr-host/input.conf".text = lib.mkAfter ''
    bindd = CTRL ALT, SPACE, HEX dictation, global, anomaly.hex:dictation-CTRL-ALT-space
    bindd = CTRL ALT, V, Paste last HEX dictation, global, anomaly.hex:paste-last-CTRL-ALT-v
  '';
}

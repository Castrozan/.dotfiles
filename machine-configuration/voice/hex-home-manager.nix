{
  inputs,
  pkgs,
  latest,
  lib,
  ...
}:
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
    autostart = false;
    shortcut = "control+option+space";
    model = "parakeet_v3";
    language = "en";
    settings = (builtins.fromJSON (builtins.readFile ./hex-settings.json)) // {
      # Follow the system-selected microphone, including a Bluetooth headset.
      avoid_bluetooth_microphone = false;
    };
  };

  # Hyprland registers portal shortcuts without assigning their preferred keys.
  xdg.configFile."hypr-host/input.conf".text = lib.mkAfter ''
    bindd = CTRL ALT, SPACE, HEX dictation, global, anomaly.hex:dictation-CTRL-ALT-space
    bindd = CTRL ALT, V, Paste last HEX dictation, global, anomaly.hex:paste-last-CTRL-ALT-v
  '';
}

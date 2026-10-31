{
  inputs,
  pkgs,
  latest,
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
    settings = builtins.fromJSON (builtins.readFile ./hex-settings.json);
  };
}

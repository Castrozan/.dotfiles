{ inputs, ... }:
{
  imports = [ inputs.hex.homeManagerModules.hex ];

  programs.hex = {
    enable = true;
    autostart = false;
    shortcut = "control+option+space";
    model = "parakeet_v3";
    language = "en";
    settings = builtins.fromJSON (builtins.readFile ./hex-settings.json);
  };
}

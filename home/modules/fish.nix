{ pkgs, ... }:
let
  shellInit = builtins.readFile ../../shell/fish/config.fish;
in
{
  home.packages = with pkgs; [
    fishPlugins.bass
    carapace
  ];

  programs.fish = {
    enable = true;
    package = pkgs.fish;
    interactiveShellInit = "${shellInit}";
    plugins = [
      {
        name = "bass";
        src = pkgs.fishPlugins.bass;
      }
      {
        name = "fzf-fish";
        src = pkgs.fishPlugins.fzf-fish;
      }
      {
        name = "autopair";
        src = pkgs.fishPlugins.autopair;
      }
      {
        name = "sponge";
        src = pkgs.fishPlugins.sponge;
      }
      {
        name = "puffer";
        src = pkgs.fishPlugins.puffer;
      }
    ];
  };

  programs.carapace = {
    enable = true;
    enableFishIntegration = true;
  };

  # Fish conf.d scripts
  xdg.configFile."fish/conf.d/hyprland-env.fish".source = ../../shell/fish/conf.d/hyprland-env.fish;
  xdg.configFile."fish/conf.d/betha-secrets.fish".source = ../../shell/fish/conf.d/betha-secrets.fish;
}

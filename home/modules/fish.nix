{ pkgs, ... }:
let
  shellInit = builtins.readFile ../../shell/fish/config.fish;
in
{
  home.packages = with pkgs; [
    fishPlugins.bass
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
    ];
  };

  # Fish conf.d scripts
  xdg.configFile."fish/conf.d/hyprland-env.fish".source = ../../shell/fish/conf.d/hyprland-env.fish;
  xdg.configFile."fish/conf.d/tmux.fish".source = ../../shell/fish/conf.d/tmux.fish;
}

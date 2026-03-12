{ pkgs, lib, ... }:
let
  shellInit = builtins.readFile ./shell/fish/config.fish;
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
    ]
    ++ lib.optionals (!pkgs.stdenv.isDarwin) [
      {
        name = "fzf-fish";
        src = pkgs.fishPlugins.fzf-fish;
      }
    ];
  };

  programs.zoxide = {
    enable = true;
    enableFishIntegration = true;
  };

  programs.carapace = {
    enable = true;
    enableFishIntegration = true;
  };

  xdg.configFile = {
    "fish/conf.d/bass-env.fish".source = ./shell/fish/bass_env.fish;
    "fish/conf.d/tmux.fish".source = ./shell/fish/conf.d/tmux.fish;
    "fish/conf.d/fish-aliases.fish".source = ./shell/fish/conf.d/fish_aliases.fish;
    "fish/conf.d/fzf.fish".source = ./shell/fish/conf.d/fzf.fish;
    "fish/conf.d/default-directories.fish".source = ./shell/fish/conf.d/default_directories.fish;
    "fish/conf.d/key-bindings.fish".source = ./shell/fish/conf.d/key_bindings.fish;
    "fish/conf.d/hyprland-env.fish".source = ./shell/fish/conf.d/hyprland-env.fish;
    "fish/conf.d/betha-secrets.fish".source = ./shell/fish/conf.d/betha-secrets.fish;

    "fish/functions/fish_prompt.fish".source = ./shell/fish/functions/fish_prompt.fish;
    "fish/functions/cursor.fish".source = ./shell/fish/functions/cursor.fish;
    "fish/functions/nix.fish".source = ./shell/fish/functions/nix.fish;
  };
}

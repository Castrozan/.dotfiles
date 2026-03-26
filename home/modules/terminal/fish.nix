{ pkgs, lib, ... }:
let
  shellInit = builtins.readFile ./shell/fish/config.fish;

  bashAliasesFileContent = builtins.readFile ./shell/aliases.sh;

  allBashSourceLines = lib.splitString "\n" bashAliasesFileContent;

  bashAliasLinePattern = "[[:space:]]*alias[[:space:]]+([^=]+)=(.*)";
  bashExportLinePattern = "[[:space:]]*export[[:space:]]+([^=]+)=(.*)";

  convertBashAliasLineToFishAlias =
    line:
    let
      matched = builtins.match bashAliasLinePattern line;
    in
    if matched != null then "alias ${builtins.elemAt matched 0} ${builtins.elemAt matched 1}" else null;

  convertBashExportLineToFishExport =
    line:
    let
      matched = builtins.match bashExportLinePattern line;
      name = if matched != null then builtins.elemAt matched 0 else "";
    in
    if matched != null && name != "PATH" && name != "XDG_DATA_DIRS" then
      "set -gx ${name} ${builtins.elemAt matched 1}"
    else
      null;

  convertedFishAliases = builtins.filter (x: x != null) (
    builtins.map convertBashAliasLineToFishAlias allBashSourceLines
  );

  convertedFishExports = builtins.filter (x: x != null) (
    builtins.map convertBashExportLineToFishExport allBashSourceLines
  );

  fishSpecificAliasOverrides = [
    "alias source-shell 'source ~/.dotfiles/home/modules/terminal/shell/fish/config.fish'"
  ];

  generatedFishAliasesAndExports =
    lib.concatStringsSep "\n" (
      convertedFishExports ++ convertedFishAliases ++ fishSpecificAliasOverrides
    )
    + "\n";
in
{
  home.packages = with pkgs; [
    carapace
    fishPlugins.bass
  ];

  programs = {
    fish = {
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
        {
          name = "fzf-fish";
          src = pkgs.fishPlugins.fzf-fish;
        }
      ];
    };

    zoxide = {
      enable = true;
      enableFishIntegration = true;
    };

    carapace = {
      enable = true;
      enableFishIntegration = true;
    };
  };

  xdg.configFile = {
    "fish/conf.d/shell-env.fish".source = ./shell/fish/shell_env.fish;
    "fish/conf.d/tmux.fish".source = ./shell/fish/conf.d/tmux.fish;
    "fish/conf.d/fish-aliases.fish".text = generatedFishAliasesAndExports;
    "fish/conf.d/fzf.fish".source = ./shell/fish/conf.d/fzf.fish;
    "fish/conf.d/default-directories.fish".source = ./shell/fish/conf.d/default_directories.fish;
    "fish/conf.d/key-bindings.fish".source = ./shell/fish/conf.d/key_bindings.fish;
    "fish/conf.d/private-aliases.fish".source = ./shell/fish/conf.d/private_aliases.fish;

    "fish/functions/fish_prompt.fish".source = ./shell/fish/functions/fish_prompt.fish;
    "fish/functions/cursor.fish".source = ./shell/fish/functions/cursor.fish;
    "fish/functions/nix.fish".source = ./shell/fish/functions/nix.fish;

    "fish/conf.d/hyprland-env.fish".source = ./shell/fish/conf.d/hyprland-env.fish;
    "fish/conf.d/betha-secrets.fish".source = ./shell/fish/conf.d/betha-secrets.fish;
  };
}

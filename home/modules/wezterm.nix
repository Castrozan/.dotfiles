{ ... }:
{
  home.file.".config/wezterm/wallpaper.png".source = ../../static/wallpaper.png;

  programs.wezterm = {
    enable = true;
    extraConfig = builtins.readFile ../../.config/wezterm/wezterm.lua;
  };
}

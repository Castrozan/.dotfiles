{
  pkgs,
  config,
  ...
}: {
  # kitty configuration
  home.file.".config/kitty/current-theme.conf".source = ../../../.config/kitty/current-theme.conf;
  home.file.".config/kitty/kitty.conf".source = ../../../.config/kitty/kitty.conf;
  home.file.".config/kitty/startup.conf".source = ../../../.config/kitty/startup.conf;
}
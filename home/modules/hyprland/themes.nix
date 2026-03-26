{ config, ... }:
let
  dotfilesStaticPath = "${config.home.homeDirectory}/.dotfiles/static";
  wallpaperFiles = [
    "polunochnie-progulki.gif"
    "alter-jellyfish.jpg"
    "alter-jellyfish-dark.jpg"
    "wallpaper.png"
  ];
in
{
  home = {
    activation.initHyprTheme = ''
      mkdir -p $HOME/.config/hypr-theme/current/theme
      mkdir -p $HOME/.config/hypr-theme/user-themes
      mkdir -p $HOME/.config/hypr-theme/backgrounds
      mkdir -p $HOME/.config/hypr-theme/wallpapers
      touch $HOME/.config/hypr-theme/current/theme/hyprland.conf

      ${builtins.concatStringsSep "\n      " (
        map (
          file: ''ln -sf "${dotfilesStaticPath}/${file}" "$HOME/.config/hypr-theme/wallpapers/${file}"''
        ) wallpaperFiles
      )}
    '';
  };
}

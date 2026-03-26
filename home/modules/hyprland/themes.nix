{ config, ... }:
let
  dotfilesStaticPath = "${config.home.homeDirectory}/.dotfiles/static";
  wallpaperFiles = [
    "alter-jellyfish-dark.jpg"
    "alter-jellyfish.jpg"
    "catppuccin-latte.png"
    "catppuccin-waves.png"
    "catppuccin.png"
    "ethereal.jpg"
    "everforest.jpg"
    "flexoki-light.png"
    "gruvbox.jpg"
    "hackerman.jpg"
    "kanagawa.jpg"
    "matte-black.jpg"
    "nord.png"
    "osaka-jade.jpg"
    "polunochnie-progulki.gif"
    "ristretto.jpg"
    "rose-pine.jpg"
    "tokyo-night.jpg"
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

{ config, ... }:
let
  dotfilesStaticPath = "${config.home.homeDirectory}/.dotfiles/static";
  wallpaperFiles = [
    "Milad-Fakurian-Abstract-Purple-Blue.jpg"
    "alter-jellyfish-dark.jpg"
    "alter-jellyfish.jpg"
    "cat-blue-eye-mocha.png"
    "catppuccin-latte.png"
    "catppuccin-waves.png"
    "catppuccin.png"
    "ethereal-3.jpg"
    "ethereal.jpg"
    "everforest.jpg"
    "flexoki-light-omarchy.png"
    "flexoki-light.png"
    "gruvbox.jpg"
    "hackerman-3.jpg"
    "hackerman.jpg"
    "kanagawa.jpg"
    "leafy-dawn-omarchy.png"
    "matte-black-hands.jpg"
    "matte-black.jpg"
    "nord.png"
    "osaka-jade-2.jpg"
    "osaka-jade-3.jpg"
    "osaka-jade.jpg"
    "polunochnie-progulki.gif"
    "ristretto.jpg"
    "rose-pine.jpg"
    "scenery-pink-lakeside-sunset-lake-landscape-scenic-panorama-7680x3215-144.png"
    "ship-at-sea.jpg"
    "tokyo-night.jpg"
    "wallpaper.png"
    "wave-light.png"
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

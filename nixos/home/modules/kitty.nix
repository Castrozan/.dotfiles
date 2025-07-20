{ pkgs, ... }:
{
  home.file.".config/kitty/startup.conf".source = ../../../.config/kitty/startup.conf;
  home.file.".config/kitty/wallpaper.png".source = ../../../resources/wallpaper.png;

  programs.kitty = {
    enable = true;
    themeFile = "Catppuccin-Mocha";
    font = {
      name = "Fira Code";
      size = 18;
      package = pkgs.fira-code;
    };
    settings = {
      confirm_os_window_close = 0;
      dynamic_background_opacity = true;
      enable_audio_bell = false;
      mouse_hide_wait = "-1.0";
      window_padding_width = 10;
      background_opacity = "1.0";
      background_image = "wallpaper.png";
      startup_session = "startup.conf";
      background_image_layout = "cscaled";
      hide_window_decorations = "yes";
    };
  };
}

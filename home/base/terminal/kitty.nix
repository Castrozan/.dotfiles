{
  pkgs,
  lib,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  kittyPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.kitty;
    binaries = [ "kitty" ];
  };
in
{
  home.file.".config/kitty/startup.conf".source = ../../../.config/kitty/startup.conf;
  home.file.".config/kitty/wallpaper.png".source = ../../../static/wallpaper.png;

  programs.kitty = {
    enable = true;
    package = kittyPackage;
    themeFile = lib.mkDefault "Catppuccin-Mocha";
    font = {
      name = lib.mkDefault "Fira Code";
      size = lib.mkDefault 16;
      package = lib.mkDefault pkgs.fira-code;
    };
    settings = {
      shell = if pkgs.stdenv.hostPlatform.isDarwin then "/run/current-system/sw/bin/bash" else "bash";
      shell_integration = "no-rc";
      confirm_os_window_close = 0;
      dynamic_background_opacity = true;
      enable_audio_bell = false;
      mouse_hide_wait = "-1.0";
      window_padding_width = 10;
      background_opacity = lib.mkForce "1.0";
      background_image = "wallpaper.png";
      startup_session = "startup.conf";
      background_image_layout = "cscaled";
      hide_window_decorations = "yes";
    };
  };
}

{ pkgs, ... }:
{
  # Global Kitty configuration
  environment.etc."kitty.conf".text = ''
    # BEGIN_KITTY_THEME
    # Catppuccin-Mocha
    include current-theme.conf
    # END_KITTY_THEME

    font_family      Fira Code
    bold_font        Fira Code bold
    italic_font      auto
    bold_italic_font Fira Code Bold

    font_size 18.0

    # Disable bell
    enable_audio_bell no

    # blur of transparency
    # tldr: This is not supported
    # background_blur 60

    # Allow kitty to be controlled remotely
    allow_remote_control yes

    # Listen on unix format
    # this is defined on startup.conf
    listen_on unix:@kitty

    # Config file for kitty sessions
    startup_session startup.conf

    # Set the background image to fill the window
    background_image_layout cscaled

    # Set some padding
    window_padding_width 10
  '';

  # Global Kitty startup configuration
  environment.etc."startup.conf".text = ''
    # startup.conf

    layout tall
  '';
}

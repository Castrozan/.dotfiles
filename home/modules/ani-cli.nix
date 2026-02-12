{
  pkgs,
  ...
}:
{
  home.packages = with pkgs; [
    ani-cli
    mpv
    mpv-handler
    mpvc
    mpv-shim-default-shaders
  ];

  # mpv configuration for ani-cli terminal video playback
  # ani-cli uses mpv to play videos. With vo=kitty and WezTerm's
  # enable_kitty_graphics=true, video frames display inline in terminal.
  home.file.".config/mpv/mpv.conf".text = ''
    vo=kitty
    video-sync=display-resample
    interpolation=no
    tscale=oversample
    ao=pulse
    hwdec=no
    cache=yes
    cache-secs=60
  '';
}

{
  pkgs,
  ...
}:
{
  home.packages = [ pkgs.ani-cli ];

  # mpv configuration for ani-cli terminal video playback
  # ani-cli uses mpv to play videos. With vo=kitty and WezTerm's
  # enable_kitty_graphics=true, video frames display inline in terminal.
  home.file.".config/mpv/mpv.conf".text = ''
    vo=kitty
    video-sync=display-resample
    interpolation=no
    tscale=oversample
    audio-device=auto
    hwdec=no
    cache=yes
    cache-secs=60
    vo-kitty-cols=80
    vo-kitty-rows=24
  '';
}

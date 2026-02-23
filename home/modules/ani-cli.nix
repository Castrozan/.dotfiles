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

  programs.fish.shellAliases = {
    ani-cli = "ani-cli --no-detach";
  };

  home.file.".config/mpv/mpv.conf".text = ''
    vo=kitty
    video-sync=display-resample
    display-fps-override=120
    interpolation=yes
    tscale=oversample
    ao=pulse
    hwdec=auto-safe
    cache=yes
    cache-secs=60
    audio-buffer=0.2
  '';
}

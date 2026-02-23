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
    interpolation=no
    tscale=oversample
    ao=pulse
    hwdec=no
    cache=yes
    cache-secs=60
  '';
}

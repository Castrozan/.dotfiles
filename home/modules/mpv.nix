_:
{
  # Configure mpv for WezTerm kitty graphics protocol
  # ani-cli uses mpv to play videos in the terminal
  # With enable_kitty_graphics=true in wezterm.lua and vo=kitty here,
  # video frames will be displayed inline in the terminal
  home.file.".config/mpv/mpv.conf".text = ''
    # Use kitty graphics protocol for terminal video display
    # This works with WezTerm's enable_kitty_graphics=true setting
    vo=kitty
    # Performance settings to prevent freezing
    # Reduce frame rate for terminal rendering to avoid overload
    video-sync=display-resample
    interpolation=no
    tscale=oversample
    # Audio settings
    audio-device=auto
    # Disable hardware acceleration for terminal output (can cause issues)
    hwdec=no
    # Prevent blocking with caching
    cache=yes
    cache-secs=60
    # Terminal-specific optimizations
    vo-kitty-cols=80
    vo-kitty-rows=24
  '';
}

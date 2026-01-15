{ pkgs, ... }:
let
  # Bad Apple YouTube URL
  badAppleUrl = "https://www.youtube.com/watch?v=FtutLA63Cp8";

  # Wrapper script that downloads video once, then plays in loop
  # tplay auto-scales to terminal size
  bad-apple-cmd = pkgs.writeShellScriptBin "bad-apple" ''
    CACHE_DIR="''${XDG_CACHE_HOME:-$HOME/.cache}/bad-apple"
    VIDEO_FILE="$CACHE_DIR/bad-apple.mp4"

    # Download video if not cached
    if [ ! -f "$VIDEO_FILE" ]; then
      mkdir -p "$CACHE_DIR"
      ${pkgs.yt-dlp}/bin/yt-dlp -f "bestvideo[height<=480]" -o "$VIDEO_FILE" "${badAppleUrl}" 2>/dev/null
    fi

    # Play in loop with grayscale, auto-scales to terminal
    exec ${pkgs.tplay}/bin/tplay -l -g "$VIDEO_FILE"
  '';
in
{
  home.packages = [
    pkgs.tplay
    bad-apple-cmd
  ];
}

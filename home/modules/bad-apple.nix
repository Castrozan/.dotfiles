{ pkgs, ... }:
let
  badAppleUrl = "https://www.youtube.com/watch?v=FtutLA63Cp8";

  # tplay wrapper with CPU optimizations:
  # -f 15: limit to 15fps (original is 30fps, halving reduces CPU ~50%)
  # -g: grayscale mode (less color processing)
  # -a: allow frame skip (drops frames if CPU can't keep up)
  # -c " .oO@": simple 5-char map (faster than default 10-char)
  # Video capped at 360p to reduce decode overhead
  bad-apple-cmd = pkgs.writeShellScriptBin "bad-apple" ''
    CACHE_DIR="''${XDG_CACHE_HOME:-$HOME/.cache}/bad-apple"
    VIDEO_FILE="$CACHE_DIR/bad-apple.mp4"

    if [ ! -f "$VIDEO_FILE" ]; then
      mkdir -p "$CACHE_DIR"
      ${pkgs.yt-dlp}/bin/yt-dlp -f "bestvideo[height<=360]" -o "$VIDEO_FILE" "${badAppleUrl}" 2>/dev/null
    fi

    # 6fps reduces CPU from ~300% to ~200% while auto-scaling to terminal
    exec ${pkgs.tplay}/bin/tplay -l -g -a -f 6 -c " .oO@" "$VIDEO_FILE"
  '';
in
{
  home.packages = [
    pkgs.tplay
    bad-apple-cmd
  ];
}

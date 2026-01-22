{ pkgs, ... }:
let
  badAppleUrl = "https://www.youtube.com/watch?v=FtutLA63Cp8";

  # Dependencies for frame generation
  deps = with pkgs; [
    yt-dlp
    ffmpeg
    chafa
    coreutils
  ];

  bad-apple-cmd = pkgs.writeShellScriptBin "bad-apple" ''
    export PATH="${pkgs.lib.makeBinPath deps}:$PATH"

    CACHE_BASE="''${XDG_CACHE_HOME:-$HOME/.cache}/bad-apple"
    VIDEO_FILE="$CACHE_BASE/video.mp4"

    # Get terminal size for cache key
    COLS=$(tput cols)
    LINES=$(tput lines)
    CACHE_DIR="$CACHE_BASE/frames-''${COLS}x''${LINES}"

    download_video() {
      echo "Downloading Bad Apple video..."
      mkdir -p "$CACHE_BASE"
      yt-dlp -f "bestvideo[height<=480]" -o "$VIDEO_FILE" "${badAppleUrl}"
    }

    generate_frames() {
      echo "Generating ASCII frames for ''${COLS}x''${LINES}..."
      mkdir -p "$CACHE_DIR"

      # Extract frames at 30fps
      TEMP_DIR=$(mktemp -d)
      ffmpeg -i "$VIDEO_FILE" -vf "fps=30" "$TEMP_DIR/frame_%04d.png" -hide_banner -loglevel error

      # Convert each frame to ASCII using chafa
      total=$(ls "$TEMP_DIR"/frame_*.png | wc -l)
      count=0
      for img in "$TEMP_DIR"/frame_*.png; do
        count=$((count + 1))
        base=$(basename "$img" .png)
        # chafa: no colors, block chars only
        chafa -f symbols -s "''${COLS}x''${LINES}" --symbols block -c none "$img" > "$CACHE_DIR/$base.txt"
        printf "\rConverting: %d/%d" "$count" "$total"
      done
      echo ""

      rm -rf "$TEMP_DIR"
      echo "Done! Frames cached at $CACHE_DIR"
    }

    # Check if we need to download/generate
    if [ ! -f "$VIDEO_FILE" ]; then
      download_video
    fi

    if [ ! -d "$CACHE_DIR" ] || [ -z "$(ls -A "$CACHE_DIR" 2>/dev/null)" ]; then
      generate_frames
    fi

    # Play cached frames
    while true; do
      for f in "$CACHE_DIR"/frame_*.txt; do
        printf '\033[H'
        cat "$f"
        sleep 0.033
      done
    done
  '';
in
{
  home.packages = [
    bad-apple-cmd
  ];
}

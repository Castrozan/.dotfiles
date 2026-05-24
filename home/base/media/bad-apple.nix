{ pkgs, latest, ... }:
let
  videoUrls = [
    "https://www.youtube.com/watch?v=FtutLA63Cp8"
    "https://www.youtube.com/watch?v=CqaAs_3azSs"
    "https://www.youtube.com/watch?v=lX44CAz-JhU"
    "https://www.youtube.com/watch?v=djV11Xbc914"
    "https://www.youtube.com/watch?v=OBk3ynRbtsw"
    "https://www.youtube.com/watch?v=I03xFqbxUp8"
  ];

  videoUrlsStr = builtins.concatStringsSep "\n" (map (url: "\"${url}\"") videoUrls);

  deps = with pkgs; [
    latest.yt-dlp
    ffmpeg
    chafa
    coreutils
    gawk
  ];

  bad-apple-cmd = pkgs.writeShellScriptBin "bad-apple" ''
    export PATH="${pkgs.lib.makeBinPath deps}:$PATH"

    VIDEO_URLS=(
    ${videoUrlsStr}
    )
    SELECTED_INDEX=$((RANDOM % ''${#VIDEO_URLS[@]}))
    SELECTED_URL="''${VIDEO_URLS[$SELECTED_INDEX]}"
    VIDEO_ID=$(echo "$SELECTED_URL" | gawk -F'[=&]' '{print $2}')

    CACHE_BASE="''${XDG_CACHE_HOME:-$HOME/.cache}/bad-apple/$VIDEO_ID"
    VIDEO_FILE="$CACHE_BASE/video.mp4"

    IS_WEZTERM=0
    if [ -n "''${WEZTERM_PANE:-}" ]; then
      IS_WEZTERM=1
    fi

    if [ -n "''${BAD_APPLE_FPS:-}" ]; then
      FPS="''${BAD_APPLE_FPS}"
    else
      if [ "''${IS_WEZTERM}" -eq 1 ]; then
        FPS=15
      else
        FPS=30
      fi
    fi

    COLS=$(tput cols)
    LINES=$(tput lines)

    if [ -n "''${BAD_APPLE_MAX_COLS:-}" ]; then
      MAX_COLS="''${BAD_APPLE_MAX_COLS}"
    else
      if [ "''${IS_WEZTERM}" -eq 1 ]; then
        MAX_COLS=140
      else
        MAX_COLS=0
      fi
    fi

    if [ -n "''${BAD_APPLE_MAX_LINES:-}" ]; then
      MAX_LINES="''${BAD_APPLE_MAX_LINES}"
    else
      if [ "''${IS_WEZTERM}" -eq 1 ]; then
        MAX_LINES=45
      else
        MAX_LINES=0
      fi
    fi

    RENDER_COLS="''${COLS}"
    RENDER_LINES="''${LINES}"

    if [ "''${MAX_COLS}" -gt 0 ] && [ "''${RENDER_COLS}" -gt "''${MAX_COLS}" ]; then
      RENDER_COLS="''${MAX_COLS}"
    fi
    if [ "''${MAX_LINES}" -gt 0 ] && [ "''${RENDER_LINES}" -gt "''${MAX_LINES}" ]; then
      RENDER_LINES="''${MAX_LINES}"
    fi

    CACHE_DIR="$CACHE_BASE/frames-''${RENDER_COLS}x''${RENDER_LINES}-fps''${FPS}-delta1-braille"

    download_video() {
      echo "Downloading video ($VIDEO_ID)..."
      mkdir -p "$CACHE_BASE"
      yt-dlp -f "bestvideo[height<=480]" -o "$VIDEO_FILE" "$SELECTED_URL" || \
        yt-dlp -f "18/best[height<=480]" -o "$VIDEO_FILE" "$SELECTED_URL"
    }

    generate_frames() {
      echo "Generating delta frames for ''${RENDER_COLS}x''${RENDER_LINES} at ''${FPS}fps..."
      mkdir -p "$CACHE_DIR"

      TEMP_DIR=$(mktemp -d)
      ffmpeg -i "$VIDEO_FILE" -vf "fps=''${FPS}" "$TEMP_DIR/frame_%04d.png" -hide_banner -loglevel error

      total=$(ls "$TEMP_DIR"/frame_*.png | wc -l)
      count=0
      prev_txt="$TEMP_DIR/prev.txt"
      curr_txt="$TEMP_DIR/curr.txt"
      first=1
      for img in "$TEMP_DIR"/frame_*.png; do
        count=$((count + 1))
        base=$(basename "$img" .png)
        chafa -f symbols -s "''${RENDER_COLS}x''${RENDER_LINES}" --symbols braille -c none "$img" > "$curr_txt"

        if [ "''${first}" -eq 1 ]; then
          { printf '\033[H'; cat "$curr_txt"; } > "$CACHE_DIR/$base.ansi"
          first=0
        else
          gawk -v lines="''${RENDER_LINES}" '
            NR==FNR { prev[NR]=$0; next }
            {
              if ($0 != prev[FNR]) {
                printf "\033[%d;1H%s\033[K", FNR, $0
              }
            }
            END {
              for (i=FNR+1; i<=lines; i++) {
                printf "\033[%d;1H\033[K", i
              }
            }
          ' "$prev_txt" "$curr_txt" > "$CACHE_DIR/$base.ansi"
        fi

        mv "$curr_txt" "$prev_txt"
        printf "\rConverting: %d/%d" "$count" "$total"
      done
      echo ""

      rm -rf "$TEMP_DIR"
      echo "Done! Frames cached at $CACHE_DIR"
    }

    if [ ! -f "$VIDEO_FILE" ]; then
      download_video
      if [ ! -f "$VIDEO_FILE" ]; then
        echo "Download failed. Exiting."
        exit 1
      fi
    fi

    if [ ! -d "$CACHE_DIR" ] || [ -z "$(ls -A "$CACHE_DIR" 2>/dev/null)" ]; then
      generate_frames
    fi

    SLEEP=$(gawk -v fps="''${FPS}" 'BEGIN { if (fps <= 0) fps=30; printf "%.6f", 1.0/fps }')
    printf '\033[?25l\033[H\033[2J'
    trap 'printf "\033[?25h\033[0m\033[H\033[2J"; exit' INT TERM
    while true; do
      for f in "$CACHE_DIR"/frame_*.ansi; do
        cat "$f"
        sleep "$SLEEP"
      done
    done
  '';
in
{
  home.packages = [
    bad-apple-cmd
  ];
}

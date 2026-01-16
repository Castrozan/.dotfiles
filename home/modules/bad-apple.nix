{ pkgs, ... }:
let
  # Pre-rendered ASCII frames from BadAppleBash (only ~2MB compressed)
  # Source: https://github.com/FelipeFMA/BadAppleBash
  badAppleFrames = pkgs.fetchFromGitHub {
    owner = "FelipeFMA";
    repo = "BadAppleBash";
    rev = "c400b0a";
    sha256 = "09psdnr6i22cv46zb9mwqqf7bqs4xh88c670fpq7ppmb8a564yv1";
  };

  # Lightweight player: just cat frames with sleep (~2-3% CPU vs 200% with tplay)
  bad-apple-cmd = pkgs.writeShellScriptBin "bad-apple" ''
    FRAMES_DIR="${badAppleFrames}/frames-ascii"
    AUDIO_FILE="${badAppleFrames}/bad_apple.mp3"

    play_audio() {
      if command -v mpv &>/dev/null; then
        mpv --no-video "$AUDIO_FILE" &>/dev/null &
        MPV_PID=$!
        trap "kill $MPV_PID 2>/dev/null" EXIT
      fi
    }

    play_audio

    while true; do
      for f in "$FRAMES_DIR"/out*.txt; do
        printf '\033[H'  # Move cursor to top-left (faster than clear)
        cat "$f"
        sleep 0.033  # ~30fps
      done
    done
  '';
in
{
  home.packages = [
    bad-apple-cmd
  ];
}

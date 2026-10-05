{ pkgs }:
if pkgs.stdenv.hostPlatform.isDarwin then
  pkgs.ffmpeg.overrideAttrs (previous: {
    postFixup = (previous.postFixup or "") + ''
      source ${pkgs.darwin.signingUtils}
      for artifact in "$bin/bin/ffmpeg" "$bin/bin/ffprobe" "$lib/lib/"*.dylib; do
        if [ -f "$artifact" ] && [ ! -L "$artifact" ]; then
          sign "$artifact"
        fi
      done
    '';
  })
else
  pkgs.ffmpeg

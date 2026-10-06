{ pkgs }:
let
  imagePackage = import ./image-package.nix { inherit pkgs; };
  speechPackage = import ./speech-package.nix { inherit pkgs; };
  ffmpegPackage = import ./video-ffmpeg-package.nix { inherit pkgs; };
in
pkgs.writeShellScriptBin "media-movie" ''
  export PYTHONDONTWRITEBYTECODE=1
  export MEDIA_IMAGE_COMMAND=${imagePackage}/bin/media-image
  export MEDIA_SPEECH_COMMAND=${speechPackage}/bin/media-speech
  export MEDIA_MOVIE_FFMPEG=${ffmpegPackage}/bin/ffmpeg
  export MEDIA_MOVIE_FFPROBE=${ffmpegPackage}/bin/ffprobe
  exec ${pkgs.python312}/bin/python3 ${./scripts}/media_movie_cli.py "$@"
''

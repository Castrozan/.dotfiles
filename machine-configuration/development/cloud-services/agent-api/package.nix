{ pkgs }:
let
  python = pkgs.python312.withPackages (import ./python-packages.nix);
  mediaDirectory = ../../../media/media-generation;
  ffmpeg = import (mediaDirectory + /video-ffmpeg-package.nix) { inherit pkgs; };
  image = import (mediaDirectory + /image-package.nix) { inherit pkgs; };
  movie = import (mediaDirectory + /movie-package.nix) { inherit pkgs; };
  speech = import (mediaDirectory + /speech-package.nix) { inherit pkgs; };
  video = import (mediaDirectory + /video-package.nix) { inherit pkgs; };
  runtime = pkgs.lib.makeBinPath [
    ffmpeg
    pkgs.whisper-cpp
    pkgs.pandoc
    image
    movie
    speech
    video
  ];
in
pkgs.writeShellScriptBin "agent-api" ''
  export PYTHONDONTWRITEBYTECODE=1
  export PATH="${runtime}:$PATH"
  exec ${python}/bin/python3 ${./scripts}/agent_api_cli.py "$@"
''

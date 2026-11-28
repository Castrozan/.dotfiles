{
  pkgs,
  computeInventoryFile ? null,
}:
let
  python = pkgs.python312.withPackages (import ./python-packages.nix);
  mediaDirectory = ../../../media/media-generation;
  ffmpeg = import (mediaDirectory + /video-ffmpeg-package.nix) { inherit pkgs; };
  image = import (mediaDirectory + /image-package.nix) { inherit pkgs; };
  movie = import (mediaDirectory + /movie-package.nix) { inherit pkgs; };
  speech = import (mediaDirectory + /speech-package.nix) { inherit pkgs; };
  video = import (mediaDirectory + /video-package.nix) { inherit pkgs; };
  job = import ./job-package.nix { inherit pkgs; };
  runtime = pkgs.lib.makeBinPath [
    job
    ffmpeg
    pkgs.whisper-cpp
    pkgs.pandoc
    image
    movie
    speech
    video
  ];
  inventoryExport = pkgs.lib.optionalString (
    computeInventoryFile != null
  ) ''export AGENT_API_COMPUTE_INVENTORY="${computeInventoryFile}"'';
in
pkgs.writeShellScriptBin "agent-api" ''
  export PYTHONDONTWRITEBYTECODE=1
  export PATH="${runtime}:$PATH"
  ${inventoryExport}
  exec ${python}/bin/python3 ${./scripts}/agent_api_cli.py "$@"
''

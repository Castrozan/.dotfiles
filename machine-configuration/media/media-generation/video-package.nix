{ pkgs }:
let
  videoFfmpeg = import ./video-ffmpeg-package.nix { inherit pkgs; };
in
pkgs.writeShellScriptBin "media-video" ''
  export PATH=${pkgs.lib.makeBinPath [ videoFfmpeg ]}:"$PATH"
  exec ${pkgs.python312}/bin/python3 ${./scripts}/media_video_cli.py "$@"
''

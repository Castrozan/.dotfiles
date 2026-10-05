{ pkgs }:
pkgs.writeShellScriptBin "media-video" ''
  export PATH=${pkgs.lib.makeBinPath [ pkgs.ffmpeg ]}:"$PATH"
  exec ${pkgs.python312}/bin/python3 ${./scripts}/media_video_cli.py "$@"
''

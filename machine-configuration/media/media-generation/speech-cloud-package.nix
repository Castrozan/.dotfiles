{ pkgs }:
let
  speechPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.elevenlabs ]);
in
pkgs.writeShellScriptBin "media-speech" ''
  exec ${speechPython}/bin/python3 ${./scripts}/media_speech_cli.py "$@"
''

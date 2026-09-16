{ pkgs }:
let
  python = pkgs.python312;
  virtualenvPath = "$HOME/.local/share/youtube-cli-venv";

  youtubeCliSources = ../scripts;

  youtubeCli = pkgs.writeShellScriptBin "youtube-cli" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        python
        pkgs.bash
      ]
    }:$PATH"
    export YOUTUBE_CLI_VIRTUALENV_PATH="${virtualenvPath}"
    export YOUTUBE_CLI_SCRIPT="${youtubeCliSources}/youtube-cli.py"
    export YOUTUBE_CLI_SETUP_SCRIPT="${youtubeCliSources}/youtube-cli-setup.sh"
    exec ${pkgs.bash}/bin/bash "${youtubeCliSources}/youtube-cli-entrypoint.sh" "$@"
  '';
in
{
  packages = [ youtubeCli ];
}

{ pkgs }:
let
  python = pkgs.python312;
  virtualenvPath = "$HOME/.local/share/youtube-cli-venv";

  youtubeCliSource = pkgs.writeText "youtube-cli.py" (builtins.readFile ../scripts/youtube-cli.py);

  youtubeCliSetupSource = pkgs.writeText "youtube-cli-setup.sh" (
    builtins.readFile ../scripts/youtube-cli-setup.sh
  );

  youtubeCliEntrypointSource = pkgs.writeText "youtube-cli-entrypoint.sh" (
    builtins.readFile ../scripts/youtube-cli-entrypoint.sh
  );

  youtubeCli = pkgs.writeShellScriptBin "youtube-cli" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        python
        pkgs.bash
      ]
    }:$PATH"
    export YOUTUBE_CLI_VIRTUALENV_PATH="${virtualenvPath}"
    export YOUTUBE_CLI_SCRIPT="${youtubeCliSource}"
    export YOUTUBE_CLI_SETUP_SCRIPT="${youtubeCliSetupSource}"
    exec ${pkgs.bash}/bin/bash "${youtubeCliEntrypointSource}" "$@"
  '';
in
{
  packages = [ youtubeCli ];
}

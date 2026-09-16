{
  pkgs,
  homeDir,
}:
let
  python = pkgs.python312;
  twikitVersion = "2.3.3";
  twikitVirtualenvPath = "${homeDir}/.local/share/twikit-venv";
  secretsDirectory = "${homeDir}/.secrets";
  twikitCookiesPath = "${homeDir}/.config/twikit/cookies.json";

  twitterScriptsDirectory = ../scripts;

  twikitCli = pkgs.writeShellScriptBin "twikit-cli" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        python
        pkgs.gnused
      ]
    }:$PATH"
    export TWIKIT_VERSION="${twikitVersion}"
    export TWIKIT_VIRTUALENV_PATH="${twikitVirtualenvPath}"
    export TWIKIT_COOKIES_PATH="${twikitCookiesPath}"
    export TWIKIT_SECRETS_DIRECTORY="${secretsDirectory}"
    export TWIKIT_SCRIPTS_DIRECTORY="${twitterScriptsDirectory}"
    exec ${pkgs.bash}/bin/bash "${twitterScriptsDirectory}/twikit-cli-entrypoint.sh" "$@"
  '';
in
{
  packages = [ twikitCli ];
}

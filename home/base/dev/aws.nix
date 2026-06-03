{
  pkgs,
  config,
  lib,
  ...
}:
let
  awsConfigSource = "${toString ../../../private-config}/aws/config";
  awsConfigSourceExists = builtins.pathExists awsConfigSource;

  awsConfigDestination = "${config.home.homeDirectory}/.aws/config";

  deployAwsConfigScript = pkgs.writeShellScript "deploy-aws-config" ''
    set -euo pipefail
    mkdir -p "$(dirname "${awsConfigDestination}")"
    cp -f "${awsConfigSource}" "${awsConfigDestination}"
    chmod 644 "${awsConfigDestination}"
  '';
in
{
  home.activation = lib.mkIf awsConfigSourceExists {
    deployAwsConfig = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      run ${deployAwsConfigScript}
    '';
  };
}

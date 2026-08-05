{
  pkgs,
  config,
  lib,
  ...
}:
let
  awsConfigSourcePath = ../../../private-config + "/aws/config";
  awsConfigSourceExists = builtins.pathExists awsConfigSourcePath;

  awsConfigSource = builtins.path {
    path = awsConfigSourcePath;
    name = "aws-config";
  };

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

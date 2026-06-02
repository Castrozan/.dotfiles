{
  pkgs,
  config,
  lib,
  ...
}:
# Deploys the betha AWS SSO profile config so `aws sso login --profile <name>`
# (the vt_prod / vt_test aliases in private-config/shell/aliases.sh) can resolve.
# The file lives in the private-config submodule because it carries betha account
# ids and the company SSO start url. It holds no credentials - real tokens are
# written by `aws sso login` into ~/.aws/sso/cache - so it needs no agenix.
# Copied (not symlinked) to keep private content out of the world-readable nix
# store and to leave ~/.aws writable for the aws cli, matching jira.nix.
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

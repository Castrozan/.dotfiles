{
  config,
  lib,
  pkgs,
  ...
}:
let
  githubTokenFile = "${config.home.homeDirectory}/.secrets/github-com-token";
  githubCredentialEnabled = (config.age.secrets or { }) ? "credentials/github-com-token";
in
{
  home.packages = [ pkgs.gh ];

  home.activation.setupGithubAuthentication = lib.mkIf githubCredentialEnabled {
    after = [
      "writeBoundary"
      "reloadSystemd"
      "disableAgenixLaunchdRestartLoop"
    ];
    before = [ ];
    data = ''
      ${pkgs.python312}/bin/python3 ${./scripts/deploy_github_authentication.py} ${pkgs.gh}/bin/gh ${lib.escapeShellArg githubTokenFile}
    '';
  };
}

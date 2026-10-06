{
  config,
  lib,
  pkgs,
  ...
}:
let
  githubTokenFile = "${config.home.homeDirectory}/.secrets/github-com-token";
  githubCredentialFile = "${config.xdg.configHome}/gh/hosts.yml";
  githubCredentialEnabled = (config.age.secrets or { }) ? "credentials/github-com-token";
  githubAuthenticationPython = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.pyyaml
  ]);
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
      ${githubAuthenticationPython}/bin/python3 ${./scripts/deploy_github_authentication.py} ${pkgs.gh}/bin/gh ${lib.escapeShellArg githubTokenFile} ${lib.escapeShellArg githubCredentialFile}
    '';
  };
}

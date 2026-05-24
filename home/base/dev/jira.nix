{
  pkgs,
  config,
  lib,
  ...
}:
let
  jiraConfigSource = ../../../private-config/machines/macbook-alpha/jira-config.yml;
  jiraConfigSourceExists = builtins.pathExists jiraConfigSource;

  jiraConfigDestination = "${config.home.homeDirectory}/.config/.jira/.config.yml";

  deployJiraConfigScript = pkgs.writeShellScript "deploy-jira-config" ''
    set -euo pipefail
    mkdir -p "$(dirname "${jiraConfigDestination}")"
    cp -f "${jiraConfigSource}" "${jiraConfigDestination}"
    chmod 600 "${jiraConfigDestination}"
  '';
in
{
  home.packages = [ pkgs.jira-cli-go ];

  home.activation = lib.mkIf jiraConfigSourceExists {
    deployJiraConfig = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      run ${deployJiraConfigScript}
    '';
  };
}

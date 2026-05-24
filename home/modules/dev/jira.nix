{ pkgs, config, ... }:
let
  jiraConfigSource = ./jira-config.yml;

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

  home.activation.deployJiraConfig = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    run ${deployJiraConfigScript}
  '';
}

{ config, ... }:
{
  home.activation.kickKarabinerUserAgentsEveryRebuild =
    config.lib.dag.entryAfter [ "setupLaunchAgents" ]
      ''
        for karabinerUserAgentLaunchdLabel in \
          org.pqrs.service.agent.Karabiner-Core-Service-rev2 \
          org.pqrs.service.agent.karabiner_session_monitor \
          org.pqrs.service.agent.karabiner_console_user_server; do
          /bin/launchctl kickstart -k "gui/$(/usr/bin/id -u)/$karabinerUserAgentLaunchdLabel" || true
        done
      '';
}

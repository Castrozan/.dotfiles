{ config, ... }:
{
  home.activation.kickKarabinerUserAgentsWhenConfigChanged =
    config.lib.dag.entryAfter
      [
        "setupLaunchAgents"
        "copyKarabinerRulesJsonToUserConfigDirectory"
      ]
      ''
        karabinerConfigChangedSentinelPath="$HOME/.local/state/karabiner-config-changed-since-last-kick"
        if [ -f "$karabinerConfigChangedSentinelPath" ]; then
          for karabinerUserAgentLaunchdLabel in \
            org.pqrs.service.agent.Karabiner-Core-Service-rev2 \
            org.pqrs.service.agent.Karabiner-Console-User-Server; do
            /bin/launchctl kickstart -k "gui/$(/usr/bin/id -u)/$karabinerUserAgentLaunchdLabel" || true
          done
          rm -f "$karabinerConfigChangedSentinelPath"
        fi
      '';
}

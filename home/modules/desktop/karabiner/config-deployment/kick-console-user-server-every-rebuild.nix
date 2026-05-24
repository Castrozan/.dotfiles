{ config, ... }:
{
  home.activation.kickKarabinerConsoleUserServerEveryRebuild =
    config.lib.dag.entryAfter [ "setupLaunchAgents" ]
      ''
        /bin/launchctl kickstart -k "gui/$(/usr/bin/id -u)/org.pqrs.service.agent.karabiner_console_user_server" || true
      '';
}

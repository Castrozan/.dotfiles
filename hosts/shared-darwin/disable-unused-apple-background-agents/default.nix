{
  lib,
  username,
  ...
}:
let
  guiDomainDisabledAppleAgentLabels = [
    "com.apple.rcd"
    "com.apple.AMPLibraryAgent"
    "com.apple.AMPArtworkAgent"
    "com.apple.AMPDeviceDiscoveryAgent"
    "com.apple.AMPDevicesAgent"
    "com.apple.AMPSystemPlayerAgent"
    "com.apple.mediaremoteagent"
    "com.apple.itunescloudd"
    "com.apple.photoanalysisd"
    "com.apple.photolibraryd"
    "com.apple.mediaanalysisd"
    "com.apple.suggestd"
    "com.apple.siriactionsd"
    "com.apple.bird"
    "com.apple.cloudd"
    "com.apple.commerce"
  ];

  systemDomainDisabledAppleDaemonLabels = [
    "com.apple.mediaremoted"
    "com.apple.cloudd"
  ];

  disableGuiDomainAgentCommands = lib.concatMapStringsSep "\n" (agentLabel: ''
    /bin/launchctl disable "gui/$appleBackgroundAgentOwnerUserId/${agentLabel}" || true
    /bin/launchctl bootout "gui/$appleBackgroundAgentOwnerUserId/${agentLabel}" 2>/dev/null || true
  '') guiDomainDisabledAppleAgentLabels;

  disableSystemDomainDaemonCommands = lib.concatMapStringsSep "\n" (daemonLabel: ''
    /bin/launchctl disable "system/${daemonLabel}" || true
    /bin/launchctl bootout "system/${daemonLabel}" 2>/dev/null || true
  '') systemDomainDisabledAppleDaemonLabels;
in
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    echo "disabling unused Apple background agents (Music/media, iCloud, Photos, App Store, Siri/Shortcuts)..." >&2
    appleBackgroundAgentOwnerUserId=$(/usr/bin/id -u ${lib.escapeShellArg username})
    ${disableGuiDomainAgentCommands}
    ${disableSystemDomainDaemonCommands}
  '';
}

{
  inputs,
  config,
  lib,
  pkgs,
  hostname,
  healthCheckLib,
  ...
}:
let
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  primaryIdentityKeyPath = "${config.home.homeDirectory}/.ssh/id_ed25519";
  identityKeyPaths = [ primaryIdentityKeyPath ];

  privateConfigRoot = ../../../private-config;
  privateMachineSecretsModulePath = "${toString privateConfigRoot}/machines/${hostname}/secrets.nix";
  privateMachineSecretsModuleExists = builtins.pathExists privateMachineSecretsModulePath;

  makeSecret = name: {
    file = ../../../secrets/${name}.age;
    path = "${secretsDirectory}/${builtins.baseNameOf name}";
  };

  secretsWithEnvironmentVariables = {
    "credentials/jira-api-token" = "JIRA_API_TOKEN";
    "credentials/glab-token" = "GITLAB_TOKEN";
  };

  secretsWithoutEnvironmentVariables = [
    "api-keys/brave-api-key"
    "api-keys/figma-personal-access-token"
    "api-keys/deepgram-api-key"
    "api-keys/gemini-api-key"
    "api-keys/nvidia-api-key"
    "api-keys/openai-api-key"
    "infrastructure/telegram-ids"
    "infrastructure/ssh-hosts"
    "credentials/x-username"
    "credentials/x-email"
    "credentials/x-password"
    "credentials/x-cookies"
    "bot-tokens/telegram-bot-token-jarvis"
    "bot-tokens/telegram-bot-token-golden"
    "bot-tokens/telegram-bot-token-clever"
    "bot-tokens/telegram-bot-token-robson"
    "bot-tokens/telegram-bot-token-jenny"
    "bot-tokens/telegram-bot-token-monster"
    "bot-tokens/telegram-bot-token-silver"
    "bot-tokens/discord-bot-token-jarvis"
    "bot-tokens/discord-bot-token-golden"
    "bot-tokens/discord-bot-token-clever"
    "bot-tokens/discord-bot-token-robson"
    "bot-tokens/discord-bot-token-jenny"
    "bot-tokens/discord-bot-token-monster"
    "bot-tokens/discord-bot-token-silver"
    "bot-tokens/discord-bot-token-claude"
    "discord-channels/discord-channels-monster"
    "credentials/obsidian-headless-auth-token"
    "credentials/obsidian-headless-sync-config"
    "infrastructure/gpg-private-key"
    "credentials/viu-auth"
    "credentials/home-assistant-token"
    "credentials/google-totp-secret"
    "credentials/gcp-usage-uploader-key"
  ];

  secretFileExists = name: builtins.pathExists (../../../secrets/${name}.age);

  allSecretNames = builtins.filter secretFileExists (
    (lib.attrNames secretsWithEnvironmentVariables) ++ secretsWithoutEnvironmentVariables
  );

  exportLines = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (
      secretName: envVariable:
      ''${envVariable}="$(cat ${secretsDirectory}/${builtins.baseNameOf secretName} 2>/dev/null)"''
    ) secretsWithEnvironmentVariables
  );

  allEnvironmentVariableNames = lib.attrValues secretsWithEnvironmentVariables;

  sourceSecretsScriptContent = ''
    #!/usr/bin/env bash
    ${exportLines}
    export ${lib.concatStringsSep " " allEnvironmentVariableNames}
  '';
in
{
  imports = [
    inputs.agenix.homeManagerModules.default
  ]
  ++ lib.optionals privateMachineSecretsModuleExists [
    privateMachineSecretsModulePath
  ];

  age = {
    identityPaths = identityKeyPaths;
    secrets = builtins.listToAttrs (
      map (name: {
        inherit name;
        value = makeSecret name;
      }) allSecretNames
    );
  };

  home.file.".secrets/source-secrets.sh" = {
    text = sourceSecretsScriptContent;
    executable = true;
  };

  healthCheck.probes = map (
    secretName:
    healthCheckLib.mkFileProbe {
      category = "secret";
      name = "agenix: ${secretName}";
      path = "${secretsDirectory}/${builtins.baseNameOf secretName}";
    }
  ) allSecretNames;

  # Upstream agenix-home-manager ships the activate-agenix launchd plist with
  # KeepAlive {Crashed: false, SuccessfulExit: false}. Both subkeys evaluate
  # to "kept alive" under launchd's dict semantics, so the mount script
  # reruns every throttle window (~10s) for the entire login session even
  # after a clean exit. Rewrite the plist to a single boolean KeepAlive: false
  # after home-manager's own setupLaunchAgents step writes it, then re-bootstrap
  # the agent so the new policy takes effect immediately.
  home.activation.disableAgenixLaunchdRestartLoop = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin (
    lib.hm.dag.entryAfter [ "setupLaunchAgents" ] ''
      plistPath="$HOME/Library/LaunchAgents/org.nix-community.home.activate-agenix.plist"
      if [ -f "$plistPath" ]; then
        $DRY_RUN_CMD /bin/chmod u+w "$plistPath"
        $DRY_RUN_CMD /usr/libexec/PlistBuddy -c "Delete :KeepAlive" "$plistPath" 2>/dev/null || true
        $DRY_RUN_CMD /usr/libexec/PlistBuddy -c "Add :KeepAlive bool false" "$plistPath"
        $DRY_RUN_CMD /bin/chmod 0444 "$plistPath"
        launchAgentDomain="gui/$(/usr/bin/id -u)"
        $DRY_RUN_CMD /bin/launchctl bootout "$launchAgentDomain/org.nix-community.home.activate-agenix" 2>/dev/null || true
        $DRY_RUN_CMD /bin/launchctl bootstrap "$launchAgentDomain" "$plistPath"
      fi
    ''
  );
}

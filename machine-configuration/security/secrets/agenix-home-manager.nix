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

  privateConfigRoot = ../../../private-configuration;
  privateMachineSecretsModulePath = "${toString privateConfigRoot}/machines/${hostname}/secrets.nix";
  privateMachineSecretsModuleExists = builtins.pathExists privateMachineSecretsModulePath;

  makeSecret = secret: {
    inherit (secret) file;
    path = "${secretsDirectory}/${builtins.baseNameOf secret.name}";
  };

  secretsWithEnvironmentVariables = {
    "credentials/jira-api-token" = "JIRA_API_TOKEN";
    "credentials/glab-token" = "GITLAB_TOKEN";
  };

  availableSecrets = builtins.filter (secret: builtins.pathExists secret.file) (
    import ./public-secret-sources.nix
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
    ./credentials-env-file-writer-home-manager.nix
  ]
  ++ lib.optionals privateMachineSecretsModuleExists [
    privateMachineSecretsModulePath
  ];

  age = {
    identityPaths = identityKeyPaths;
    secrets = builtins.listToAttrs (
      map (secret: {
        inherit (secret) name;
        value = makeSecret secret;
      }) availableSecrets
    );
  };

  home.file.".secrets/source-secrets.sh" = {
    text = sourceSecretsScriptContent;
    executable = true;
  };

  healthCheck.probes = map (
    secret:
    healthCheckLib.mkFileProbe {
      category = "secret";
      name = "agenix: ${secret.name}";
      path = "${secretsDirectory}/${builtins.baseNameOf secret.name}";
    }
  ) availableSecrets;

  # Upstream agenix-home-manager ships the activate-agenix launchd plist with
  # KeepAlive {Crashed: false, SuccessfulExit: false}. Both subkeys evaluate
  # to "kept alive" under launchd's dict semantics, so the mount script
  # reruns every throttle window (~10s) for the entire login session even
  # after a clean exit. Rewrite the plist to a single boolean KeepAlive: false
  # after home-manager's own setupLaunchAgents step writes it, then re-bootstrap
  # the agent so the new policy takes effect immediately.
  # A mount killed mid-run also leaves its half-written secret behind as a 0400
  # .tmp file, which age cannot reopen for writing, so every later mount dies on
  # that same secret and every secret after it silently never appears. The
  # generation the agenix symlink points at is the live one; anything else under
  # agenix.d is wreckage from such a run, and with the agent booted out nothing
  # is writing to it, so it goes before the agent comes back up.
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

        temporaryRoot="$(/usr/bin/getconf DARWIN_USER_TEMP_DIR)"
        liveGeneration="$(basename "$(readlink "$temporaryRoot/agenix" || echo none)")"
        for generation in "$temporaryRoot/agenix.d"/*; do
          if [ -d "$generation" ] && [ "$(basename "$generation")" != "$liveGeneration" ]; then
            $DRY_RUN_CMD /bin/chmod -R u+w "$generation" || true
            $DRY_RUN_CMD rm -rf "$generation" || true
          fi
        done

        $DRY_RUN_CMD /bin/launchctl bootstrap "$launchAgentDomain" "$plistPath"
      fi
    ''
  );
}

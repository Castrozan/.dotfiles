{
  pkgs,
  lib,
  interactivePreferencesFile,
}:
let
  profilePython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.tomli-w ]);

  interactiveProfile =
    name: instructionsFile: configurationOverrides:
    pkgs.runCommand "${name}.config.toml"
      {
        overridesFile = pkgs.writeText "${name}-overrides.json" (
          builtins.toJSON (lib.mapAttrs (_: toString) configurationOverrides)
        );
      }
      ''
        ${profilePython}/bin/python3 ${./scripts/generate_interactive_profile.py} \
          ${instructionsFile} "$overridesFile" "$out"
      '';

  workspaceProfileName = workspaceProfile: "dotfiles-workspace-${workspaceProfile.name}";

  developerInstructionsFile =
    workspaceProfile:
    pkgs.runCommand "codex-workspace-profile-${workspaceProfile.name}-developer-instructions.md" { } ''
      for fragment in ${interactivePreferencesFile} ${lib.escapeShellArgs (map toString workspaceProfile.instructionFiles)}; do
        cat "$fragment"
        printf '\n'
      done > "$out"
    '';

  hasCodexConfiguration =
    workspaceProfile:
    workspaceProfile.instructionFiles != [ ] || (workspaceProfile.codex.configOverrides or { }) != { };

  hookConfigurationArguments =
    workspaceProfile:
    lib.concatStringsSep " " (
      lib.mapAttrsToList (
        overrideKey: overrideValue: "-c ${lib.escapeShellArg "${overrideKey}=${toString overrideValue}"}"
      ) (workspaceProfile.codex.configOverrides or { })
    );
in
{
  profileFiles =
    workspaceProfiles:
    {
      ".codex/dotfiles-interactive.config.toml".source =
        interactiveProfile "dotfiles-interactive" interactivePreferencesFile
          { };
    }
    // builtins.listToAttrs (
      map (workspaceProfile: {
        name = ".codex/${workspaceProfileName workspaceProfile}.config.toml";
        value.source =
          interactiveProfile (workspaceProfileName workspaceProfile)
            (developerInstructionsFile workspaceProfile)
            (workspaceProfile.codex.configOverrides or { });
      }) (builtins.filter hasCodexConfiguration workspaceProfiles)
    );

  activationShellStatementsForProfile =
    workspaceProfile:
    lib.optionalString (hasCodexConfiguration workspaceProfile) ''
      codexDeveloperInstructionsFile=${developerInstructionsFile workspaceProfile}
      codexInteractiveProfile=${lib.escapeShellArg (workspaceProfileName workspaceProfile)}
      workspaceProfileArguments+=(${hookConfigurationArguments workspaceProfile})
    '';
}

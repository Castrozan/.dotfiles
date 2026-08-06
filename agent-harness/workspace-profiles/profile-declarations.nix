{ hostname }:
let
  perMachineDeclarationsPath =
    ../../private-configuration/machines + "/${hostname}/workspace-profiles.nix";

  perMachineDeclarations =
    if builtins.pathExists perMachineDeclarationsPath then import perMachineDeclarationsPath else [ ];

  withDefaultedSections = declaration: {
    inherit (declaration) name;
    directoryPrefixes = declaration.directoryPrefixes or [ ];
    gitRemotePatterns = declaration.gitRemotePatterns or [ ];
    instructionFiles = declaration.instructionFiles or [ ];
    claudeCode = declaration.claudeCode or { };
    codex = declaration.codex or { };
    opencode = declaration.opencode or { };
  };
in
map withDefaultedSections perMachineDeclarations

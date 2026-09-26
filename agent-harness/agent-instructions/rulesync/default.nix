{ pkgs }:
let
  rulesync = import ./package.nix { inherit pkgs; };
  coreInstructions = ../core-rules/core.md;
  sources = pkgs.linkFarm "rulesync-configuration-sources" [
    {
      name = "rules/core.md";
      path = pkgs.writeText "rulesync-core.md" ''
        ---
        root: true
        targets: [claudecode, codexcli, opencode, hermesagent]
        description: Shared agent instructions
        ---
        ${builtins.readFile coreInstructions}
      '';
    }
    {
      name = "subagents";
      path = ./sources/subagents;
    }
  ];
in
pkgs.runCommand "rulesync-agent-configuration"
  {
    nativeBuildInputs = [ pkgs.python312 ];
    passthru = { inherit sources; };
  }
  ''
    python3 ${./scripts/build_configuration.py} ${sources} "$out" \
      --rulesync ${rulesync}/bin/rulesync --core-instructions ${coreInstructions}
  ''

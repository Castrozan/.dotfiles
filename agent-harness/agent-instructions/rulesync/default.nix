{ pkgs }:
let
  rulesync = import ./package.nix { inherit pkgs; };
  coreInstructions = ../core-rules/core.md;
  coreSource = pkgs.writeText "rulesync-core.md" ''
    ---
    root: true
    targets: [claudecode, codexcli, opencode, hermesagent]
    description: Shared agent instructions
    ---
    ${builtins.readFile coreInstructions}
  '';
  sources = pkgs.runCommand "rulesync-configuration-sources" { } ''
    mkdir -p "$out/rules"
    cp ${coreSource} "$out/rules/core.md"
    cp -r ${./sources/subagents} "$out/subagents"
  '';

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

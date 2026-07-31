{
  lib,
  mkEvalCheck,
}:
let
  partitionFor =
    allMcpServerNames:
    import ../mcps/mcp-server-injection-partition.nix { inherit lib allMcpServerNames; };

  representativeInteractiveDefinitionNames = [
    "chrome-devtools"
    "codex"
    "mem0"
  ];

  partition = partitionFor representativeInteractiveDefinitionNames;
in
{
  a2a-stays-retired-so-the-dead-stdio-server-is-pruned =
    mkEvalCheck "a2a-stays-retired-so-the-dead-stdio-server-is-pruned"
      (
        builtins.elem "a2a" partition.retiredMcpServerNames
        && !(builtins.elem "a2a" partition.agentOnlyMcpServerNames)
      )
      "a2a is reached through the `a2a` command line tool, not an MCP, so it must stay retired: every host that once injected the stdio server still carries that entry in ~/.claude.json, and only the managed prune set removes it. Re-adding it as a definition also costs every agent its tool schemas at session start, which is what moving to a command line tool bought back";

  retired-mcps-remain-in-managed-prune-set =
    mkEvalCheck "retired-mcps-remain-in-managed-prune-set"
      (lib.all (retiredName: builtins.elem retiredName partition.managedMcpServerNames) [
        "a2a"
        "brave-devtools"
        "browser-use"
        "figma"
        "figma-read"
        "vivaldi-devtools"
      ])
      "brave-devtools, browser-use, figma, figma-read, and vivaldi-devtools must stay in the managed prune set so the injector strips any prior entry from existing ~/.claude.json on every host that previously injected them; dropping one leaves a dead stdio MCP that spawns a server that never connects";

  mem0-remains-in-managed-prune-set-on-hosts-without-it =
    mkEvalCheck "mem0-remains-in-managed-prune-set-on-hosts-without-it"
      (
        let
          partitionWithoutMem0 = partitionFor [
            "chrome-devtools"
            "codex"
          ];
        in
        builtins.elem "mem0" partitionWithoutMem0.managedMcpServerNames
      )
      "mem0 must stay in the managed prune set even on hosts whose mcpServerDefinitions omit it (no private mem0-host.nix), because mem0 is host-gated into the definitions; without the standalone hostGatedRemoteMemoryMcpServerNames entry a stale localhost mem0 sse entry written by a prior rebuild would never be pruned from ~/.claude.json and would persist as a dead server";
}

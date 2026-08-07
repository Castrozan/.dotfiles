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
        "mem0"
        "vivaldi-devtools"
      ])
      "brave-devtools, browser-use, figma, figma-read, mem0, and vivaldi-devtools must stay in the managed prune set so the injector strips any prior entry from existing ~/.claude.json on every host that previously injected them; dropping one leaves a dead MCP that spawns a server that never connects, and mem0 in particular was a remote sse entry that answers 503";
}

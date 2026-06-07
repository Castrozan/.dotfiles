{
  pkgs,
  config,
  lib,
}:
let
  inherit (config.home) username homeDirectory;

  homeDir = homeDirectory;
  secretsDirectory = "${homeDir}/.secrets";
  claudeBinary = lib.getExe config.claude.package;

  runtimeLocations = import ./runtime-locations.nix { inherit homeDir; };

  defaultTmuxSessionName = "clawde";
  agentWorkspacesBaseDirectory = runtimeLocations.runtimeRootDirectory;

  cfg = config.clawde;
  agentNames = builtins.attrNames cfg.agents;
  hasAgents = cfg.agents != { };

  clawdeRuntimePaths = import ./runtime-paths.nix {
    inherit
      pkgs
      lib
      username
      homeDir
      ;
  };

  clawdeRuntimeInstructions =
    builtins.readFile ./instructions/clawde-runtime.md
    + "\n"
    + builtins.readFile ../../../../agents/snippets/rebuild.md;

  a2aPeerHelpers = import ./peer-adapters/a2a/lib.nix { inherit pkgs lib; };

  getChannelAdapterFor = agent: cfg.channelAdapters.${agent.channel.type} or null;

  agentWorkspaceDirectory =
    name:
    let
      agent = cfg.agents.${name};
      adapter = getChannelAdapterFor agent;
      adapterWorkspace = if adapter != null then adapter.workspaceDirectoryFor agent else null;
    in
    if agent.workspaceDirectory != null then
      agent.workspaceDirectory
    else if adapterWorkspace != null then
      adapterWorkspace
    else
      "${agentWorkspacesBaseDirectory}/${name}";

  resolveChannelAdapterInstructions =
    agent:
    let
      adapter = getChannelAdapterFor agent;
    in
    if adapter != null then adapter.instructions else "";

  resolveChannelAdapterLaunchFlag =
    agent:
    let
      adapter = getChannelAdapterFor agent;
    in
    if adapter != null then adapter.launchFlags agent else "";

  resolveChannelAdapterEnvironmentSetter =
    agent:
    let
      adapter = getChannelAdapterFor agent;
    in
    if adapter != null then adapter.environmentSetterFor agent else "";

  resolveChannelAdapterTokenSecretFile =
    agent:
    if agent.channel.type == "discord" && agent.channel.discord.botTokenSecretName != null then
      "${secretsDirectory}/${agent.channel.discord.botTokenSecretName}"
    else
      null;

  resolveChannelAdapterTokenEnvironmentVariable =
    agent: if agent.channel.type == "discord" then "DISCORD_BOT_TOKEN" else null;

  agentWindowSpecHelpers = import ./agent-window-spec.nix {
    inherit
      pkgs
      lib
      cfg
      clawdeRuntimeInstructions
      a2aPeerHelpers
      agentWorkspaceDirectory
      resolveChannelAdapterInstructions
      resolveChannelAdapterLaunchFlag
      resolveChannelAdapterEnvironmentSetter
      ;
    inherit (runtimeLocations) agentInstructionsFile;
  };
  inherit (agentWindowSpecHelpers)
    buildAllSpecificationsForOneAgent
    buildAgentClaudeMarkdownContentByName
    ;

  distinctTmuxSessionNames = lib.unique (map (name: cfg.agents.${name}.tmuxSession) agentNames);

  agentNamesInTmuxSession =
    sessionName: builtins.filter (name: cfg.agents.${name}.tmuxSession == sessionName) agentNames;

  buildSessionSpecification = sessionName: {
    name = sessionName;
    agents = lib.concatMap buildAllSpecificationsForOneAgent (agentNamesInTmuxSession sessionName);
  };

  clawdeServiceSpecificationFile = pkgs.writeText "clawde-service-specification.json" (
    builtins.toJSON {
      sessions = map buildSessionSpecification distinctTmuxSessionNames;
    }
  );
in
{
  inherit
    homeDir
    secretsDirectory
    claudeBinary
    defaultTmuxSessionName
    distinctTmuxSessionNames
    agentWorkspacesBaseDirectory
    cfg
    agentNames
    hasAgents
    clawdeRuntimePaths
    agentWorkspaceDirectory
    resolveChannelAdapterTokenSecretFile
    resolveChannelAdapterTokenEnvironmentVariable
    clawdeServiceSpecificationFile
    buildAgentClaudeMarkdownContentByName
    runtimeLocations
    ;
}

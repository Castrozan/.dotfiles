{
  pkgs,
  config,
  lib,
}:
let
  inherit (config.home) username homeDirectory;

  homeDir = homeDirectory;
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

  getAgentTypeFor = agent: cfg.agentTypes.${agent.type} or null;

  firstNonNull = preferred: fallback: if preferred != null then preferred else fallback;

  agentWorkspaceDirectory =
    name:
    let
      agent = cfg.agents.${name};
      adapter = getChannelAdapterFor agent;
      agentType = getAgentTypeFor agent;
      typeWorkspace = if agentType != null then agentType.workspaceDirectoryFor agent else null;
      adapterWorkspace = if adapter != null then adapter.workspaceDirectoryFor agent else null;
    in
    if agent.workspaceDirectory != null then
      agent.workspaceDirectory
    else if typeWorkspace != null then
      typeWorkspace
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

  effectiveAgentByName =
    name:
    let
      agent = cfg.agents.${name};
      agentType = getAgentTypeFor agent;
      typeDefault = selector: if agentType != null then selector agentType else null;
      typeList = selector: if agentType != null then selector agentType else [ ];
      typePersonality = if agentType != null then agentType.personalityTemplateFor agent else null;
    in
    agent
    // {
      model = firstNonNull agent.model (firstNonNull (typeDefault (t: t.defaultModel)) "sonnet");
      permissionMode = firstNonNull agent.permissionMode (
        firstNonNull (typeDefault (t: t.defaultPermissionMode)) "default"
      );
      dailySessionRotation = firstNonNull agent.dailySessionRotation (
        firstNonNull (typeDefault (t: t.defaultDailySessionRotation)) false
      );
      personality = firstNonNull agent.personality typePersonality;
      heartbeatInterval = firstNonNull agent.heartbeatInterval (
        typeDefault (t: t.defaultHeartbeatInterval)
      );
      heartbeatPrompt = firstNonNull agent.heartbeatPrompt (typeDefault (t: t.defaultHeartbeatPrompt));
      heartbeatGateCommand = firstNonNull agent.heartbeatGateCommand (
        typeDefault (t: t.defaultHeartbeatGateCommand)
      );
      activeHoursStart = firstNonNull agent.activeHoursStart (typeDefault (t: t.defaultActiveHoursStart));
      activeHoursEnd = firstNonNull agent.activeHoursEnd (typeDefault (t: t.defaultActiveHoursEnd));
      denyToolPatterns = (typeList (t: t.defaultDenyToolPatterns)) ++ agent.denyToolPatterns;
      skillDirectories = agent.skillDirectories ++ (typeList (t: t.defaultSkillDirectories));
    };

  resolveAgentTypeInstructions =
    agent:
    let
      agentType = getAgentTypeFor agent;
    in
    if agentType != null then agentType.runtimeInstructions else "";

  agentWindowSpecHelpers = import ./agent-window-spec.nix {
    inherit
      pkgs
      lib
      effectiveAgentByName
      resolveAgentTypeInstructions
      clawdeRuntimeInstructions
      a2aPeerHelpers
      agentWorkspaceDirectory
      resolveChannelAdapterInstructions
      resolveChannelAdapterLaunchFlag
      resolveChannelAdapterEnvironmentSetter
      ;
    inherit (runtimeLocations) agentInstructionsFile agentLaunchConfigFile;
  };
  inherit (agentWindowSpecHelpers)
    buildAllSpecificationsForOneAgent
    buildAgentClaudeMarkdownContentByName
    buildAgentLaunchConfigByName
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
    claudeBinary
    defaultTmuxSessionName
    distinctTmuxSessionNames
    agentWorkspacesBaseDirectory
    cfg
    agentNames
    hasAgents
    clawdeRuntimePaths
    agentWorkspaceDirectory
    getChannelAdapterFor
    effectiveAgentByName
    clawdeServiceSpecificationFile
    buildAgentClaudeMarkdownContentByName
    buildAgentLaunchConfigByName
    runtimeLocations
    ;
}

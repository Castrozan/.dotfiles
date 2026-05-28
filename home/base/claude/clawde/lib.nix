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

  tmuxSessionName = "clawde";
  agentWorkspacesBaseDirectory = "${homeDir}/clawde";

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

  clawdeRuntimeInstructions = builtins.readFile ./instructions/clawde-runtime.md;

  a2aPeerHelpers = import ./peer-adapters/a2a/lib.nix { inherit pkgs lib tmuxSessionName; };

  agentChannelEnvDirectory = name: "${homeDir}/.claude/channels/discord/${name}";

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

  buildAgentClaudeMarkdownContent = name: agent: ''
    ${agent.personality}

    ${clawdeRuntimeInstructions}

    ${resolveChannelAdapterInstructions agent}

    ${a2aPeerHelpers.instructionsBlockForAgent agent}

    ${agent.additionalInstructions}
  '';

  buildAgentInstructionsFile =
    name: agent:
    pkgs.writeText "clawde-agent-${name}-instructions.md" (buildAgentClaudeMarkdownContent name agent);

  buildAgentLaunchCommand =
    name: agent:
    let
      workspace = agentWorkspaceDirectory name;
      environmentSetter = resolveChannelAdapterEnvironmentSetter agent;
      channelFlag = resolveChannelAdapterLaunchFlag agent;
      modelFlag = "--model ${agent.model}";
      nameFlag = "--name ${name}";
      permissionModeFlag = "--permission-mode ${agent.permissionMode}";
      skillDirFlags = lib.concatMapStringsSep " " (dir: "--add-dir ${dir}") agent.skillDirectories;
      appendSystemPromptFileFlag = "--append-system-prompt-file ${buildAgentInstructionsFile name agent}";
    in
    "cd ${workspace} && ${environmentSetter}${claudeBinary} ${channelFlag} ${modelFlag} ${nameFlag} ${permissionModeFlag} ${appendSystemPromptFileFlag} ${skillDirFlags}";

  buildHeartbeatBootstrapArgv = name: agent: [
    "${pkgs.python312}/bin/python3"
    "${./scripts/bootstrap-heartbeat.py}"
    "--session"
    tmuxSessionName
    "--window"
    name
    "--interval"
    agent.heartbeatInterval
    "--prompt"
    agent.heartbeatPrompt
  ];

  buildAgentWindowCommand =
    name: agent:
    let
      workspaceDirectory = agentWorkspaceDirectory name;
      heartbeatBootstrapArgvFlag =
        if agent.heartbeatInterval != null then
          "--heartbeat-bootstrap-argv ${lib.escapeShellArg (builtins.toJSON (buildHeartbeatBootstrapArgv name agent))}"
        else
          "";
      activeHoursFlags =
        if agent.activeHoursStart != null then
          "--active-hours-start ${toString agent.activeHoursStart} --active-hours-end ${toString agent.activeHoursEnd}"
        else
          "";
      dailySessionRotationFlag = if agent.dailySessionRotation then "--daily-session-rotation" else "";
      execPythonWrapperInvocation = lib.concatStringsSep " " [
        "exec"
        "${pkgs.python312}/bin/python3"
        "${./scripts/clawde-agent-wrapper.py}"
        "--agent-name ${lib.escapeShellArg name}"
        "--launch-command ${lib.escapeShellArg (buildAgentLaunchCommand name agent)}"
        heartbeatBootstrapArgvFlag
        activeHoursFlags
        dailySessionRotationFlag
      ];
    in
    pkgs.writeShellScript "clawde-agent-${name}" ''
      cd ${lib.escapeShellArg workspaceDirectory}
      ${execPythonWrapperInvocation}
    '';

  buildAgentSpecification = name: agent: {
    inherit name;
    wrapper_command = "exec ${buildAgentWindowCommand name agent}";
  };

  buildAllSpecificationsForOneAgent =
    name:
    let
      agent = cfg.agents.${name};
      mainSpec = buildAgentSpecification name agent;
      peerSpecs = a2aPeerHelpers.peerWindowSpecificationsForAgent name agent;
    in
    [ mainSpec ] ++ peerSpecs;

  clawdeServiceSpecificationFile = pkgs.writeText "clawde-service-specification.json" (
    builtins.toJSON {
      session_name = tmuxSessionName;
      agents = lib.concatMap buildAllSpecificationsForOneAgent agentNames;
    }
  );
in
{
  inherit
    homeDir
    secretsDirectory
    claudeBinary
    tmuxSessionName
    agentWorkspacesBaseDirectory
    cfg
    agentNames
    hasAgents
    clawdeRuntimePaths
    agentWorkspaceDirectory
    agentChannelEnvDirectory
    resolveChannelAdapterTokenSecretFile
    resolveChannelAdapterTokenEnvironmentVariable
    buildAgentClaudeMarkdownContent
    clawdeServiceSpecificationFile
    ;
}

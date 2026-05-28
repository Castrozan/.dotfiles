{
  pkgs,
  lib,
  cfg,
  claudeBinary,
  clawdeRuntimeInstructions,
  a2aPeerHelpers,
  agentWorkspaceDirectory,
  resolveChannelAdapterInstructions,
  resolveChannelAdapterLaunchFlag,
  resolveChannelAdapterEnvironmentSetter,
}:
let
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
    agent.tmuxSession
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
in
{
  inherit buildAllSpecificationsForOneAgent;
}

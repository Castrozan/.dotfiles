{
  pkgs,
  lib,
  effectiveAgentByName,
  clawdeRuntimeInstructions,
  a2aPeerHelpers,
  agentWorkspaceDirectory,
  agentInstructionsFile,
  agentLaunchConfigFile,
  resolveChannelAdapterInstructions,
  resolveChannelAdapterLaunchFlag,
  resolveChannelAdapterEnvironmentSetter,
}:
let
  claudeResolvedFromAgentRuntimePathForRebuildStability = "claude";

  buildAgentClaudeMarkdownContent = name: agent: ''
    ${agent.personality}

    ${clawdeRuntimeInstructions}

    ${resolveChannelAdapterInstructions agent}

    ${a2aPeerHelpers.instructionsBlockForAgent agent}

    ${agent.additionalInstructions}
  '';

  buildAgentClaudeMarkdownContentByName =
    name: buildAgentClaudeMarkdownContent name (effectiveAgentByName name);

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
      appendSystemPromptFlag = "--append-system-prompt \"$(cat ${agentInstructionsFile name})\"";
    in
    "cd ${workspace} && ${environmentSetter}${claudeResolvedFromAgentRuntimePathForRebuildStability} \${CLAWDE_RESUME_FLAG:-} ${channelFlag} ${modelFlag} ${nameFlag} ${permissionModeFlag} ${appendSystemPromptFlag} ${skillDirFlags}";

  buildHeartbeatDriverArgv =
    name: agent:
    [
      "${pkgs.python312}/bin/python3"
      "${./scripts/heartbeat}/driver.py"
      "--session"
      agent.tmuxSession
      "--window"
      name
      "--interval"
      agent.heartbeatInterval
      "--prompt"
      agent.heartbeatPrompt
    ]
    ++ lib.optionals (agent.heartbeatGateCommand != null) [
      "--gate-command"
      agent.heartbeatGateCommand
    ];

  buildAgentLaunchConfig = name: agent: {
    launch_command = buildAgentLaunchCommand name agent;
    heartbeat_driver_argv =
      if agent.heartbeatInterval != null then buildHeartbeatDriverArgv name agent else null;
    active_hours_start = agent.activeHoursStart;
    active_hours_end = agent.activeHoursEnd;
    daily_session_rotation = agent.dailySessionRotation;
    tmux_session = agent.tmuxSession;
  };

  buildAgentLaunchConfigByName = name: buildAgentLaunchConfig name (effectiveAgentByName name);

  buildAgentWindowCommand =
    name: _agent:
    let
      workspaceDirectory = agentWorkspaceDirectory name;
      execPythonWrapperInvocation = lib.concatStringsSep " " [
        "exec"
        "${pkgs.python312}/bin/python3"
        "${./scripts/agent-wrapper}/wrapper.py"
        "--agent-name ${lib.escapeShellArg name}"
        "--config-file ${lib.escapeShellArg (agentLaunchConfigFile name)}"
      ];
    in
    pkgs.writeShellScript "clawde-agent-${name}" ''
      mkdir -p ${lib.escapeShellArg workspaceDirectory}
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
      agent = effectiveAgentByName name;
      mainSpec = buildAgentSpecification name agent;
      peerSpecs = a2aPeerHelpers.peerWindowSpecificationsForAgent name agent;
    in
    [ mainSpec ] ++ peerSpecs;
in
{
  inherit
    buildAllSpecificationsForOneAgent
    buildAgentClaudeMarkdownContentByName
    buildAgentLaunchConfigByName
    ;
}

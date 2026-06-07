{
  pkgs,
  lib,
  cfg,
  clawdeRuntimeInstructions,
  a2aPeerHelpers,
  agentWorkspaceDirectory,
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
      appendSystemPromptFlag = "--append-system-prompt \"$(cat ${buildAgentInstructionsFile name agent})\"";
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

  buildAgentWindowCommand =
    name: agent:
    let
      workspaceDirectory = agentWorkspaceDirectory name;
      heartbeatDriverArgvFlag =
        if agent.heartbeatInterval != null then
          "--heartbeat-driver-argv ${lib.escapeShellArg (builtins.toJSON (buildHeartbeatDriverArgv name agent))}"
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
        "${./scripts/agent-wrapper}/wrapper.py"
        "--agent-name ${lib.escapeShellArg name}"
        "--tmux-session ${lib.escapeShellArg agent.tmuxSession}"
        "--launch-command ${lib.escapeShellArg (buildAgentLaunchCommand name agent)}"
        heartbeatDriverArgvFlag
        activeHoursFlags
        dailySessionRotationFlag
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
      agent = cfg.agents.${name};
      mainSpec = buildAgentSpecification name agent;
      peerSpecs = a2aPeerHelpers.peerWindowSpecificationsForAgent name agent;
    in
    [ mainSpec ] ++ peerSpecs;
in
{
  inherit buildAllSpecificationsForOneAgent;
}

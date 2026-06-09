{ config, lib }:
agentSubmoduleArguments:
let
  typeDefinition = config.clawde.agentTypes.${agentSubmoduleArguments.config.type} or null;
  resolvedPersonality =
    if typeDefinition == null then
      null
    else
      typeDefinition.personalityTemplateFor agentSubmoduleArguments.config;
in
lib.mkIf (typeDefinition != null) (
  lib.mkMerge [
    (lib.optionalAttrs (typeDefinition.defaultModel != null) {
      model = lib.mkDefault typeDefinition.defaultModel;
    })
    (lib.optionalAttrs (typeDefinition.defaultPermissionMode != null) {
      permissionMode = lib.mkDefault typeDefinition.defaultPermissionMode;
    })
    (lib.optionalAttrs (typeDefinition.defaultHeartbeatInterval != null) {
      heartbeatInterval = lib.mkDefault typeDefinition.defaultHeartbeatInterval;
    })
    (lib.optionalAttrs (typeDefinition.defaultHeartbeatPrompt != null) {
      heartbeatPrompt = lib.mkDefault typeDefinition.defaultHeartbeatPrompt;
    })
    (lib.optionalAttrs (typeDefinition.defaultHeartbeatGateCommand != null) {
      heartbeatGateCommand = lib.mkDefault typeDefinition.defaultHeartbeatGateCommand;
    })
    (lib.optionalAttrs (typeDefinition.defaultActiveHoursStart != null) {
      activeHoursStart = lib.mkDefault typeDefinition.defaultActiveHoursStart;
    })
    (lib.optionalAttrs (typeDefinition.defaultActiveHoursEnd != null) {
      activeHoursEnd = lib.mkDefault typeDefinition.defaultActiveHoursEnd;
    })
    (lib.optionalAttrs (typeDefinition.defaultDailySessionRotation != null) {
      dailySessionRotation = lib.mkDefault typeDefinition.defaultDailySessionRotation;
    })
    { denyToolPatterns = typeDefinition.defaultDenyToolPatterns; }
    { skillDirectories = typeDefinition.defaultSkillDirectories; }
    (lib.optionalAttrs (resolvedPersonality != null) {
      personality = lib.mkDefault resolvedPersonality;
    })
  ]
)

{
  config,
  lib,
  pkgs,
  ...
}:
let
  helpers = import ./lib.nix { inherit pkgs config lib; };
in
{
  config = lib.mkIf helpers.hasAgents {
    assertions =
      let
        knownChannelTypes = [ "none" ] ++ builtins.attrNames helpers.cfg.channelAdapters;
        knownAgentTypes = builtins.attrNames helpers.cfg.agentTypes;
        assertionsForAgent =
          name:
          let
            agent = helpers.cfg.agents.${name};
            typeDefinition = helpers.cfg.agentTypes.${agent.type} or null;
            missingRequiredParams =
              if typeDefinition == null then
                [ ]
              else
                builtins.filter (
                  param: (agent.typeParams.${agent.type}.${param} or null) == null
                ) typeDefinition.requiredParams;
          in
          [
            {
              assertion = (agent.activeHoursStart == null) == (agent.activeHoursEnd == null);
              message = "Agent ${name}: activeHoursStart and activeHoursEnd must both be set or both be null.";
            }
            {
              assertion = builtins.elem agent.channel.type knownChannelTypes;
              message = "Agent ${name}: channel.type must be one of ${lib.concatStringsSep ", " knownChannelTypes} (got '${agent.channel.type}').";
            }
            {
              assertion = builtins.elem agent.type knownAgentTypes;
              message = "Agent ${name}: type must be one of ${lib.concatStringsSep ", " knownAgentTypes} (got '${agent.type}').";
            }
            {
              assertion = missingRequiredParams == [ ];
              message = "Agent ${name}: type '${agent.type}' requires typeParams.${agent.type} fields ${lib.concatStringsSep ", " missingRequiredParams} to be set and non-null.";
            }
          ];
      in
      lib.concatMap assertionsForAgent helpers.agentNames;
  };
}

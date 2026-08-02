{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  listHookScriptsRecursively =
    import ../../../home/base/agent-hooks/list-hook-scripts-recursively.nix
      {
        inherit lib;
      };

  hooksEventDefinition = import ../event-to-dispatcher-map.nix;

  flatDeployedHookScriptNames = map (entry: entry.flatDeploymentFilename) (
    listHookScriptsRecursively ../../../agents/hooks
  );

  deployedDispatcherScriptNames = lib.filter (
    scriptName: lib.hasSuffix "-dispatcher.py" scriptName
  ) flatDeployedHookScriptNames;

  dispatcherScriptNamesReferencedByTheEventMap = lib.attrValues hooksEventDefinition.dispatchersByEvent;

  dispatchersReferencedByTheMapButNotDeployed = lib.filter (
    scriptName: !(lib.elem scriptName flatDeployedHookScriptNames)
  ) dispatcherScriptNamesReferencedByTheEventMap;

  deployedDispatchersNotClaimedByAnyEvent = lib.filter (
    scriptName: !(lib.elem scriptName dispatcherScriptNamesReferencedByTheEventMap)
  ) deployedDispatcherScriptNames;

  eventMapKeysSorted = lib.sort (a: b: a < b) (lib.attrNames hooksEventDefinition.dispatchersByEvent);
in
{
  hooks-every-event-maps-to-a-flat-deployed-dispatcher =
    mkEvalCheck "hooks-every-event-maps-to-a-flat-deployed-dispatcher"
      (dispatchersReferencedByTheMapButNotDeployed == [ ])
      (
        "every event in agents/hooks/event-to-dispatcher-map.nix must map to a -dispatcher.py that "
        + "exists in the flat deploy of agents/hooks; a map referencing a missing script ships a "
        + "registration that fails at runtime with no build error. Dispatchers referenced but not "
        + "deployed: "
        + lib.concatStringsSep ", " dispatchersReferencedByTheMapButNotDeployed
      );

  hooks-every-flat-deployed-dispatcher-is-claimed-by-an-event =
    mkEvalCheck "hooks-every-flat-deployed-dispatcher-is-claimed-by-an-event"
      (deployedDispatchersNotClaimedByAnyEvent == [ ])
      (
        "every -dispatcher.py flat-deployed from agents/hooks must be claimed by at least one event "
        + "in agents/hooks/event-to-dispatcher-map.nix; an unclaimed dispatcher never runs, so "
        + "handlers folded into it are silently dead and no harness test can catch it. Unclaimed "
        + "dispatchers: "
        + lib.concatStringsSep ", " deployedDispatchersNotClaimedByAnyEvent
      );

  hooks-the-event-map-covers-every-hook-option =
    mkEvalCheck "hooks-the-event-map-covers-every-hook-option"
      (
        eventMapKeysSorted == [
          "PostToolUse"
          "PreToolUse"
          "SessionStart"
          "Stop"
          "SubagentStop"
          "UserPromptSubmit"
        ]
      )
      (
        "agents/hooks/event-to-dispatcher-map.nix is the single definition of which hook option each "
        + "harness registers; dropping an event from the map silently unregisters that hook option on "
        + "every harness that imports it. Event map keys must be exactly the hook options Claude and "
        + "Codex support. Current keys: "
        + lib.concatStringsSep ", " eventMapKeysSorted
      );
}

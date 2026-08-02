{
  lib,
  mkEvalCheck,
  cfg,
}:
let
  hooksEventDefinition = import ../../../../agents/hooks/event-to-dispatcher-map.nix;

  deployedSettings = builtins.fromJSON cfg.home.file.".claude/settings.json.nix-source".text;

  deployedHookEvents = lib.attrNames (deployedSettings.hooks or { });

  deployedCommandsForEvent =
    event:
    lib.concatMap (matcherGroup: map (hook: hook.command) (matcherGroup.hooks or [ ])) (
      deployedSettings.hooks.${event} or [ ]
    );

  expectedDeployedEvents =
    lib.attrNames hooksEventDefinition.dispatchersByEvent ++ hooksEventDefinition.inlineExceptionEvents;

  deployedEventsNotDeclaredInTheCanonicalMap = lib.filter (
    event: !(lib.elem event expectedDeployedEvents)
  ) deployedHookEvents;

  canonicalEventsMissingFromTheDeploy = lib.filter (
    event: !(lib.elem event deployedHookEvents)
  ) expectedDeployedEvents;

  eventsWhoseDeployedCommandDivergesFromTheCanonicalDispatcher = lib.filter (
    event:
    let
      dispatcher = hooksEventDefinition.dispatchersByEvent.${event};
      commands = deployedCommandsForEvent event;
    in
    !(
      lib.length commands == 1
      && lib.hasInfix "run-hook.sh" (lib.head commands)
      && lib.hasInfix dispatcher (lib.head commands)
    )
  ) (lib.attrNames hooksEventDefinition.dispatchersByEvent);

  inlineExceptionEventsWithDivergingCommandCount = lib.filter (
    event: lib.length (deployedCommandsForEvent event) != 1
  ) hooksEventDefinition.inlineExceptionEvents;
in
{
  hooks-deployed-events-match-the-canonical-event-map =
    mkEvalCheck "hooks-deployed-events-match-the-canonical-event-map"
      (deployedEventsNotDeclaredInTheCanonicalMap == [ ] && canonicalEventsMissingFromTheDeploy == [ ])
      (
        "the deployed settings.json must register exactly the events declared in "
        + "agents/hooks/event-to-dispatcher-map.nix (plus the inline exception events); a hook option "
        + "registered here but not in the map is a hand-written harness hook, the half-merged shape "
        + "the single-dispatcher refactor removed, and a map event missing from the deploy is a "
        + "silently dropped registration. Events deployed but not declared: "
        + lib.concatStringsSep ", " deployedEventsNotDeclaredInTheCanonicalMap
        + ". Events declared but not deployed: "
        + lib.concatStringsSep ", " canonicalEventsMissingFromTheDeploy
      );

  hooks-every-deployed-command-runs-its-canonical-dispatcher =
    mkEvalCheck "hooks-every-deployed-command-runs-its-canonical-dispatcher"
      (
        eventsWhoseDeployedCommandDivergesFromTheCanonicalDispatcher == [ ]
        && inlineExceptionEventsWithDivergingCommandCount == [ ]
      )
      (
        "each event's deployed registration must be exactly one command running the canonical "
        + "dispatcher from agents/hooks/event-to-dispatcher-map.nix through run-hook.sh, with no "
        + "standalone command beside or instead of it; events violating that: "
        + lib.concatStringsSep ", " eventsWhoseDeployedCommandDivergesFromTheCanonicalDispatcher
        + ". Inline exception events must also register exactly one command: "
        + lib.concatStringsSep ", " inlineExceptionEventsWithDivergingCommandCount
      );
}

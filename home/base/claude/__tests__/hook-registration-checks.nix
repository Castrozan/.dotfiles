{
  lib,
  mkEvalCheck,
  cfg,
}:
let
  deployedSettings = builtins.fromJSON cfg.home.file.".claude/settings.json.nix-source".text;

  deployedHookCommandsForEvent =
    event:
    lib.concatMap (matcherGroup: map (hook: hook.command) (matcherGroup.hooks or [ ])) (
      deployedSettings.hooks.${event} or [ ]
    );
  deployedEventRunsStopDispatcher =
    event:
    lib.any (command: lib.hasInfix "stop-dispatcher.py" command) (deployedHookCommandsForEvent event);

  deployedPreToolUseMatcherGroupsWithMatcher =
    matcher:
    lib.filter (matcherGroup: (matcherGroup.matcher or "") == matcher) (
      deployedSettings.hooks.PreToolUse or [ ]
    );
  codexSandboxDowngradeGuardRegisteredOnCodexLaunch = lib.any (
    matcherGroup:
    lib.any (hook: lib.hasInfix "codex-sandbox-downgrade-guard.py" (hook.command or "")) (
      matcherGroup.hooks or [ ]
    )
  ) (deployedPreToolUseMatcherGroupsWithMatcher "mcp__codex__codex");
in
{
  hooks-stop-dispatcher-registered-on-stop =
    mkEvalCheck "hooks-stop-dispatcher-registered-on-stop" (deployedEventRunsStopDispatcher "Stop")
      "the deployed settings must register stop-dispatcher.py on the Stop event; it composes lint-turn-review and end-of-turn-format-guard, and test_stop_dispatcher_composition guards that the lint handler stays in it";

  hooks-stop-dispatcher-registered-on-subagent-stop =
    mkEvalCheck "hooks-stop-dispatcher-registered-on-subagent-stop"
      (deployedEventRunsStopDispatcher "SubagentStop")
      "the deployed settings must register stop-dispatcher.py on the SubagentStop event so subagent turns get the same lint review; guards event-registrations.nix against dropping the SubagentStop registration";

  hooks-codex-sandbox-downgrade-guard-registered-on-codex-launch =
    mkEvalCheck "hooks-codex-sandbox-downgrade-guard-registered-on-codex-launch"
      codexSandboxDowngradeGuardRegisteredOnCodexLaunch
      "the deployed settings must register codex-sandbox-downgrade-guard.py on a PreToolUse matcher group whose matcher is exactly mcp__codex__codex, so a dropped or mistyped registration cannot silently let a Claude session launch Codex with a weakened sandbox or approval policy";
}

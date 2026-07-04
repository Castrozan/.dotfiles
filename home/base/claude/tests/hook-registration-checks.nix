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
  deployedEventRunsLintTurnReview =
    event:
    lib.any (command: lib.hasInfix "lint-turn-review.py" command) (deployedHookCommandsForEvent event);

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
  hooks-lint-turn-review-registered-on-stop =
    mkEvalCheck "hooks-lint-turn-review-registered-on-stop" (deployedEventRunsLintTurnReview "Stop")
      "the deployed settings must register lint-turn-review.py on the Stop event so end-of-turn lint review fires";

  hooks-lint-turn-review-registered-on-subagent-stop =
    mkEvalCheck "hooks-lint-turn-review-registered-on-subagent-stop"
      (deployedEventRunsLintTurnReview "SubagentStop")
      "the deployed settings must register lint-turn-review.py on the SubagentStop event so subagent turns get the same lint review; guards event-registrations.nix against dropping the SubagentStop registration";

  hooks-codex-sandbox-downgrade-guard-registered-on-codex-launch =
    mkEvalCheck "hooks-codex-sandbox-downgrade-guard-registered-on-codex-launch"
      codexSandboxDowngradeGuardRegisteredOnCodexLaunch
      "the deployed settings must register codex-sandbox-downgrade-guard.py on a PreToolUse matcher group whose matcher is exactly mcp__codex__codex, so a dropped or mistyped registration cannot silently let a Claude session launch Codex with a weakened sandbox or approval policy";
}

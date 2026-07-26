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

  deployedPreToolUseRunsDispatcher = lib.any (
    command: lib.hasInfix "pre-tool-use-dispatcher.py" command
  ) (deployedHookCommandsForEvent "PreToolUse");
in
{
  hooks-stop-dispatcher-registered-on-stop =
    mkEvalCheck "hooks-stop-dispatcher-registered-on-stop" (deployedEventRunsStopDispatcher "Stop")
      "the deployed settings must register stop-dispatcher.py on the Stop event; it composes lint-turn-review and end-of-turn-format-guard, and test_stop_dispatcher_composition guards that the lint handler stays in it";

  hooks-stop-dispatcher-registered-on-subagent-stop =
    mkEvalCheck "hooks-stop-dispatcher-registered-on-subagent-stop"
      (deployedEventRunsStopDispatcher "SubagentStop")
      "the deployed settings must register stop-dispatcher.py on the SubagentStop event so subagent turns get the same lint review; guards event-registrations.nix against dropping the SubagentStop registration";

  hooks-pre-tool-use-dispatcher-registered-on-pre-tool-use =
    mkEvalCheck "hooks-pre-tool-use-dispatcher-registered-on-pre-tool-use"
      deployedPreToolUseRunsDispatcher
      "the deployed settings must register pre-tool-use-dispatcher.py on the PreToolUse event (env-prefixed with the per-host PROHIBITED_WORDS_ALLOWED allowlist); it composes memory-recall, prohibited-command-guard, prohibited-words-guard, and the tool-specific guards including codex-sandbox-downgrade-guard, and test_pre_tool_use_dispatcher_composition guards that the codex-sandbox-downgrade handler stays in PRE_TOOL_USE_HANDLERS with tool_matcher mcp__codex__codex so a Claude session cannot silently launch Codex with a weakened sandbox or approval policy";
}

{
  lib,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };
  inherit (fixtures)
    supervisedWindowNames
    sidecarProcessesOfAgent
    sidecarProcessNamesOfAgent
    sidecarProcessMatchPatternsOfAgent
    ;
in
{
  clawde-a-bridge-sidecar-stays-findable-across-its-own-upgrades =
    mkEvalCheck "clawde-a-bridge-sidecar-stays-findable-across-its-own-upgrades"
      (
        !(builtins.any (pattern: lib.hasInfix "/nix/store/" pattern) (
          sidecarProcessMatchPatternsOfAgent "agent-on-discord-via-codex"
        ))
      )
      "this pattern is the only way the supervisor recognises a bridge it already started, so pinning it to the bridge script's store path makes every edit to that script invisible to the reconcile loop: the bridge from the previous generation is never culled, two discord clients end up holding the same bot token, and the agent answers everything twice";

  clawde-discord-on-codex-gets-a-bridge-sidecar-process =
    mkEvalCheck "clawde-discord-on-codex-gets-a-bridge-sidecar-process"
      (
        sidecarProcessNamesOfAgent "agent-on-discord-via-codex" == [
          "agent-on-discord-via-codex-discord"
        ]
      )
      "codex has no --channels flag and no plugin providing an inbound channel transport, so a discord agent on it only ever receives a message through the sidecar bridge process; drop that process and the agent looks deployed while nothing can reach it";

  clawde-discord-on-claude-gets-no-enabled-bridge-sidecar-process =
    mkEvalCheck "clawde-discord-on-claude-gets-no-enabled-bridge-sidecar-process"
      (
        builtins.filter (sidecar: sidecar.enabled or true) (sidecarProcessesOfAgent "agent-on-discord")
        == [ ]
      )
      "claude carries discord inside its own process through the official plugin, so enabling a bridge sidecar beside it would put two clients on one bot token and double every reply";

  clawde-a-bridge-sidecar-never-takes-a-window-of-its-own =
    mkEvalCheck "clawde-a-bridge-sidecar-never-takes-a-window-of-its-own"
      (!(builtins.elem "agent-on-discord-via-codex-discord" supervisedWindowNames))
      "a bridge is plumbing, not something a human opens, so the supervisor runs it headless and logs it to a file: give it a window and every bridged agent shows up twice in the multiplexer, the human cannot tell which of the two is the agent, and the window-reconcile loop retypes the bridge command into a busy pane on every poll because no agent wrapper is running in it";

  clawde-every-supervised-window-is-an-agent-a-human-can-open =
    mkEvalCheck "clawde-every-supervised-window-is-an-agent-a-human-can-open"
      (
        builtins.sort (a: b: a < b) supervisedWindowNames == [
          "agent-on-claude"
          "agent-on-codex"
          "agent-on-discord"
          "agent-on-discord-via-codex"
        ]
      )
      "one window per declared agent and nothing else is what makes the multiplexer a usable entrypoint: any extra supervised window is machinery leaking into the human's tab bar";
}

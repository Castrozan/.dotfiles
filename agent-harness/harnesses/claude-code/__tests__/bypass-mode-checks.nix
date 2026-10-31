{
  pkgs,
  lib,
  mkEvalCheck,
  cfg,
}:
{
  claude-bypass-mode-forced-at-launch = pkgs.runCommand "claude-bypass-mode-forced-at-launch" { } ''
    grep -q -- '--dangerously-skip-permissions' ${cfg.claude.package}/bin/claude
    touch "$out"
  '';

  claude-mode-cycle-key-unbound =
    let
      chatBindings =
        lib.findFirst (contextBindings: contextBindings.context == "Chat")
          (throw "Chat keybindings missing")
          (builtins.fromJSON cfg.home.file.".claude/keybindings.json".text).bindings;
    in
    mkEvalCheck "claude-mode-cycle-key-unbound" (
      chatBindings.bindings ? "shift+tab" && chatBindings.bindings."shift+tab" == null
    ) "shift+tab must stay unbound so one keypress cannot drop a session out of bypass mode";
}

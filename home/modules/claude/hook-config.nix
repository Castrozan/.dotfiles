let
  hooksPath = "~/.claude/hooks";
  runHook = "${hooksPath}/run-hook.sh";

  # Keywords that trigger delegation-reminder.py
  delegationMatcher =
    "(?i)("
    + builtins.concatStringsSep "|" [
      "rebuild"
      "nixos"
      "home-manager"
      "flake"
      "devenv"
      "agents?/"
      "SKILL\\.md"
      "create.*agent"
      "design.*agent"
      "write.*skill"
      "Ralph"
      "PRD"
      "dotfiles?"
      "add.*module"
      "create.*module"
      "nix.*(expression|syntax|eval|repl|build)"
      "how.*nix"
    ]
    + ")";
in
{
  SessionStart = [
    {
      matcher = ".*";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/session-context.py";
          timeout = 5000;
        }
      ];
    }
  ];

  PreToolUse = [
    {
      matcher = "Bash";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/dangerous-command-guard.py";
          timeout = 3000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/branch-protection.py";
          timeout = 5000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/rebuild-notify.py";
          timeout = 3000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/tmux-reminder.py";
          timeout = 3000;
        }
      ];
    }
  ];

  PostToolUse = [
    {
      matcher = "Edit|Write";
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/auto-format.py";
          timeout = 15000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/lint-on-edit.py";
          timeout = 30000;
        }
        {
          type = "command";
          command = "${runHook} ${hooksPath}/nix-rebuild-trigger.py";
          timeout = 3000;
        }
      ];
    }
  ];

  UserPromptSubmit = [
    {
      matcher = delegationMatcher;
      hooks = [
        {
          type = "command";
          command = "${runHook} ${hooksPath}/delegation-reminder.py";
          timeout = 3000;
        }
      ];
    }
  ];
}

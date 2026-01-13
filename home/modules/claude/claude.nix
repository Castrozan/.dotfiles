{
  pkgs,
  ...
}:
let
  claudeSettings = {
    model = "opus";
    spinnerTipsEnabled = false;
    dangerouslySkipPermissions = true;
    permissions = {
      defaultMode = "bypassPermissions";
      allow = [ "*" ];
      deny = [ ];
    };
    terminalShowHoverHint = false;
    composer = {
      shouldChimeAfterChatFinishes = true;
    };
    agent = {
      permissionMode = "allow-all";
      disallowedTools = [ ];
    };
  };

  userRules = ''
    ---
    description: Core agent guidelines migrated from Cursor.
    alwaysApply: true
    ---

    Do not change this file if not requested or if the change does not follow the pattern that focuses on token usage and information density. These are user rules that must be followed without exception. Follow this at all costs.

    Commands
    Use timeouts for commands.

    Git
    Use git to check logs before and commit changes for rollback. Follow my commit messages pattern.

    Workflow
    Search codebase before coding. Read relevant files first. Test changes and check linter errors.

    Files
    Before writing code, check if the file contents where changed, user changed code should be taken into consideration.

    Time
    Check current date, time and location before searches and when referencing software versions or documentation.

    Prompts
    Understand prompts contextually. User prompts may contain errors. Interpret intent and correct obvious mistakes when understanding requests.

    Questions
    User is a senior software engineer. When stuck or unsure, ask the user instead of assuming. User can help diagnose issues and understands context well.

    Parallel Agents
    Only use this when mentioned. Use parallel agents with Git worktrees for independent tasks. Each agent operates in isolated worktree. Use for: independent features, approach comparison, split concerns. User can request parallel agents by mentioning "parallel agents" in the prompt. Each agent should be able to work independently on different tasks defined by the user. As a agent you should look for a file following the pattern agent-<1,2,3...>.md in the root of the project. If the file does not exist, you should create it sequentially with the next number that way you know what task you are working on. After knowing your task, delete the file you created.

    Code Style
    No obvious comments. Code should be self-documenting. Keep comments only for "why", not "what". Prefer concise, direct code. Follow existing patterns.

    Iteration
    Don't ask for permission unless ambiguous or dangerous. When user asks "is this right?", explain briefly and fix if needed. Prefer implementing over explaining. Show code, not descriptions. Test changes before presenting.

    Documentation
    Keep docs short and concise. No excessive formatting. Plain markdown is fine.

    Error Handling
    If build fails, fix immediately. Don't just report. Verify builds pass before marking complete when possible.

    Communication
    Be direct and technical. Answer questions concisely. No long explanations. If user is wrong or going on a wrong direction tell.

    Key principle: Implement first, explain if needed. User prefers seeing code over descriptions.
  '';

  nixosRules = ''
    ---
    description: NixOS dotfiles repository specific AI guidelines
    alwaysApply: true
    ---

    Do not change this file if not requested or if the change does not follow the pattern that focuses on token usage and information density. Follow these rules at all costs. These are repository-specific patterns that must be followed without exception.

    NixOS Patterns
    Use conditional configs with lib.mkIf for optional features. Check file existence with builtins.pathExists before including secrets. Import modules from nixos/modules/ following existing structure.

    Agenix Secrets
    Keep secrets in secrets/ directory encrypted with agenix. Each .age file gets entry in secrets.nix mapping to public keys that can decrypt. Use conditional configs to allow rebuilds without secret files so we don't break the system rebuild. Edit secrets with agenix-edit script. Public keys in secrets.nix are safe to commit. Private keys stay on machine only.

    File Organization
    Scripts in bin/ for executables. Home Manager scripts in home/scripts/. NixOS modules in nixos/modules/. User configs in users/<username>/. Secrets in secrets/ with secrets.nix defining access. Follow existing import patterns.

    Scripts
    Raw scripts go in bin/. Create <name>.nix in home/scripts/ or users/<username>/scripts/ following pattern in respective default.nix. Scripts requiring root use sudo wrapper or check EUID in script.

    Common Tasks
    Rebuild with ./bin/rebuild. Edit secrets with agenix-edit <secret-name>. Always check config with nix flake check --impure. Add new module by creating in appropriate directory and importing in user config.
  '';
in
{
  home.file.".claude/.keep".text = "";
  home.file.".claude/settings.json".text = builtins.toJSON claudeSettings;
  home.file.".claude/rules/user-rules.md".text = userRules;
  home.file.".claude/rules/nixos-rules.md".text = nixosRules;

  home.sessionVariables = {
    CLAUDE_CODE_SHELL = "${pkgs.bash}/bin/bash";
    CLAUDE_BASH_NO_LOGIN = "1";
    BASH_DEFAULT_TIMEOUT_MS = "120000";
    BASH_MAX_TIMEOUT_MS = "600000";
    CLAUDE_DANGEROUSLY_DISABLE_SANDBOX = "true";
    CLAUDE_SKIP_PERMISSIONS = "true";
  };
}

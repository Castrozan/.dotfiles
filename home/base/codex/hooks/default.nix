{ pkgs, ... }:
let
  sharedHooksDirectory = ../../../../agents/hooks;

  codexPostToolUseHookScripts = pkgs.runCommandLocal "codex-post-tool-use-hooks" { } ''
    mkdir -p "$out"
    install -m 0644 ${sharedHooksDirectory}/common/changed_file_paths.py "$out/changed_file_paths.py"
    install -m 0644 ${sharedHooksDirectory}/post-tool-use/formatter_table_by_extension.py "$out/formatter_table_by_extension.py"
    install -m 0644 ${sharedHooksDirectory}/post-tool-use/auto-format.py "$out/auto-format.py"
    install -m 0644 ${sharedHooksDirectory}/post-tool-use/nix-rebuild-trigger.py "$out/nix-rebuild-trigger.py"
  '';

  runCodexPostToolUseHookScript =
    scriptFilename: "${pkgs.python3}/bin/python3 ${codexPostToolUseHookScripts}/${scriptFilename}";

  codexHooksConfiguration = {
    hooks = {
      SessionStart = [
        {
          matcher = "startup|resume|clear|compact";
          hooks = [
            {
              type = "command";
              command = "cat ~/.dotfiles/.deep-work/*/context.md 2>/dev/null || true";
              timeout = 5;
              statusMessage = "Loading deep-work context";
            }
          ];
        }
      ];
      PostToolUse = [
        {
          matcher = ".*";
          hooks = [
            {
              type = "command";
              command = runCodexPostToolUseHookScript "auto-format.py";
              timeout = 15;
            }
            {
              type = "command";
              command = runCodexPostToolUseHookScript "nix-rebuild-trigger.py";
              timeout = 5;
            }
          ];
        }
      ];
    };
  };
in
{
  home.file.".codex/hooks.json".text = builtins.toJSON codexHooksConfiguration;
}

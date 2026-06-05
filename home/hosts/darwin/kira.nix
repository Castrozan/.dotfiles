{ ... }:
{
  imports = [
    ../../darwin

    ../../base/dev/git-toggle-user.nix
    ../../base/claude/agents/jojo-clawde-agents.nix

    ../../base/opencode
    ../../base/opencode/private.nix

    ../../base/browser/firefox.nix

    ../../base/editor/jetbrains-idea.nix
    ../../base/editor/scripts.nix
    ../../base/editor/zed-editor.nix

    ../../base/dev/aws.nix
    ../../base/dev/google-workspace-cli.nix
    ../../base/dev/mcporter.nix
    ../../base/dev/ralph-tui.nix
    ../../base/dev/tuisvn.nix
  ];
}

{ pkgs, ... }:
let
  codexWeb = pkgs.writeShellScriptBin "codex-web" ''
    exec ${pkgs.xdg-utils}/bin/xdg-open "https://chatgpt.com/codex"
  '';
in
{
  home.packages = [ codexWeb ];

  # Linux doesn't currently ship a native "Codex App" binary the way macOS does.
  # This provides an app-like launcher that opens the official Codex web UI.
  xdg.desktopEntries.codex-web = {
    name = "OpenAI Codex (Web)";
    comment = "Open Codex in your browser";
    exec = "${codexWeb}/bin/codex-web";
    terminal = false;
    categories = [
      "Development"
      "IDE"
    ];
  };

  # Quick launcher for the Codex TUI (our Nix-managed wrapper).
  xdg.desktopEntries.codex-cli = {
    name = "OpenAI Codex (CLI)";
    comment = "Start Codex in the terminal";
    exec = "codex";
    terminal = true;
    categories = [
      "Development"
      "IDE"
    ];
  };
}


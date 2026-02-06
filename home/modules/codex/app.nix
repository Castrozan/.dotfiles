{ pkgs, ... }:
let
  codexWeb = pkgs.writeShellScriptBin "codex-web" ''
    exec ${pkgs.xdg-utils}/bin/xdg-open "https://chatgpt.com/codex"
  '';

  # Convenience alias (people expect "app" semantics).
  codexApp = pkgs.writeShellScriptBin "codex-app" ''
    exec ${codexWeb}/bin/codex-web
  '';

  codexWebDesktop = pkgs.writeText "codex-web.desktop" ''
    [Desktop Entry]
    Type=Application
    Name=OpenAI Codex (Web)
    Comment=Open Codex in your browser
    Exec=${codexWeb}/bin/codex-web
    Terminal=false
    Categories=Development;IDE;
  '';

  codexCliDesktop = pkgs.writeText "codex-cli.desktop" ''
    [Desktop Entry]
    Type=Application
    Name=OpenAI Codex (CLI)
    Comment=Start Codex in the terminal
    Exec=codex
    Terminal=true
    Categories=Development;IDE;
  '';
in
{
  home.packages = [
    codexWeb
    codexApp
  ];

  # Linux doesn't currently ship a native "Codex App" binary the way macOS does.
  # This provides an app-like launcher that opens the official Codex web UI.
  home.file.".local/share/applications/codex-web.desktop".source = codexWebDesktop;
  home.file.".local/share/applications/codex-cli.desktop".source = codexCliDesktop;
}

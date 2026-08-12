{
  pkgs,
  lib,
  config,
  ...
}:
let
  claudePluginPortGenerator = pkgs.runCommand "codex-claude-plugin-porter" { } ''
    mkdir -p "$out"
    cp ${./claude-plugin-port}/*.py "$out"/
    cp ${../claude-code/plugin-discovery}/*.py "$out"/
  '';
  codexBinary = "${config.home.homeDirectory}/.local/bin/codex";
in
{
  home.activation.codexClaudePluginPort =
    lib.hm.dag.entryAfter
      [
        "writeBoundary"
        "seedCodexConfigAsMutableFile"
      ]
      ''
        CODEX_BIN=${lib.escapeShellArg codexBinary} \
        ${pkgs.python312}/bin/python3 ${claudePluginPortGenerator}/port_claude_plugins_to_codex.py || true
      '';
}

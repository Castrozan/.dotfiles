{
  pkgs,
  lib,
  config,
  ...
}:
let
  claudePluginPortGenerator = ./claude-plugin-port;
  codexBinary = "${config.home.homeDirectory}/.local/bin/codex";
  privatePrunedConfigSubstrings = import ./private-pruned-config-substrings.nix { inherit lib; };
  prunedConfigSubstringsJson = builtins.toJSON privatePrunedConfigSubstrings;
in
{
  home.activation.codexClaudePluginPort =
    lib.hm.dag.entryAfter
      [
        "writeBoundary"
        "codexBaselineConfig"
      ]
      ''
        CODEX_BIN=${lib.escapeShellArg codexBinary} \
        CODEX_PRUNED_CONFIG_SUBSTRINGS_JSON=${lib.escapeShellArg prunedConfigSubstringsJson} \
        ${pkgs.python3}/bin/python3 ${claudePluginPortGenerator}/port_claude_plugins_to_codex.py || true
      '';
}

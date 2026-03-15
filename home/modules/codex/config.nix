{
  pkgs,
  lib,
  config,
  ...
}:
let
  patchScript = ./patch.py;
  codexDefaultModel = "gpt-5.4";
  codexDeveloperInstructions = "Operate pragmatically: keep diffs small, verify with fast checks, and prefer repo-local truth (AGENTS.md, bin/, home/modules/). Use profiles: fast (default), deep, web.";
  chromeDevtoolsMcpCommand = "${config.home.homeDirectory}/.local/share/chrome-devtools-mcp-npm/bin/chrome-devtools-mcp";
  scraplingFetchMcpCommand = "${config.home.homeDirectory}/.local/bin/scrapling-mcp";

  codexHooksConfig = builtins.toJSON {
    SessionStart = [
      {
        command = "cat ~/.dotfiles/.deep-work/*/context.md 2>/dev/null || true";
        timeout = 5000;
      }
    ];
  };

  codexHooksJsonFile = pkgs.writeText "codex-hooks.json" codexHooksConfig;
in
{
  home.activation.codexBaselineConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    CODEX_DEFAULT_MODEL=${lib.escapeShellArg codexDefaultModel} \
    CODEX_DEVELOPER_INSTRUCTIONS=${lib.escapeShellArg codexDeveloperInstructions} \
    CODEX_CHROME_DEVTOOLS_MCP_COMMAND=${lib.escapeShellArg chromeDevtoolsMcpCommand} \
    CODEX_CHROME_USER_DATA_DIR="${config.home.homeDirectory}/.config/google-chrome" \
    CODEX_SCRAPLING_FETCH_MCP_COMMAND=${lib.escapeShellArg scraplingFetchMcpCommand} \
    ${pkgs.python3}/bin/python3 ${patchScript}
  '';

  home.activation.codexHooksConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.codex"
    cp ${codexHooksJsonFile} "$HOME/.codex/hooks.json"
    chmod 644 "$HOME/.codex/hooks.json"
  '';
}

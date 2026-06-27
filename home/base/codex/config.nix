{
  pkgs,
  lib,
  config,
  latest,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  homeDir = config.home.homeDirectory;
  browserMcp = import ../../../agents/skills/browser/install {
    inherit pkgs nodejs homeDir;
    chromePackage = latest.google-chrome;
  };
  codexConfigGenerator = ./config-generator;
  codexDefaultModel = "gpt-5.5";
  codexDeveloperInstructions = "Operate pragmatically: keep diffs small, verify with fast checks, and prefer repo-local truth (AGENTS.md, bin/, home/{base,linux,darwin}/). Use profiles: fast (default), deep, web.";
  inherit (browserMcp) chromeDevtoolsMcpStdioCommand;
  chromeDevtoolsMcpStdioArgsJson = builtins.toJSON browserMcp.chromeDevtoolsMcpStdioArgs;
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
    CODEX_CHROME_DEVTOOLS_MCP_COMMAND=${lib.escapeShellArg chromeDevtoolsMcpStdioCommand} \
    CODEX_CHROME_DEVTOOLS_MCP_ARGS_JSON=${lib.escapeShellArg chromeDevtoolsMcpStdioArgsJson} \
    ${pkgs.python3}/bin/python3 ${codexConfigGenerator}/generate_config.py
  '';

  home.activation.codexHooksConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.codex"
    cp ${codexHooksJsonFile} "$HOME/.codex/hooks.json"
    chmod 644 "$HOME/.codex/hooks.json"
  '';
}

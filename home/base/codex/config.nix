{
  pkgs,
  lib,
  config,
  latest,
  hostname,
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
  codexDefaultModel = "gpt-5.6-sol";
  codexDeveloperInstructions = "Operate pragmatically: keep diffs small, verify with fast checks, and prefer repo-local truth (AGENTS.md, bin/, home/{base,linux,darwin}/). Use profiles: fast (default), deep, web.";
  inherit (browserMcp)
    chromeDevtoolsMcpStdioCommand
    ;
  includeVivaldiDevtoolsMcp = hostname == "chise";
  vivaldiDevtoolsMcpStdioCommand =
    if includeVivaldiDevtoolsMcp then browserMcp.vivaldiDevtoolsMcpStdioCommand else "";
  chromeDevtoolsMcpStdioArgsJson = builtins.toJSON browserMcp.chromeDevtoolsMcpStdioArgs;
  vivaldiDevtoolsMcpStdioArgsJson = builtins.toJSON (
    if includeVivaldiDevtoolsMcp then browserMcp.vivaldiDevtoolsMcpStdioArgs else [ ]
  );
in
{
  home.activation.codexBaselineConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    CODEX_DEFAULT_MODEL=${lib.escapeShellArg codexDefaultModel} \
    CODEX_DEVELOPER_INSTRUCTIONS=${lib.escapeShellArg codexDeveloperInstructions} \
    CODEX_CHROME_DEVTOOLS_MCP_COMMAND=${lib.escapeShellArg chromeDevtoolsMcpStdioCommand} \
    CODEX_CHROME_DEVTOOLS_MCP_ARGS_JSON=${lib.escapeShellArg chromeDevtoolsMcpStdioArgsJson} \
    CODEX_VIVALDI_DEVTOOLS_MCP_COMMAND=${lib.escapeShellArg vivaldiDevtoolsMcpStdioCommand} \
    CODEX_VIVALDI_DEVTOOLS_MCP_ARGS_JSON=${lib.escapeShellArg vivaldiDevtoolsMcpStdioArgsJson} \
    ${pkgs.python3}/bin/python3 ${codexConfigGenerator}/generate_config.py
  '';
}

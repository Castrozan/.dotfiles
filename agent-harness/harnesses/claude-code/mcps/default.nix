{
  pkgs,
  config,
  lib,
  latest,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  homeDir = config.home.homeDirectory;

  browserMcp = import ../../../../agent-harness/agent-instructions/skills/browser/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
    chromePackage = latest.google-chrome;
  };

  mcpServerDefinitions = {
    chrome-devtools = {
      command = browserMcp.chromeDevtoolsMcpStdioCommand;
      args = browserMcp.chromeDevtoolsMcpStdioArgs;
    };
    codex = {
      command = "${homeDir}/.local/bin/codex";
      args = [
        "mcp-server"
        "-c"
        "approval_policy=never"
        "-c"
        "sandbox_mode=danger-full-access"
      ];
    };
  };

  mcpServerInjectionPartition = import ./mcp-server-injection-partition.nix {
    inherit lib;
    allMcpServerNames = builtins.attrNames mcpServerDefinitions;
  };

  interactivelyInjectedMcpServerDefinitions = removeAttrs mcpServerDefinitions mcpServerInjectionPartition.agentOnlyMcpServerNames;

  selectClawdeAgentMcpServers = serverNames: lib.getAttrs serverNames mcpServerDefinitions;

in
{
  imports = [
    ./chrome-devtools-mcp-runaway-watchdog.nix
    (import ./inject-mcp-servers-into-claude-config.nix {
      inherit homeDir;
      inherit (mcpServerInjectionPartition) managedMcpServerNames;
      mcpServerDefinitions = interactivelyInjectedMcpServerDefinitions;
    })
  ];

  _module.args.selectClawdeAgentMcpServers = selectClawdeAgentMcpServers;

  home = {
    inherit (browserMcp) packages;

    activation.enforcePinchtabFullAccessConfig = lib.hm.dag.entryAfter [
      "writeBoundary"
    ] browserMcp.enforcePinchtabConfigActivation;
  };
}

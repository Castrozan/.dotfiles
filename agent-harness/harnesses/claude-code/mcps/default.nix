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

  browserMcp = import ../../../agent-instructions/skills/workstation/browser/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
    chromePackage = latest.google-chrome;
  };

  mcpServerDefinitions =
    (import ../../../agent-instructions/production-plugin/mcp-servers.nix {
      inherit pkgs;
      homeDirectory = homeDir;
      chromePackage = latest.google-chrome;
    })
    // {
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

  interactivelyInjectedMcpServerDefinitions = { };

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

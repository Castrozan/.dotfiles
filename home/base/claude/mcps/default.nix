{
  pkgs,
  config,
  lib,
  latest,
  hostname,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  homeDir = config.home.homeDirectory;

  browserMcp = import ../../../../agents/skills/browser/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
    chromePackage = latest.google-chrome;
  };

  a2aMcp = import ../../agents/a2a/install.nix {
    inherit
      pkgs
      nodejs
      homeDir
      ;
  };

  mem0Mcp = import ./mem0/wrapper.nix {
    inherit lib hostname;
    privateConfigRoot = ../../../../private-config;
    defaultUserId = "lucas";
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
    a2a = {
      command = a2aMcp.mcpServerCommand;
      args = a2aMcp.mcpServerArgs;
    };
  }
  // lib.optionalAttrs mem0Mcp.remoteConfigured {
    mem0 = mem0Mcp.serverConfig;
  }
  // lib.optionalAttrs (hostname == "chise") {
    vivaldi-devtools = {
      command = browserMcp.vivaldiDevtoolsMcpStdioCommand;
      args = browserMcp.vivaldiDevtoolsMcpStdioArgs;
    };
  };

  mcpServerInjectionPartition = import ./mcp-server-injection-partition.nix {
    inherit lib;
    allMcpServerNames = builtins.attrNames mcpServerDefinitions;
  };

  interactivelyInjectedMcpServerDefinitions = removeAttrs mcpServerDefinitions mcpServerInjectionPartition.agentOnlyMcpServerNames;

  buildClawdeAgentMcpConfigFile =
    agentName: serverNames:
    "${pkgs.writeText "clawde-agent-mcp-config-${agentName}.json" (
      builtins.toJSON { mcpServers = lib.getAttrs serverNames mcpServerDefinitions; }
    )}";

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

  _module.args.buildClawdeAgentMcpConfigFile = buildClawdeAgentMcpConfigFile;

  home = {
    inherit (browserMcp) packages;
  };
}

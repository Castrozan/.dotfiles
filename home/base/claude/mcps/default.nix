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
  inherit (pkgs.stdenv.hostPlatform) isDarwin;

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
    localBaseUrl = "http://localhost:8765";
  };

  mem0OpenmemoryUp = pkgs.writeShellScriptBin "mem0-openmemory-up" (
    builtins.readFile ./mem0/scripts/mem0-openmemory-up
  );

  mem0AutostartEnvironmentPath = lib.concatStringsSep ":" [
    "/usr/local/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${config.home.username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  mcpServerDefinitions = {
    chrome-devtools = {
      command = browserMcp.chromeDevtoolsMcpStdioCommand;
      args = browserMcp.chromeDevtoolsMcpStdioArgs;
    };
    brave-devtools = {
      command = browserMcp.braveDevtoolsMcpStdioCommand;
      args = browserMcp.braveDevtoolsMcpStdioArgs;
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
    (import ./mem0/autostart.nix {
      inherit lib isDarwin;
      usesLocalStack = !mem0Mcp.remoteConfigured;
      bringUpScriptBin = mem0OpenmemoryUp;
      environmentPath = mem0AutostartEnvironmentPath;
    })
    (import ./inject-mcp-servers-into-claude-config.nix {
      inherit homeDir;
      managedMcpServerNames = mcpServerInjectionPartition.managedMcpServerNames;
      mcpServerDefinitions = interactivelyInjectedMcpServerDefinitions;
    })
  ];

  _module.args.buildClawdeAgentMcpConfigFile = buildClawdeAgentMcpConfigFile;

  home = {
    packages = browserMcp.packages ++ [ mem0OpenmemoryUp ];
    file.".config/mem0/openmemory-compose.yaml".source = ./mem0/openmemory-compose.yaml;
  };
}

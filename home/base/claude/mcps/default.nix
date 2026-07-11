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
  chromeBinary =
    if isDarwin then
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else
      "${latest.google-chrome}/bin/google-chrome-stable";

  browserMcp = import ../../../../agents/skills/browser/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
    chromePackage = latest.google-chrome;
  };

  browserUseConfigDir = "${homeDir}/.config/browseruse";

  browserUseMcpWrapper = pkgs.writeShellScript "browser-use-mcp" ''
    export BROWSER_USE_CONFIG_PATH="${browserUseConfigDir}/config.json"
    export ANONYMIZED_TELEMETRY=false
    exec ${pkgs.uv}/bin/uvx --python ${pkgs.python312}/bin/python3.12 --from 'browser-use[cli]' browser-use --mcp "$@"
  '';

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

  figmaMcp = import ./figma {
    inherit
      pkgs
      nodejs
      homeDir
      hostname
      ;
  };

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
    browser-use = {
      command = browserUseMcpWrapper;
      args = [ ];
    };
    mem0 = mem0Mcp.serverConfig;
    figma = figmaMcp.figmaWriteCapableRemoteServerConfig;
    figma-read = {
      command = figmaMcp.figmaReadMcpStdioCommand;
      args = figmaMcp.figmaReadMcpStdioArgs;
    };
  }
  // lib.optionalAttrs (hostname == "chise") {
    vivaldi-devtools = {
      command = browserMcp.vivaldiDevtoolsMcpStdioCommand;
      args = browserMcp.vivaldiDevtoolsMcpStdioArgs;
    };
  };

  hostGatedBrowserMcpServerNames = [ "vivaldi-devtools" ];

  managedMcpServerNames = lib.unique (
    builtins.attrNames mcpServerDefinitions ++ hostGatedBrowserMcpServerNames
  );

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
    (import ./browser-use-config-patcher.nix {
      inherit browserUseConfigDir chromeBinary;
    })
    (import ./inject-mcp-servers-into-claude-config.nix {
      inherit homeDir mcpServerDefinitions managedMcpServerNames;
    })
  ];

  _module.args.buildClawdeAgentMcpConfigFile = buildClawdeAgentMcpConfigFile;

  home = {
    packages = browserMcp.packages ++ [ mem0OpenmemoryUp ];
    file.".config/mem0/openmemory-compose.yaml".source = ./mem0/openmemory-compose.yaml;
  };
}

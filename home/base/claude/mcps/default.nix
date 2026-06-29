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
      inherit homeDir;
      inherit (browserMcp)
        chromeDevtoolsMcpStdioCommand
        chromeDevtoolsMcpStdioArgs
        braveDevtoolsMcpStdioCommand
        braveDevtoolsMcpStdioArgs
        ;
      a2aMcpStdioCommand = a2aMcp.mcpServerCommand;
      a2aMcpStdioArgs = a2aMcp.mcpServerArgs;
      browserUseMcpStdioCommand = browserUseMcpWrapper;
      mem0McpServerConfig = mem0Mcp.serverConfig;
      inherit (figmaMcp)
        figmaReadMcpStdioCommand
        figmaReadMcpStdioArgs
        figmaWriteCapableRemoteServerConfig
        ;
      codexBinaryPath = "${homeDir}/.local/bin/codex";
    })
  ];

  home = {
    packages = browserMcp.packages ++ [ mem0OpenmemoryUp ];
    file.".config/mem0/openmemory-compose.yaml".source = ./mem0/openmemory-compose.yaml;
  };
}

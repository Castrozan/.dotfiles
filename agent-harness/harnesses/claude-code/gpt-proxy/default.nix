{
  pkgs,
  lib,
  config,
  hostname,
  ...
}:
let
  hostsWithClaudex = [
    "chise"
    "kira"
    "rin"
  ];
  claudexEnabledOnThisHost = lib.elem hostname hostsWithClaudex;

  cliProxyApiPackage = import ../cli-proxy-api/package.nix { inherit pkgs lib; };
  cliProxyApiIpv4Gateway = import ../cli-proxy-api/ipv4-gateway { inherit pkgs; };

  proxyListenAddress = "127.0.0.1";
  proxyListenPort = 8317;
  proxyIpv4GatewayListenAddress = "127.0.0.1";
  proxyIpv4GatewayListenPort = 8318;
  proxyIpv4GatewayLoginPort = 8319;
  proxyAuthenticationDirectory = "${config.home.homeDirectory}/.cli-proxy-api";
  proxyLogFilePath = "${config.home.homeDirectory}/.local/state/cli-proxy-api/cli-proxy-api.log";
  proxyLaunchdAgentLabel = "com.dotfiles.cli-proxy-api";
  proxySystemdServiceName = "cli-proxy-api.service";

  proxyServiceInspectionCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      "launchctl print gui/@CURRENT_USER_ID@/${proxyLaunchdAgentLabel}"
    else
      "systemctl --user status ${proxySystemdServiceName}";

  reloadProxyServiceCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      ''launchctl kickstart -k "gui/$(id -u)/${proxyLaunchdAgentLabel}" 2>/dev/null || true''
    else
      "systemctl --user restart ${proxySystemdServiceName} 2>/dev/null || true";

  outboundProxyUrlForGatewayPort =
    ipv4GatewayPort:
    cliProxyApiIpv4Gateway.outboundProxyUrlFor {
      listenAddress = proxyIpv4GatewayListenAddress;
      listenPort = ipv4GatewayPort;
    };

  makeCliProxyApiConfigFile =
    name: ipv4GatewayPort:
    pkgs.writeText name ''
      host: "${proxyListenAddress}"
      port: ${toString proxyListenPort}
      auth-dir: "${proxyAuthenticationDirectory}"
      api-keys: []
      proxy-url: "${outboundProxyUrlForGatewayPort ipv4GatewayPort}"
      debug: false
    '';
  cliProxyApiConfigFile = makeCliProxyApiConfigFile "cli-proxy-api-config.yaml" proxyIpv4GatewayListenPort;
  cliProxyApiLoginConfigFile = makeCliProxyApiConfigFile "cli-proxy-api-login-config.yaml" proxyIpv4GatewayLoginPort;

  cliProxyApiProgramArguments = [
    "${cliProxyApiPackage}/bin/cli-proxy-api"
    "--config"
    "${cliProxyApiConfigFile}"
    "--local-model"
  ];
  ipv4GatewayCliProxyApiProgramArguments = cliProxyApiIpv4Gateway.programArgumentsThroughIpv4Gateway {
    listenAddress = proxyIpv4GatewayListenAddress;
    listenPort = proxyIpv4GatewayListenPort;
    programArguments = cliProxyApiProgramArguments;
  };
  ipv4GatewayCliProxyApiLoginProgramArguments =
    cliProxyApiIpv4Gateway.programArgumentsThroughIpv4Gateway
      {
        listenAddress = proxyIpv4GatewayListenAddress;
        listenPort = proxyIpv4GatewayLoginPort;
        programArguments = [
          "${cliProxyApiPackage}/bin/cli-proxy-api"
          "--config"
          "${cliProxyApiLoginConfigFile}"
          "--codex-login"
        ];
      };

  gptModelForOpusTier = "gpt-5.6-sol(max)[1m]";
  gptModelForSonnetTier = "gpt-5.6-sol(medium)";
  gptModelForHaikuTier = "gpt-5.6-sol(low)";

  claudexLauncher = pkgs.writeShellApplication {
    name = "claudex";
    bashOptions = [ ];
    runtimeEnv = {
      ANTHROPIC_BASE_URL = "http://${proxyListenAddress}:${toString proxyListenPort}";
      ANTHROPIC_AUTH_TOKEN = "cli-proxy-api-local-loopback";
      ANTHROPIC_DEFAULT_OPUS_MODEL = gptModelForOpusTier;
      ANTHROPIC_DEFAULT_SONNET_MODEL = gptModelForSonnetTier;
      ANTHROPIC_DEFAULT_HAIKU_MODEL = gptModelForHaikuTier;
      CLAUDEX_LAUNCHER_PROXY_LISTEN_ADDRESS = proxyListenAddress;
      CLAUDEX_LAUNCHER_PROXY_LISTEN_PORT = toString proxyListenPort;
      CLAUDEX_LAUNCHER_PROXY_SERVICE_INSPECTION_COMMAND = proxyServiceInspectionCommand;
      CLAUDEX_LAUNCHER_CLAUDE_BINARY = "${config.claude.package}/bin/claude";
      CLAUDEX_LAUNCHER_MODEL = gptModelForOpusTier;
    };
    text = builtins.readFile ./scripts/claudex;
  };

  claudexLoginLauncher = pkgs.writeShellScriptBin "claudex-login" ''
    echo "Authenticating your ChatGPT/Codex subscription for cli-proxy-api."
    echo "A browser window opens for OAuth; the callback listens on ${proxyListenAddress}:1455."
    if ! ${lib.escapeShellArgs ipv4GatewayCliProxyApiLoginProgramArguments} "$@"; then
      echo "Authentication failed; credentials were not updated." >&2
      exit 1
    fi
    echo "Credentials stored under ${proxyAuthenticationDirectory}."
    ${reloadProxyServiceCommand}
    echo "Proxy reloaded. Run claudex to start Claude Code on your ChatGPT subscription."
  '';

  ensureCliProxyApiStateDirectoriesScript = pkgs.writeShellScript "cli-proxy-api-ensure-state-directories" ''
    mkdir -p ${lib.escapeShellArg proxyAuthenticationDirectory}
    mkdir -p ${lib.escapeShellArg (builtins.dirOf proxyLogFilePath)}
  '';
in
{
  config = lib.mkIf claudexEnabledOnThisHost (
    lib.mkMerge [
      {
        home.packages = [
          cliProxyApiPackage
          claudexLauncher
          claudexLoginLauncher
        ];

        home.activation.ensureCliProxyApiStateDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${ensureCliProxyApiStateDirectoriesScript}
        '';
      }
      (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
        launchd.agents.cli-proxy-api = {
          enable = true;
          config = {
            Label = proxyLaunchdAgentLabel;
            ProgramArguments = ipv4GatewayCliProxyApiProgramArguments;
            RunAtLoad = true;
            KeepAlive = true;
            StandardOutPath = proxyLogFilePath;
            StandardErrorPath = proxyLogFilePath;
          };
        };
      })
      (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
        systemd.user.services.cli-proxy-api = {
          Unit = {
            Description = "Local proxy bridging the Anthropic Messages API onto a ChatGPT subscription";
            After = [ "default.target" ];
          };
          Service = {
            ExecStart = lib.concatMapStringsSep " " lib.escapeShellArg ipv4GatewayCliProxyApiProgramArguments;
            Restart = "always";
            RestartSec = 5;
          };
          Install.WantedBy = [ "default.target" ];
        };
      })
    ]
  );
}

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

  cliProxyApiPackage = import ../api-translation/cli-proxy-api-package.nix { inherit pkgs lib; };
  cliProxyApiIpv4Gateway = import ../api-translation/ipv4-gateway { inherit pkgs; };
  onDemandService = import ../api-translation/on-demand-service { inherit pkgs; };

  proxyListenAddress = "127.0.0.1";
  proxyListenPort = 8317;
  proxyIpv4GatewayListenAddress = "127.0.0.1";
  proxyIpv4GatewayListenPort = 8318;
  proxyIpv4GatewayLoginPort = 8319;
  proxyAuthenticationDirectory = "${config.home.homeDirectory}/.cli-proxy-api";
  proxyStateDirectory = "${config.home.homeDirectory}/.local/state/cli-proxy-api";
  proxyLogFilePath = "${proxyStateDirectory}/cli-proxy-api.log";
  proxyInstalledConfigurationPath = "${proxyStateDirectory}/config.yaml";
  proxyInstalledLoginConfigurationPath = "${proxyStateDirectory}/login-config.yaml";
  proxyLauncherRegistryDirectory = "${proxyStateDirectory}/launcher-holders";
  proxyStartupTimeoutSeconds = 20;
  proxyLaunchdAgentLabel = "com.dotfiles.cli-proxy-api";
  proxySystemdServiceName = "cli-proxy-api.service";

  proxyServiceInspectionCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      "launchctl print gui/@CURRENT_USER_ID@/${proxyLaunchdAgentLabel}"
    else
      "systemctl --user status ${proxySystemdServiceName}";

  stopProxyServiceCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      ''launchctl kill SIGTERM "gui/$(id -u)/${proxyLaunchdAgentLabel}" 2>/dev/null || true''
    else
      "systemctl --user stop ${proxySystemdServiceName} 2>/dev/null || true";

  proxyServiceSelector = {
    launchdAgentLabel = proxyLaunchdAgentLabel;
    systemdServiceName = proxySystemdServiceName;
  };
  proxyStartCommand = onDemandService.startCommandFor proxyServiceSelector;
  proxyStopCommand = onDemandService.stopCommandFor proxyServiceSelector;
  proxyUnavailableMessage = ''
    cli-proxy-api is not listening on ${proxyListenAddress}:${toString proxyListenPort}.
    If you have never authenticated your ChatGPT subscription, run: claudex-login
    Otherwise inspect the service: ${proxyServiceInspectionCommand}'';

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
    proxyInstalledConfigurationPath
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
          proxyInstalledLoginConfigurationPath
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
      CLAUDEX_LAUNCHER_PROXY_REGISTRY_DIRECTORY = proxyLauncherRegistryDirectory;
      CLAUDEX_LAUNCHER_PROXY_STARTUP_TIMEOUT_SECONDS = toString proxyStartupTimeoutSeconds;
      CLAUDEX_LAUNCHER_PROXY_START_COMMAND = builtins.toJSON proxyStartCommand;
      CLAUDEX_LAUNCHER_PROXY_STOP_COMMAND = builtins.toJSON proxyStopCommand;
      CLAUDEX_LAUNCHER_PROXY_UNAVAILABLE_MESSAGE = proxyUnavailableMessage;
      CLAUDEX_LAUNCHER_LIFECYCLE_PYTHON = builtins.elemAt onDemandService.lifecycleProgramArguments 0;
      CLAUDEX_LAUNCHER_LIFECYCLE_SCRIPT = builtins.elemAt onDemandService.lifecycleProgramArguments 1;
      CLAUDEX_LAUNCHER_CLAUDE_BINARY = "${config.claude.unrestrictedInteractivePackage}/bin/claude";
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
    ${stopProxyServiceCommand}
    echo "Run claudex; it starts the proxy on the new credentials and stops it again when you leave."
  '';

  ensureCliProxyApiStateDirectoriesScript = pkgs.writeShellScript "cli-proxy-api-ensure-state-directories" ''
    mkdir -p ${lib.escapeShellArg proxyAuthenticationDirectory}
    mkdir -p ${lib.escapeShellArg proxyStateDirectory}
    ${pkgs.coreutils}/bin/install -m 600 ${cliProxyApiConfigFile} ${lib.escapeShellArg proxyInstalledConfigurationPath}
    ${pkgs.coreutils}/bin/install -m 600 ${cliProxyApiLoginConfigFile} ${lib.escapeShellArg proxyInstalledLoginConfigurationPath}
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
            RunAtLoad = false;
            KeepAlive = false;
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
            Restart = "no";
          };
        };
      })
    ]
  );
}

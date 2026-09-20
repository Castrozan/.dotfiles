{
  pkgs,
  lib,
  hostname,
  config,
  ...
}:
let
  hostsWithClaudeGo = [
    "chise"
    "kira"
    "rin"
  ];
  claudeGoEnabledOnThisHost = lib.elem hostname hostsWithClaudeGo;
  opencodeGo = import ../../../opencode/go-provider.nix { inherit (config.home) homeDirectory; };

  cliProxyApiPackage = import ../api-translation/cli-proxy-api-package.nix { inherit pkgs lib; };
  cliProxyApiIpv4Gateway = import ../api-translation/ipv4-gateway { inherit pkgs; };
  onDemandService = import ../api-translation/on-demand-service { inherit pkgs; };

  translationProxyListenAddress = "127.0.0.1";
  translationProxyListenPort = 8321;
  translationProxyIpv4GatewayListenAddress = "127.0.0.1";
  translationProxyIpv4GatewayListenPort = 8322;
  translationProxyStateDirectory = "${config.home.homeDirectory}/.local/state/claude-go-proxy";
  translationProxyAuthenticationDirectory = "${translationProxyStateDirectory}/auth";
  translationProxyRenderedConfigurationPath = "${translationProxyStateDirectory}/config.yaml";
  translationProxyLogFilePath = "${translationProxyStateDirectory}/claude-go-proxy.log";
  translationProxyLaunchdAgentLabel = "com.dotfiles.claude-go-proxy";
  translationProxySystemdServiceName = "claude-go-proxy.service";
  translationProxyLauncherRegistryDirectory = "${translationProxyStateDirectory}/launcher-holders";
  translationProxyStartupTimeoutSeconds = 20;

  translationProxyInspectionCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      "launchctl print gui/@CURRENT_USER_ID@/${translationProxyLaunchdAgentLabel}"
    else
      "systemctl --user status ${translationProxySystemdServiceName}";

  translationProxyServiceSelector = {
    launchdAgentLabel = translationProxyLaunchdAgentLabel;
    systemdServiceName = translationProxySystemdServiceName;
  };
  translationProxyServiceLabel = onDemandService.serviceLabelFor translationProxyServiceSelector;
  translationProxyUnavailableMessage = ''
    claude-go: the Console Go translation proxy is not listening on ${translationProxyListenAddress}:${toString translationProxyListenPort}.
    The native Console Go Anthropic endpoint drops tool names, so Claude Code cannot reach these models without it.
    Inspect the service: ${translationProxyInspectionCommand}'';

  translatedModelNames = lib.unique (builtins.attrValues opencodeGo.models);

  translationProxyConfigurationText = import ./translation-proxy-configuration.nix {
    listenAddress = translationProxyListenAddress;
    listenPort = translationProxyListenPort;
    authenticationDirectory = translationProxyAuthenticationDirectory;
    upstreamBaseUrl = "${opencodeGo.baseUrl}/v1";
    upstreamProviderName = "opencode-go";
    modelNames = translatedModelNames;
    apiKeyPlaceholder = "@OPENCODE_GO_API_KEY@";
    outboundProxyUrl = cliProxyApiIpv4Gateway.outboundProxyUrlFor {
      listenAddress = translationProxyIpv4GatewayListenAddress;
      listenPort = translationProxyIpv4GatewayListenPort;
    };
  };

  translationProxyConfigurationTemplate = pkgs.writeText "claude-go-proxy-config-template.yaml" translationProxyConfigurationText;

  renderProxyConfigurationSource = pkgs.writeText "render-proxy-configuration-and-exec.py" (
    builtins.readFile ./scripts/render_proxy_configuration_and_exec.py
  );

  translationProxyProgramArguments = [
    "${pkgs.python312}/bin/python3"
    "${renderProxyConfigurationSource}"
    "${translationProxyConfigurationTemplate}"
    opencodeGo.apiKeyFile
    translationProxyRenderedConfigurationPath
  ]
  ++ cliProxyApiIpv4Gateway.programArgumentsThroughIpv4Gateway {
    listenAddress = translationProxyIpv4GatewayListenAddress;
    listenPort = translationProxyIpv4GatewayListenPort;
    programArguments = [
      "${cliProxyApiPackage}/bin/cli-proxy-api"
      "--config"
      translationProxyRenderedConfigurationPath
      "--local-model"
    ];
  };

  claudeGoLauncher = pkgs.writeShellApplication {
    name = "claude-go";
    bashOptions = [ ];
    runtimeEnv = {
      ANTHROPIC_BASE_URL = "http://${translationProxyListenAddress}:${toString translationProxyListenPort}";
      ANTHROPIC_AUTH_TOKEN = "claude-go-local-loopback";
      ANTHROPIC_DEFAULT_OPUS_MODEL = opencodeGo.models.opus;
      ANTHROPIC_DEFAULT_SONNET_MODEL = opencodeGo.models.sonnet;
      ANTHROPIC_DEFAULT_HAIKU_MODEL = opencodeGo.models.haiku;
      CLAUDE_GO_LAUNCHER_PROXY_LISTEN_ADDRESS = translationProxyListenAddress;
      CLAUDE_GO_LAUNCHER_PROXY_LISTEN_PORT = toString translationProxyListenPort;
      CLAUDE_GO_LAUNCHER_PROXY_INSPECTION_COMMAND = translationProxyInspectionCommand;
      CLAUDE_GO_LAUNCHER_PROXY_REGISTRY_DIRECTORY = translationProxyLauncherRegistryDirectory;
      CLAUDE_GO_LAUNCHER_PROXY_STARTUP_TIMEOUT_SECONDS = toString translationProxyStartupTimeoutSeconds;
      CLAUDE_GO_LAUNCHER_PROXY_SERVICE_CONTROLLER = onDemandService.serviceControllerName;
      CLAUDE_GO_LAUNCHER_PROXY_SERVICE_LABEL = translationProxyServiceLabel;
      # shellcheck disable=SC2089,SC2090 # JSON is consumed literally by the Python lifecycle helper.
      CLAUDE_GO_LAUNCHER_PROXY_START_COMMAND = builtins.toJSON translationProxyStartCommand;
      # shellcheck disable=SC2089,SC2090 # JSON is consumed literally by the Python lifecycle helper.
      CLAUDE_GO_LAUNCHER_PROXY_STOP_COMMAND = builtins.toJSON translationProxyStopCommand;
      # shellcheck disable=SC2089,SC2090 # Text is forwarded verbatim to the lifecycle helper.
      CLAUDE_GO_LAUNCHER_PROXY_UNAVAILABLE_MESSAGE = translationProxyUnavailableMessage;
      CLAUDE_GO_LAUNCHER_LIFECYCLE_PYTHON = builtins.elemAt onDemandService.lifecycleProgramArguments 0;
      CLAUDE_GO_LAUNCHER_LIFECYCLE_SCRIPT = builtins.elemAt onDemandService.lifecycleProgramArguments 1;
      CLAUDE_GO_LAUNCHER_CLAUDE_BINARY = "${config.claude.unrestrictedInteractivePackage}/bin/claude";
      CLAUDE_GO_LAUNCHER_MODEL = opencodeGo.models.sonnet;
    };
    text = builtins.readFile ./scripts/claude-go;
  };

  ensureTranslationProxyStateDirectoriesScript = pkgs.writeShellScript "claude-go-proxy-ensure-state-directories" ''
    mkdir -p ${lib.escapeShellArg translationProxyAuthenticationDirectory}
    chmod 700 ${lib.escapeShellArg translationProxyStateDirectory}
  '';
in
{
  config = lib.mkIf claudeGoEnabledOnThisHost (
    lib.mkMerge [
      {
        home.packages = [ claudeGoLauncher ];

        home.activation.ensureClaudeGoProxyStateDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${ensureTranslationProxyStateDirectoriesScript}
        '';
      }
      (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
        launchd.agents.claude-go-proxy = {
          enable = true;
          config = {
            Label = translationProxyLaunchdAgentLabel;
            ProgramArguments = translationProxyProgramArguments;
            RunAtLoad = false;
            KeepAlive = false;
            StandardOutPath = translationProxyLogFilePath;
            StandardErrorPath = translationProxyLogFilePath;
          };
        };
      })
      (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
        systemd.user.services.claude-go-proxy = {
          Unit = {
            Description = "Translates the Anthropic Messages API onto Console Go's OpenAI endpoint for claude-go";
            After = [ "default.target" ];
          };
          Service = {
            ExecStart = lib.concatMapStringsSep " " lib.escapeShellArg translationProxyProgramArguments;
            Restart = "no";
          };
        };
      })
    ]
  );
}

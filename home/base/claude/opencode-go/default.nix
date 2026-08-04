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
  opencodeGo = import ../../opencode/go-provider.nix { inherit (config.home) homeDirectory; };

  cliProxyApiPackage = import ../cli-proxy-api/package.nix { inherit pkgs lib; };

  translationProxyListenAddress = "127.0.0.1";
  translationProxyListenPort = 8321;
  translationProxyStateDirectory = "${config.home.homeDirectory}/.local/state/claude-go-proxy";
  translationProxyAuthenticationDirectory = "${translationProxyStateDirectory}/auth";
  translationProxyRenderedConfigurationPath = "${translationProxyStateDirectory}/config.yaml";
  translationProxyLogFilePath = "${translationProxyStateDirectory}/claude-go-proxy.log";
  translationProxyLaunchdAgentLabel = "com.dotfiles.claude-go-proxy";
  translationProxySystemdServiceName = "claude-go-proxy.service";

  translationProxyInspectionCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      "launchctl print gui/$(id -u)/${translationProxyLaunchdAgentLabel}"
    else
      "systemctl --user status ${translationProxySystemdServiceName}";

  translatedModelNames = lib.unique (builtins.attrValues opencodeGo.models);

  translationProxyConfigurationText = import ./translation-proxy-configuration.nix {
    listenAddress = translationProxyListenAddress;
    listenPort = translationProxyListenPort;
    authenticationDirectory = translationProxyAuthenticationDirectory;
    upstreamBaseUrl = "${opencodeGo.baseUrl}/v1";
    upstreamProviderName = "opencode-go";
    modelNames = translatedModelNames;
    apiKeyPlaceholder = "@OPENCODE_GO_API_KEY@";
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
    "${cliProxyApiPackage}/bin/cli-proxy-api"
    "--config"
    translationProxyRenderedConfigurationPath
    "--local-model"
  ];

  claudeGoLauncher = pkgs.writeShellScriptBin "claude-go" ''
    unset ANTHROPIC_API_KEY
    export ANTHROPIC_BASE_URL="http://${translationProxyListenAddress}:${toString translationProxyListenPort}"
    export ANTHROPIC_AUTH_TOKEN="claude-go-local-loopback"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="${opencodeGo.models.opus}"
    export ANTHROPIC_DEFAULT_SONNET_MODEL="${opencodeGo.models.sonnet}"
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="${opencodeGo.models.haiku}"
    if ! (exec 3<>/dev/tcp/${translationProxyListenAddress}/${toString translationProxyListenPort}) 2>/dev/null; then
      echo "claude-go: the Console Go translation proxy is not listening on ${translationProxyListenAddress}:${toString translationProxyListenPort}." >&2
      echo "Console Go's own Anthropic endpoint drops tool names, so Claude Code cannot reach these models without it." >&2
      echo "Inspect the service: ${translationProxyInspectionCommand}" >&2
    fi
    exec ${config.claude.package}/bin/claude --model "${opencodeGo.models.sonnet}" "$@"
  '';

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
            RunAtLoad = true;
            KeepAlive = true;
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
            Restart = "always";
            RestartSec = 5;
          };
          Install.WantedBy = [ "default.target" ];
        };
      })
    ]
  );
}

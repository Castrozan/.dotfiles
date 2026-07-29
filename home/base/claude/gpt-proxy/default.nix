{
  pkgs,
  lib,
  config,
  hostname,
  ...
}:
let
  hostsWithClaudeGptProxy = [
    "chise"
    "kira"
    "rin"
  ];
  claudeGptProxyEnabledOnThisHost = lib.elem hostname hostsWithClaudeGptProxy;

  fetchPrebuiltBinary = import ../../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  cliProxyApiVersion = "7.2.96";
  cliProxyApiArtifacts = {
    aarch64-darwin = {
      releaseSystem = "darwin_aarch64";
      sha256 = "sha256-iG7HLFMqhjF3/+C6Fxam39ZNbXp9KwaWXjf9rhRedII=";
    };
    x86_64-linux = {
      releaseSystem = "linux_amd64";
      sha256 = "sha256-sOOK4ufSp6STWywMQ6B5tlM4eqGrzuIwM6GVRJJKLp0=";
    };
  };
  cliProxyApiArtifact =
    cliProxyApiArtifacts.${pkgs.stdenv.hostPlatform.system}
      or (throw "cli-proxy-api is unsupported on ${pkgs.stdenv.hostPlatform.system}");
  cliProxyApiPackage = fetchPrebuiltBinary {
    pname = "cli-proxy-api";
    version = cliProxyApiVersion;
    url = "https://github.com/router-for-me/CLIProxyAPI/releases/download/v${cliProxyApiVersion}/CLIProxyAPI_${cliProxyApiVersion}_${cliProxyApiArtifact.releaseSystem}.tar.gz";
    inherit (cliProxyApiArtifact) sha256;
    binaryName = "cli-proxy-api";
    meta = {
      description = "Local proxy bridging the Anthropic Messages API onto a ChatGPT/Codex subscription";
      homepage = "https://github.com/router-for-me/CLIProxyAPI";
      license = lib.licenses.mit;
      platforms = builtins.attrNames cliProxyApiArtifacts;
      mainProgram = "cli-proxy-api";
    };
  };

  proxyListenAddress = "127.0.0.1";
  proxyListenPort = 8317;
  proxyAuthenticationDirectory = "${config.home.homeDirectory}/.cli-proxy-api";
  proxyLogFilePath = "${config.home.homeDirectory}/.local/state/cli-proxy-api/cli-proxy-api.log";
  proxyLaunchdAgentLabel = "com.dotfiles.cli-proxy-api";
  proxySystemdServiceName = "cli-proxy-api.service";

  proxyServiceInspectionCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      "launchctl print gui/$(id -u)/${proxyLaunchdAgentLabel}"
    else
      "systemctl --user status ${proxySystemdServiceName}";

  reloadProxyServiceCommand =
    if pkgs.stdenv.hostPlatform.isDarwin then
      ''launchctl kickstart -k "gui/$(id -u)/${proxyLaunchdAgentLabel}" 2>/dev/null || true''
    else
      "systemctl --user restart ${proxySystemdServiceName} 2>/dev/null || true";

  cliProxyApiConfigFile = pkgs.writeText "cli-proxy-api-config.yaml" ''
    host: "${proxyListenAddress}"
    port: ${toString proxyListenPort}
    auth-dir: "${proxyAuthenticationDirectory}"
    api-keys: []
    debug: false
  '';

  cliProxyApiProgramArguments = [
    "${cliProxyApiPackage}/bin/cli-proxy-api"
    "--config"
    "${cliProxyApiConfigFile}"
    "--local-model"
  ];

  gptModelForOpusTier = "gpt-5.6-sol(high)";
  gptModelForSonnetTier = "gpt-5.6-sol(medium)";
  gptModelForHaikuTier = "gpt-5.6-sol(low)";

  claudeGptLauncher = pkgs.writeShellScriptBin "claude-gpt" ''
    unset ANTHROPIC_API_KEY
    export ANTHROPIC_BASE_URL="http://${proxyListenAddress}:${toString proxyListenPort}"
    export ANTHROPIC_AUTH_TOKEN="cli-proxy-api-local-loopback"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="${gptModelForOpusTier}"
    export ANTHROPIC_DEFAULT_SONNET_MODEL="${gptModelForSonnetTier}"
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="${gptModelForHaikuTier}"
    if ! (exec 3<>/dev/tcp/${proxyListenAddress}/${toString proxyListenPort}) 2>/dev/null; then
      echo "cli-proxy-api is not listening on ${proxyListenAddress}:${toString proxyListenPort}." >&2
      echo "If you have never authenticated your ChatGPT subscription, run: claude-gpt-login" >&2
      echo "Otherwise inspect the service: ${proxyServiceInspectionCommand}" >&2
    fi
    exec ${config.claude.package}/bin/claude --model "${gptModelForOpusTier}" "$@"
  '';

  claudeGptLoginLauncher = pkgs.writeShellScriptBin "claude-gpt-login" ''
    echo "Authenticating your ChatGPT/Codex subscription for cli-proxy-api."
    echo "A browser window opens for OAuth; the callback listens on ${proxyListenAddress}:1455."
    ${cliProxyApiPackage}/bin/cli-proxy-api --config ${cliProxyApiConfigFile} --codex-login "$@"
    echo "Credentials stored under ${proxyAuthenticationDirectory}."
    ${reloadProxyServiceCommand}
    echo "Proxy reloaded. Run claude-gpt to start Claude Code on your ChatGPT subscription."
  '';

  ensureCliProxyApiStateDirectoriesScript = pkgs.writeShellScript "cli-proxy-api-ensure-state-directories" ''
    mkdir -p ${lib.escapeShellArg proxyAuthenticationDirectory}
    mkdir -p ${lib.escapeShellArg (builtins.dirOf proxyLogFilePath)}
  '';
in
{
  config = lib.mkIf claudeGptProxyEnabledOnThisHost (
    lib.mkMerge [
      {
        home.packages = [
          cliProxyApiPackage
          claudeGptLauncher
          claudeGptLoginLauncher
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
            ProgramArguments = cliProxyApiProgramArguments;
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
            ExecStart = lib.concatMapStringsSep " " lib.escapeShellArg cliProxyApiProgramArguments;
            Restart = "always";
            RestartSec = 5;
          };
          Install.WantedBy = [ "default.target" ];
        };
      })
    ]
  );
}

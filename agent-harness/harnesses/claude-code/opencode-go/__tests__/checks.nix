{
  pkgs,
  lib,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  linuxConfiguration = helpers.homeManagerTestConfigurationForLinuxHost "chise" [
    self.homeManagerModules.claude-code
  ];

  darwinConfigurations =
    map
      (
        hostname:
        helpers.homeManagerTestConfigurationForDarwinHost hostname [
          self.homeManagerModules.claude-code
        ]
      )
      [
        "kira"
        "rin"
      ];

  rinConfiguration = builtins.elemAt darwinConfigurations 1;

  hasPackage =
    configuration: packageName:
    builtins.any (package: lib.getName package == packageName) configuration.home.packages;

  linuxProxyService = linuxConfiguration.systemd.user.services.claude-go-proxy or null;
  rinClaudeGoPackage = builtins.head (
    builtins.filter (package: lib.getName package == "claude-go") rinConfiguration.home.packages
  );
  darwinProxyAgents = map (
    configuration: configuration.launchd.agents.claude-go-proxy or null
  ) darwinConfigurations;
  linuxProxyCommand = builtins.concatStringsSep " " (
    lib.toList (linuxProxyService.Service.ExecStart or "")
  );

  translatedModelNames = [
    "deepseek-v4-pro"
    "deepseek-v4-flash"
    "kimi-k3"
  ];
  translationProxyConfigurationText = import ../translation-proxy-configuration.nix {
    listenAddress = "127.0.0.1";
    listenPort = 8321;
    authenticationDirectory = "/home/test/.local/state/claude-go-proxy/auth";
    upstreamBaseUrl = "https://opencode.ai/zen/go/v1";
    upstreamProviderName = "opencode-go";
    modelNames = translatedModelNames;
    apiKeyPlaceholder = "@OPENCODE_GO_API_KEY@";
    outboundProxyUrl = "http://127.0.0.1:8322";
  };
in
{
  opencode-go-linux-package =
    mkEvalCheck "opencode-go-linux-package" (hasPackage linuxConfiguration "claude-go")
      "Chise must install the claude-go launcher";

  opencode-go-darwin-packages = mkEvalCheck "opencode-go-darwin-packages" (builtins.all (
    configuration: hasPackage configuration "claude-go"
  ) darwinConfigurations) "Kira and Rin must install the claude-go launcher";

  opencode-go-rin-launches-the-unrestricted-interactive-package =
    mkEvalCheck "opencode-go-rin-launches-the-unrestricted-interactive-package"
      (
        lib.hasInfix "${rinConfiguration.claude.unrestrictedInteractivePackage}/bin/claude" rinClaudeGoPackage.text
        && !(lib.hasInfix "${rinConfiguration.claude.package}/bin/claude" rinClaudeGoPackage.text)
      )
      "claude-go uses a different provider and must remain available outside Rin's MCD-only plain claude command";

  opencode-go-linux-translation-proxy-service =
    mkEvalCheck "opencode-go-linux-translation-proxy-service"
      (linuxProxyService != null && linuxProxyService.Service.Restart == "always")
      "claude-go reaches Console Go only through the local translation proxy, so a host installing the launcher without an always-restarting proxy behind it ships a launcher that 400s on its first tool call";

  opencode-go-darwin-translation-proxy-agents =
    mkEvalCheck "opencode-go-darwin-translation-proxy-agents"
      (builtins.all (agent: agent != null && agent.config.KeepAlive) darwinProxyAgents)
      "the darwin hosts install the same launcher, so they need the same always-running translation proxy behind it";

  opencode-go-translation-proxy-nests-every-model-under-its-provider =
    mkEvalCheck "opencode-go-translation-proxy-nests-every-model-under-its-provider"
      (builtins.all (
        modelName:
        lib.hasInfix "      - name: \"${modelName}\"\n        alias: \"${modelName}\"\n" translationProxyConfigurationText
      ) translatedModelNames)
      "the proxy config is YAML, so each model must stay indented under its provider's models key; a Nix indented string silently strips the leading whitespace of interpolated multi-line text, which flattens the list, makes the file unparseable, and leaves the service restarting forever while claude-go reports only a refused connection";

  opencode-go-translation-proxy-template-carries-no-credential =
    mkEvalCheck "opencode-go-translation-proxy-template-carries-no-credential"
      (lib.hasInfix "api-key: \"@OPENCODE_GO_API_KEY@\"" translationProxyConfigurationText)
      "the template is written to the world-readable Nix store, so it must carry the placeholder the service substitutes at start and never the key itself";

  opencode-go-translation-proxy-routes-its-upstream-through-the-ipv4-gateway =
    mkEvalCheck "opencode-go-translation-proxy-routes-its-upstream-through-the-ipv4-gateway"
      (
        lib.hasInfix "proxy-url: \"http://127.0.0.1:8322\"" translationProxyConfigurationText
        && lib.hasInfix "cli-proxy-api-ipv4-gateway.py" linuxProxyCommand
        && builtins.all (
          agent:
          agent != null
          && builtins.any (lib.hasSuffix "cli-proxy-api-ipv4-gateway.py") agent.config.ProgramArguments
        ) darwinProxyAgents
      )
      "a host that resolves Console Go to an AAAA record it cannot reach fails the write mid-request, so claude-go reports a bare socket error instead of the upstream's own answer; pinning the proxy's egress to IPv4 through the gateway is what makes a quota or authentication failure arrive as the message the API actually sent";

  opencode-go-translation-proxy-takes-the-key-from-disk =
    mkEvalCheck "opencode-go-translation-proxy-takes-the-key-from-disk"
      (
        lib.hasInfix ".secrets/opencode-api-key" linuxProxyCommand
        && !(lib.hasInfix "api-key: " linuxProxyCommand)
      )
      "the proxy authenticates to the paid plan and every Nix store path is world readable, so its command must point at the agenix-deployed key file rather than carry the credential";
}

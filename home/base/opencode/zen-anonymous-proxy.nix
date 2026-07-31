{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.opencode.zenAnonymousProxy;
in
{
  options.opencode.zenAnonymousProxy = {
    enable = lib.mkEnableOption ''
      a loopback proxy that carries OpenAI-compatible calls to OpenCode Zen with
      the Authorization header stripped. Zen serves its free models to
      unauthenticated callers and rejects any key it did not issue, while a model
      runtime that insists on a configured key for every remote provider has no
      way to send none; pointing such a runtime at this loopback base URL gives it
      a local, keyless provider that still reaches Zen
    '';

    port = lib.mkOption {
      type = lib.types.port;
      default = 18790;
      description = "Loopback port the proxy listens on.";
    };

    baseUrl = lib.mkOption {
      type = lib.types.str;
      readOnly = true;
      default = "http://127.0.0.1:${toString cfg.port}/v1";
      description = "OpenAI-compatible base URL a model runtime points at to reach Zen through this proxy. Read-only so a consumer names the proxy rather than restating its port.";
    };
  };

  config = lib.mkIf (cfg.enable && pkgs.stdenv.hostPlatform.isLinux) {
    systemd.user.services.opencode-zen-anonymous-proxy = {
      Unit = {
        Description = "Loopback proxy reaching OpenCode Zen without an Authorization header";
        After = [ "network.target" ];
      };
      Service = {
        ExecStart = "${pkgs.python312}/bin/python3 ${./scripts/opencode_zen_anonymous_proxy.py}";
        Environment = [ "OPENCODE_ZEN_PROXY_PORT=${toString cfg.port}" ];
        Restart = "always";
        RestartSec = "5s";
      };
      Install.WantedBy = [ "default.target" ];
    };
  };
}

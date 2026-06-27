{
  pkgs,
  lib,
  self,
  ...
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  nixosCfg = self.nixosConfigurations.chise.config;

  evalCloudflareTunnelConnector =
    connectorSettings:
    (lib.evalModules {
      modules = [
        ../../../nixos/modules/cloudflare-tunnel-connector
        {
          options.services.cloudflared = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.cloudflareTunnelConnector = connectorSettings;
        }
      ];
    }).config;

  cloudflareTunnelConnectorTunnelId = "00000000-0000-0000-0000-000000000000";

  cloudflareTunnelConnectorDisabled = evalCloudflareTunnelConnector {
    enable = false;
  };

  cloudflareTunnelConnectorEnabled = evalCloudflareTunnelConnector {
    enable = true;
    tunnelId = cloudflareTunnelConnectorTunnelId;
    ingressHostname = "jarvis-session-origin.lucaszanoni.com";
    credentialsFile = "/run/agenix/jarvis-session-connector-credentials";
  };

  cloudflareTunnelConnectorEnabledTunnel =
    cloudflareTunnelConnectorEnabled.services.cloudflared.tunnels.${cloudflareTunnelConnectorTunnelId};
in
{
  chise-nix-daemon-max-jobs = mkEvalCheck "chise-nix-daemon-max-jobs" (
    nixosCfg.nix.settings.max-jobs <= 6
  ) "max-jobs must be <= 6 to prevent memory saturation on 16GB RAM";

  chise-nix-daemon-cores = mkEvalCheck "chise-nix-daemon-cores" (
    nixosCfg.nix.settings.cores > 0 && nixosCfg.nix.settings.cores <= 2
  ) "cores must be 1-2 to leave CPU headroom for interactive processes";

  chise-nix-daemon-cpu-sched-policy = mkEvalCheck "chise-nix-daemon-cpu-sched-policy" (
    nixosCfg.nix.daemonCPUSchedPolicy == "batch"
  ) "nix-daemon must use batch CPU scheduling for background throughput";

  chise-nix-daemon-io-sched-class = mkEvalCheck "chise-nix-daemon-io-sched-class" (
    nixosCfg.nix.daemonIOSchedClass == "idle"
  ) "nix-daemon must use idle IO scheduling to avoid starving interactive IO";

  chise-nix-daemon-nice = mkEvalCheck "chise-nix-daemon-nice" (
    nixosCfg.systemd.services.nix-daemon.serviceConfig.Nice == 19
  ) "nix-daemon must run at Nice=19 (lowest CPU priority)";

  chise-earlyoom-enabled =
    mkEvalCheck "chise-earlyoom-enabled" nixosCfg.services.earlyoom.enable
      "earlyoom must be enabled to prevent kernel OOM freezes";

  chise-zram-enabled =
    mkEvalCheck "chise-zram-enabled" nixosCfg.zramSwap.enable
      "zram swap must be enabled for compressed in-memory swap";

  chise-keyboard-backlight-service-enabled =
    mkEvalCheck "chise-keyboard-backlight-service-enabled"
      (nixosCfg.systemd.services.dim-keyboard-backlight.enable or true)
      "dim-keyboard-backlight service must be defined";

  chise-keyboard-backlight-service-oneshot = mkEvalCheck "chise-keyboard-backlight-service-oneshot" (
    nixosCfg.systemd.services.dim-keyboard-backlight.serviceConfig.Type == "oneshot"
  ) "dim-keyboard-backlight must be a oneshot service";

  chise-keyboard-backlight-service-remain-after-exit =
    mkEvalCheck "chise-keyboard-backlight-service-remain-after-exit"
      nixosCfg.systemd.services.dim-keyboard-backlight.serviceConfig.RemainAfterExit
      "dim-keyboard-backlight must remain after exit";

  chise-keyboard-backlight-scripts-installed =
    mkEvalCheck "chise-keyboard-backlight-scripts-installed"
      (
        let
          packageNames = map (p: p.name or "") nixosCfg.environment.systemPackages;
          hasScript = name: builtins.any (n: lib.hasPrefix name n) packageNames;
        in
        hasScript "set-keyboard-backlight-brightness"
        && hasScript "set-keyboard-backlight-color"
        && hasScript "reset-keyboard-backlight"
      )
      "all three keyboard backlight scripts must be in system packages";

  chise-cockpit-session-bridge-enabled =
    mkEvalCheck "chise-cockpit-session-bridge-enabled"
      (builtins.elem "multi-user.target" nixosCfg.systemd.services.cockpit-session-bridge.wantedBy)
      "cockpit-session-bridge unit must be wanted by multi-user.target so the cockpit Internal terminal has a backend";

  chise-cockpit-session-bridge-execstart-resolves =
    mkEvalCheck "chise-cockpit-session-bridge-execstart-resolves"
      (lib.hasInfix "cockpit_session_bridge" nixosCfg.systemd.services.cockpit-session-bridge.serviceConfig.ExecStart)
      "cockpit-session-bridge ExecStart must resolve to the packaged bridge so the service can start";

  chise-cockpit-session-bridge-loopback-only =
    mkEvalCheck "chise-cockpit-session-bridge-loopback-only"
      (
        nixosCfg.systemd.services.cockpit-session-bridge.environment.COCKPIT_SESSION_BRIDGE_LISTEN_ADDRESS
        == "127.0.0.1"
      )
      "cockpit-session-bridge must bind loopback only so only the co-located Cloudflare Tunnel connector can reach it";

  chise-cockpit-session-bridge-origin-non-empty =
    mkEvalCheck "chise-cockpit-session-bridge-origin-non-empty"
      (
        nixosCfg.systemd.services.cockpit-session-bridge.environment.COCKPIT_SESSION_BRIDGE_ALLOWED_ORIGIN
        != ""
      )
      "cockpit-session-bridge must enforce a non-empty allowed Origin so a forged browser request cannot open a session";

  chise-cockpit-session-bridge-attaches-persistent-session =
    mkEvalCheck "chise-cockpit-session-bridge-attaches-persistent-session"
      (lib.hasInfix "attach-session" nixosCfg.systemd.services.cockpit-session-bridge.environment.COCKPIT_SESSION_BRIDGE_COMMAND_JSON)
      "cockpit-session-bridge must attach each owner connection to the always-on opencode tmux session rather than spawn a throwaway shell, so every connection shares one live TUI";

  chise-jarvis-session-tmux-enabled =
    mkEvalCheck "chise-jarvis-session-tmux-enabled"
      (builtins.elem "multi-user.target" nixosCfg.systemd.services.jarvis-session-tmux.wantedBy)
      "the persistent opencode tmux session unit must be wanted by multi-user.target so the always-on TUI exists for the bridge to attach to";

  chise-jarvis-session-tmux-keepalive =
    mkEvalCheck "chise-jarvis-session-tmux-keepalive"
      (nixosCfg.systemd.services.jarvis-session-tmux.serviceConfig.Restart == "always")
      "the persistent opencode tmux session must restart always so opencode is resident like the clawde agents and a crash respawns a fresh TUI";

  chise-jarvis-session-tmux-launches-opencode =
    mkEvalCheck "chise-jarvis-session-tmux-launches-opencode"
      (lib.hasInfix "opencode" nixosCfg.systemd.services.jarvis-session-tmux.environment.JARVIS_PERSISTENT_SESSION_COMMAND)
      "the persistent tmux session must launch opencode as its window command so the cockpit terminal shows the opencode TUI";

  chise-cloudflare-tunnel-connector-disabled-publishes-nothing =
    mkEvalCheck "chise-cloudflare-tunnel-connector-disabled-publishes-nothing"
      (!(cloudflareTunnelConnectorDisabled.services.cloudflared.enable or false))
      "the Cloudflare Tunnel connector must publish no cloudflared service while disabled, so a host that does not opt in exposes no public origin and the Jarvis bridge stays reachable only over loopback";

  chise-cloudflare-tunnel-connector-enabled-turns-on-cloudflared =
    mkEvalCheck "chise-cloudflare-tunnel-connector-enabled-turns-on-cloudflared"
      cloudflareTunnelConnectorEnabled.services.cloudflared.enable
      "an enabled Cloudflare Tunnel connector must turn cloudflared on so the owner-only cockpit terminal reaches the Jarvis bridge over the named tunnel";

  chise-cloudflare-tunnel-connector-registers-tunnel-by-id =
    mkEvalCheck "chise-cloudflare-tunnel-connector-registers-tunnel-by-id"
      (builtins.hasAttr cloudflareTunnelConnectorTunnelId cloudflareTunnelConnectorEnabled.services.cloudflared.tunnels)
      "the connector must register the named tunnel under its configured tunnelId so cloudflared runs the provisioned tunnel rather than an empty default";

  chise-cloudflare-tunnel-connector-ingress-routes-origin-to-loopback =
    mkEvalCheck "chise-cloudflare-tunnel-connector-ingress-routes-origin-to-loopback"
      (
        cloudflareTunnelConnectorEnabledTunnel.ingress."jarvis-session-origin.lucaszanoni.com"
        == "http://127.0.0.1:8787"
      )
      "the connector must route only the single Jarvis origin hostname to the loopback bridge so it exposes nothing else from the host";

  chise-cloudflare-tunnel-connector-credentials-from-agenix =
    mkEvalCheck "chise-cloudflare-tunnel-connector-credentials-from-agenix"
      (
        cloudflareTunnelConnectorEnabledTunnel.credentialsFile
        == "/run/agenix/jarvis-session-connector-credentials"
      )
      "the connector must take its tunnel credentials from the agenix-provisioned path so the account tag and tunnel secret never enter the Nix store";
}

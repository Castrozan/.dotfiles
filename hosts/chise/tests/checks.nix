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

  arrStackChecks = import ./arr-stack.nix { inherit pkgs lib; };

  cloudflareTunnelChecks = import ./cloudflare-tunnels.nix { inherit pkgs lib; };

  arrMediaFunnelChecks = import ./arr-media-funnel.nix { inherit pkgs lib; };

  arrMediaLoginRateLimitProxyChecks = import ./arr-media-login-ratelimit-proxy.nix {
    inherit pkgs lib;
  };

  arrStackOnDemandSupervisorChecks = import ./arr-stack-on-demand-supervisor.nix {
    inherit pkgs lib;
  };

  arrMediaFunnelExecStart = builtins.concatStringsSep "\n" nixosCfg.systemd.services.arr-media-tailscale-funnel.serviceConfig.ExecStart;
in
arrStackChecks
// cloudflareTunnelChecks
// arrMediaFunnelChecks
// arrMediaLoginRateLimitProxyChecks
// arrStackOnDemandSupervisorChecks
// {
  chise-arr-on-demand-supervisor-wired-on-chise =
    mkEvalCheck "chise-arr-on-demand-supervisor-wired-on-chise"
      (
        (nixosCfg.systemd.services ? arr-stack-on-demand-supervisor)
        && builtins.elem "timers.target" nixosCfg.systemd.timers.arr-stack-on-demand-supervisor.wantedBy
      )
      "chise must actually run the on-demand supervisor service and its polling timer, or the download chain would never come up for a request or go down when idle on the real host";

  chise-arr-on-demand-supervisor-excludes-front-ends-on-chise =
    mkEvalCheck "chise-arr-on-demand-supervisor-excludes-front-ends-on-chise"
      (
        !(lib.hasInfix "jellyfin" nixosCfg.systemd.services.arr-stack-on-demand-supervisor.environment.ARR_ON_DEMAND_SERVICES)
        && !(lib.hasInfix "jellyseerr" nixosCfg.systemd.services.arr-stack-on-demand-supervisor.environment.ARR_ON_DEMAND_SERVICES)
      )
      "the wired chise supervisor must never list jellyfin or jellyseerr among its on-demand services, so the idle sweep can never stop the always-on public front ends the funnel and rate limiter depend on";

  chise-arr-on-demand-supervisor-keeps-chain-always-on =
    mkEvalCheck "chise-arr-on-demand-supervisor-keeps-chain-always-on"
      (
        nixosCfg.systemd.services.arr-stack-on-demand-supervisor.environment.ARR_KEEP_CHAIN_ALWAYS_ON
        == "true"
      )
      "chise opts the supervisor into keep-chain-always-on so Sonarr and Radarr stay resident and catch newly aired episodes of monitored series the moment they release, instead of idling down and missing them";

  chise-arr-media-funnel-targets-ratelimit-proxy-not-container =
    mkEvalCheck "chise-arr-media-funnel-targets-ratelimit-proxy-not-container"
      (
        lib.hasInfix "http://127.0.0.1:9443" arrMediaFunnelExecStart
        && lib.hasInfix "http://127.0.0.1:9444" arrMediaFunnelExecStart
        && !(lib.hasInfix "http://127.0.0.1:8096" arrMediaFunnelExecStart)
        && !(lib.hasInfix "http://127.0.0.1:5055" arrMediaFunnelExecStart)
      )
      "the public funnel must target the loopback rate-limit proxy ports (9443/9444), never the container ports (8096/5055) directly, so no public request can reach the loginless media origins without passing the per-IP login limiter first";

  chise-arr-media-ratelimit-nginx-enabled-on-chise =
    mkEvalCheck "chise-arr-media-ratelimit-nginx-enabled-on-chise" nixosCfg.services.nginx.enable
      "chise must actually run the rate-limiting nginx the funnel now depends on, or the public media endpoints would 502 behind a funnel pointing at a dead port";

  chise-arr-media-funnel-requires-nginx-before-repoint =
    mkEvalCheck "chise-arr-media-funnel-requires-nginx-before-repoint"
      (
        builtins.elem "nginx.service" nixosCfg.systemd.services.arr-media-tailscale-funnel.after
        && builtins.elem "nginx.service" nixosCfg.systemd.services.arr-media-tailscale-funnel.requires
      )
      "the funnel unit must order after and require nginx so a rebuild only repoints the public funnel onto the proxy once nginx has actually started; if nginx fails its config test the funnel unit never starts and the previous container target stays live (up but unthrottled) instead of the funnel 502-ing onto a dead proxy";

  chise-rebuild-guard-wrapper-shadows-nixos-rebuild =
    mkEvalCheck "chise-rebuild-guard-wrapper-shadows-nixos-rebuild"
      (builtins.any (
        p:
        (p.name or "") == "nixos-rebuild"
        && (p.meta.priority or lib.meta.defaultPriority) < lib.meta.defaultPriority
      ) nixosCfg.environment.systemPackages)
      "the nixos-rebuild guard wrapper must be installed with lib.hiPrio so it wins the systemPackages collision and shadows the real nixos-rebuild, blocking a manual switch/boot/test outside the rebuild command";

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
}

{
  lib,
  mkEvalCheck,
  nixosCfg,
}:
let
  arrMediaFunnelExecStart = builtins.concatStringsSep "\n" nixosCfg.systemd.services.arr-media-tailscale-funnel.serviceConfig.ExecStart;
in
{
  chise-jellyseerr-email-notifications-wired-on-chise =
    mkEvalCheck "chise-jellyseerr-email-notifications-wired-on-chise"
      (
        (nixosCfg.systemd.services ? jellyseerr-email-notifications)
        && builtins.elem "multi-user.target" nixosCfg.systemd.services.jellyseerr-email-notifications.wantedBy
        && nixosCfg.systemd.services.jellyseerr-email-notifications.restartTriggers != [ ]
      )
      "chise must actually run the email-notification patcher and carry a restartTrigger, or a fresh Gmail app password dropped into agenix would never be applied to Jellyseerr on rebuild";

  chise-jellyseerr-email-notifies-requester-on-media-available =
    mkEvalCheck "chise-jellyseerr-email-notifies-requester-on-media-available"
      (
        builtins.bitAnd (lib.toInt nixosCfg.systemd.services.jellyseerr-email-notifications.environment.JELLYSEERR_NOTIFICATION_TYPES_BITMASK) 8
        == 8
      )
      "chise must set the email agent bitmask to include Media Available (bit 8), the notification Jellyseerr routes to the requester, so an auto-approving friend whose request finishes downloading is emailed that it is now available; auto-approval suppresses any requester-facing 'being processed' notification, so available is the friend-facing event that survives it";

  chise-jellyseerr-email-app-password-secret-declared =
    mkEvalCheck "chise-jellyseerr-email-app-password-secret-declared"
      (
        (nixosCfg.age.secrets ? "jellyseerr-smtp-app-password")
        && lib.hasInfix "jellyseerr-smtp-app-password" nixosCfg.systemd.services.jellyseerr-email-notifications.environment.JELLYSEERR_SMTP_APP_PASSWORD_FILE
      )
      "the Gmail app password must be a declared agenix secret whose decrypted path is what the patcher reads, so the password lives only in the encrypted store and never in the module env as a literal";

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

  chise-arr-config-provisioner-wired-with-agenix-secrets =
    mkEvalCheck "chise-arr-config-provisioner-wired-with-agenix-secrets"
      (
        (nixosCfg.systemd.services ? arr-config-provisioner)
        && (nixosCfg.age.secrets ? "arr-qbittorrent-password")
        && (nixosCfg.age.secrets ? "arr-samaritano-indexer-apikey")
        && nixosCfg.systemd.services.arr-config-provisioner.restartTriggers != [ ]
      )
      "chise must actually run the config provisioner, declare both arr secrets in agenix, and carry a restartTrigger so a re-encrypted secret re-provisions on rebuild, or a wiped config dir would not be reconstructed from the repo";

  chise-arr-on-demand-disk-guard-emails-via-agenix-secret =
    mkEvalCheck "chise-arr-on-demand-disk-guard-emails-via-agenix-secret"
      (
        lib.hasInfix "jellyseerr-smtp-app-password" nixosCfg.systemd.services.arr-stack-on-demand-supervisor.environment.ARR_DISK_ALERT_APP_PASSWORD_FILE
        &&
          nixosCfg.systemd.services.arr-stack-on-demand-supervisor.environment.ARR_DISK_ALERT_EMAIL_RECIPIENT
          != ""
      )
      "the chise disk guard must send its low-space alert through the agenix Gmail app password and a real recipient, reusing the Jellyseerr email secret so a critical disk pauses downloads and actually tells Lucas rather than failing silently";

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

  chise-arr-drive-guard-restores-front-ends-on-reconnect =
    mkEvalCheck "chise-arr-drive-guard-restores-front-ends-on-reconnect"
      (lib.hasInfix "arr-stack-drive-guard-start" nixosCfg.systemd.services.arr-stack-drive-guard.serviceConfig.ExecStart)
      "the drive guard's ExecStart must run the compose bring-up script rather than the true no-op, so when the data drive reconnects and the mount reactivates the always-on front ends the guard tore down come back without a manual bring-up; the download chain is left to the supervisor poll, and the guard's ExecStop still stops it gracefully on disconnect";
}

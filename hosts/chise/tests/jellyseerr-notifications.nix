{
  pkgs,
  lib,
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  evalNotifications =
    settings:
    (lib.evalModules {
      specialArgs = { inherit pkgs; };
      modules = [
        ../../../nixos/modules/jellyseerr-notifications
        {
          options.systemd = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.jellyseerrEmailNotifications = settings;
        }
      ];
    }).config;

  baseSettings = {
    enable = true;
    jellyseerrSettingsFile = "/home/zanoni/arr-stack/config/jellyseerr/settings.json";
    senderAddress = "castro.lucas290@gmail.com";
    smtpUsername = "castro.lucas290@gmail.com";
    appPasswordSecretFile = "/run/agenix/jellyseerr-smtp-app-password";
  };

  notificationsDisabled = evalNotifications (baseSettings // { enable = false; });
  notificationsEnabled = evalNotifications baseSettings;

  enabledService = notificationsEnabled.systemd.services.jellyseerr-email-notifications;
  enabledEnvironment = enabledService.environment;
in
{
  chise-jellyseerr-email-disabled-defines-no-service =
    mkEvalCheck "chise-jellyseerr-email-disabled-defines-no-service"
      (!(notificationsDisabled.systemd.services or { } ? jellyseerr-email-notifications))
      "a host that does not opt in must get no email-notification patcher service, so an unopted host never touches Jellyseerr settings.json";

  chise-jellyseerr-email-is-oneshot-remain-after-exit =
    mkEvalCheck "chise-jellyseerr-email-is-oneshot-remain-after-exit"
      (
        enabledService.serviceConfig.Type == "oneshot"
        && enabledService.serviceConfig.RemainAfterExit
        && builtins.elem "multi-user.target" enabledService.wantedBy
      )
      "the patcher must be a oneshot that remains after exit and is wanted by multi-user.target, so it renders the email agent once per activation and a restartTrigger on the secret re-runs it when the app password changes";

  chise-jellyseerr-email-runs-the-packaged-patcher =
    mkEvalCheck "chise-jellyseerr-email-runs-the-packaged-patcher"
      (lib.hasInfix "patch_jellyseerr_email_notifications.py" enabledService.serviceConfig.ExecStart)
      "the service must launch the packaged patch script so the settings.json rewrite logic is the tested code, not an inline shell heredoc";

  chise-jellyseerr-email-targets-pending-approval =
    mkEvalCheck "chise-jellyseerr-email-targets-pending-approval"
      (enabledEnvironment.JELLYSEERR_NOTIFICATION_TYPES_BITMASK == "2")
      "the default notification bitmask must be 2 (Request Pending Approval), the event routed to admins the moment a user requests media needing approval, which is exactly the ask of getting notified on a new request";

  chise-jellyseerr-email-drives-gmail-submission =
    mkEvalCheck "chise-jellyseerr-email-drives-gmail-submission"
      (
        enabledEnvironment.JELLYSEERR_SMTP_HOST == "smtp.gmail.com"
        && enabledEnvironment.JELLYSEERR_SMTP_PORT == "587"
        && enabledEnvironment.JELLYSEERR_CONTAINER_NAME == "arr-jellyseerr"
      )
      "the patcher must submit through Gmail on the STARTTLS port and reload the arr-jellyseerr container, matching the compose container_name so Jellyseerr picks the new agent up";

  chise-jellyseerr-email-keeps-app-password-out-of-source =
    mkEvalCheck "chise-jellyseerr-email-keeps-app-password-out-of-source"
      (
        lib.hasInfix "agenix" enabledEnvironment.JELLYSEERR_SMTP_APP_PASSWORD_FILE
        && (enabledEnvironment.JELLYSEERR_SMTP_APP_PASSWORD_SENTINEL or "") != ""
        && !(enabledEnvironment ? JELLYSEERR_SMTP_APP_PASSWORD)
      )
      "the only real secret, the Gmail app password, must reach the patcher as an agenix file path with a sentinel guard and never as a literal env value, so no password ever enters the public nix source";
}

{
  config,
  lib,
  pkgs,
  ...
}:
let
  jellyseerrEmailNotificationsConfig = config.custom.jellyseerrEmailNotifications;
  patchScript = ./scripts/patch_jellyseerr_email_notifications.py;
in
{
  options.custom.jellyseerrEmailNotifications = {
    enable = lib.mkEnableOption "a root systemd oneshot that renders the Jellyseerr email notification agent declaratively from nix, enabling it to mail the admin whenever a request needs approval; the SMTP host, port, sender and username live in nix while only the Gmail app password comes from an agenix secret, and until that secret holds a real password the agent is left untouched so no half-configured email agent is pushed";

    jellyseerrSettingsFile = lib.mkOption {
      type = lib.types.str;
      description = "Absolute path to the Jellyseerr settings.json the patcher reads and rewrites in place; it is container-owned root state under the arr-stack config volume, so the patcher runs as root and only touches the notifications.agents.email block.";
    };

    jellyseerrContainerName = lib.mkOption {
      type = lib.types.str;
      default = "arr-jellyseerr";
      description = "The docker container name to restart after patching settings.json so Jellyseerr reloads the new email agent, matching the container_name declared in docker-compose.yml.";
    };

    smtpHost = lib.mkOption {
      type = lib.types.str;
      default = "smtp.gmail.com";
      description = "SMTP relay host Jellyseerr sends through; defaults to Gmail's submission host.";
    };

    smtpPort = lib.mkOption {
      type = lib.types.int;
      default = 587;
      description = "SMTP submission port; port 465 selects implicit TLS while any other port (587) selects STARTTLS, which the patcher derives into Jellyseerr's secure/requireTls options.";
    };

    senderName = lib.mkOption {
      type = lib.types.str;
      default = "Jellyseerr Requests";
      description = "Display name on the From header of the notification mail.";
    };

    senderAddress = lib.mkOption {
      type = lib.types.str;
      description = "The From address of the notification mail, which for Gmail submission must be the same account as the SMTP username.";
    };

    smtpUsername = lib.mkOption {
      type = lib.types.str;
      description = "SMTP auth username, the full Gmail address whose app password authorizes submission.";
    };

    appPasswordSecretFile = lib.mkOption {
      type = lib.types.str;
      description = "Path to the agenix-decrypted file holding the Gmail app password; the only real secret, kept out of nix source and read at activation by the root patcher.";
    };

    appPasswordSentinel = lib.mkOption {
      type = lib.types.str;
      default = "PENDING_GMAIL_APP_PASSWORD_SET_VIA_AGENIX";
      description = "Placeholder value the app password secret ships with before a real Gmail app password is minted; while the decrypted secret equals this sentinel the patcher leaves the email agent disabled instead of pushing a broken SMTP password.";
    };

    notificationTypesBitmask = lib.mkOption {
      type = lib.types.int;
      default = 2;
      description = "Jellyseerr notification-type bitmask for the email agent; 2 is Request Pending Approval, the event routed to admins the moment a user requests media that needs approval. Other bits: 4 approved, 8 available, 16 failed, 64 declined, 128 auto-approved.";
    };
  };

  config = lib.mkIf jellyseerrEmailNotificationsConfig.enable {
    systemd.services.jellyseerr-email-notifications = {
      description = "Render the Jellyseerr email notification agent declaratively and reload the container";
      after = [ "docker.service" ];
      wantedBy = [ "multi-user.target" ];
      environment = {
        JELLYSEERR_SETTINGS_FILE = jellyseerrEmailNotificationsConfig.jellyseerrSettingsFile;
        JELLYSEERR_CONTAINER_NAME = jellyseerrEmailNotificationsConfig.jellyseerrContainerName;
        JELLYSEERR_SMTP_APP_PASSWORD_FILE = jellyseerrEmailNotificationsConfig.appPasswordSecretFile;
        JELLYSEERR_SMTP_APP_PASSWORD_SENTINEL = jellyseerrEmailNotificationsConfig.appPasswordSentinel;
        JELLYSEERR_EMAIL_SENDER_ADDRESS = jellyseerrEmailNotificationsConfig.senderAddress;
        JELLYSEERR_EMAIL_SENDER_NAME = jellyseerrEmailNotificationsConfig.senderName;
        JELLYSEERR_SMTP_HOST = jellyseerrEmailNotificationsConfig.smtpHost;
        JELLYSEERR_SMTP_PORT = toString jellyseerrEmailNotificationsConfig.smtpPort;
        JELLYSEERR_SMTP_USERNAME = jellyseerrEmailNotificationsConfig.smtpUsername;
        JELLYSEERR_NOTIFICATION_TYPES_BITMASK = toString jellyseerrEmailNotificationsConfig.notificationTypesBitmask;
        DOCKER_BINARY = "${pkgs.docker}/bin/docker";
      };
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        ExecStart = "${pkgs.python3}/bin/python3 ${patchScript}";
      };
    };
  };
}

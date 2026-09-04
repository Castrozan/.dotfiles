{
  pkgs,
  lib,
  config,
  latest,
  inputs,
  isDarwin,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  notificationDriver = import ./notification-driver.nix {
    inherit isDarwin;
    linuxNotificationExecutablePath = "${pkgs.libnotify}/bin/notify-send";
    linuxDesktopFocusExecutablePath = "${pkgs.hyprland}/bin/hyprctl";
  };
  codexTurnNotificationScripts = ./scripts/codex_turn_notification;
  browserMcp = import ../../../agent-harness/agent-instructions/skills/browser/install {
    inherit pkgs homeDir;
    nodejs = pkgs.nodejs_22;
    chromePackage = latest.google-chrome;
  };
  codexDefaultModel = import ./default-model.nix;
  codexConfigTomlFormat = pkgs.formats.toml { };
  codexConfigSeedPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.tomli-w ]);
  mcpServerModule = {
    options = {
      command = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = null;
        description = "Launcher command for a private stdio MCP server.";
      };
      args = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ ];
        description = "Arguments passed to the private stdio MCP server command.";
      };
      environment = lib.mkOption {
        type = lib.types.attrsOf lib.types.str;
        default = { };
        description = "Environment variables passed to the private stdio MCP server.";
      };
      url = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = null;
        description = "Endpoint for a private HTTP MCP server.";
      };
      startupTimeoutSeconds = lib.mkOption {
        type = lib.types.nullOr lib.types.ints.positive;
        default = null;
        description = "Startup timeout for the MCP server.";
      };
      bearerTokenFile = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = null;
        description = "Path to an agenix file whose value becomes the HTTP bearer token.";
      };
    };
  };
  configuredMcpServers = lib.mapAttrs (
    _: server:
    lib.optionalAttrs (server.command != null) {
      inherit (server) command args;
    }
    // lib.optionalAttrs (server.environment != { }) {
      env = server.environment;
    }
    // lib.optionalAttrs (server.url != null) {
      inherit (server) url;
    }
    // lib.optionalAttrs (server.startupTimeoutSeconds != null) {
      startup_timeout_sec = server.startupTimeoutSeconds;
    }
  ) config.codex.mcpServers;
  trustedProjectParentDirectories = [
    "${homeDir}/repo"
  ];
  codexMcpServerBearerTokenFiles = builtins.toJSON (
    lib.mapAttrs (_: server: server.bearerTokenFile) (
      lib.filterAttrs (_: server: server.bearerTokenFile != null) config.codex.mcpServers
    )
  );
  codexConfigSource = codexConfigTomlFormat.generate "codex-config.toml" {
    approval_policy = "never";
    check_for_update_on_startup = false;
    model = codexDefaultModel;
    model_reasoning_effort = "xhigh";
    notify = [
      "${pkgs.python312}/bin/python3"
      "${codexTurnNotificationScripts}/notify.py"
      notificationDriver.platform
      notificationDriver.notificationExecutablePath
      notificationDriver.desktopFocusExecutablePath
      "${herdrPackage}/bin/herdr"
    ];
    sandbox_mode = "danger-full-access";
    suppress_unstable_features_warning = true;
    features = {
      code_mode_host = true;
      hooks = true;
      multi_agent = true;
    };
    tui = {
      alternate_screen = "always";
      animations = false;
      session_picker_view = "dense";
      show_tooltips = false;
      status_line = [
        "git-branch"
        "model-with-reasoning"
        "context-used"
        "weekly-limit"
        "thread-id"
      ];
      status_line_use_colors = true;
      terminal_title = [
        "activity"
        "project-name"
        "git-branch"
      ];
    };
    notice = {
      fast_default_opt_out = true;
      hide_full_access_warning = true;
      hide_gpt5_1_migration_prompt = true;
      hide_rate_limit_model_nudge = true;
      hide_world_writable_warning = true;
    };
    projects = {
      "${homeDir}".trust_level = "trusted";
      "${homeDir}/.dotfiles".trust_level = "trusted";
    };
    mcp_servers = {
      "chrome-devtools" = {
        command = browserMcp.chromeDevtoolsMcpStdioCommand;
        args = browserMcp.chromeDevtoolsMcpStdioArgs;
      };
    }
    // configuredMcpServers;
  };
in
{
  options.codex.mcpServers = lib.mkOption {
    type = lib.types.attrsOf (lib.types.submodule mcpServerModule);
    default = { };
    description = "Private MCP servers merged into the authoritative Codex configuration.";
  };

  config = {
    assertions =
      lib.mapAttrsToList (serverName: server: {
        assertion = (server.command != null) != (server.url != null);
        message = "codex.mcpServers.${serverName} must declare exactly one of command or url";
      }) config.codex.mcpServers
      ++ lib.mapAttrsToList (serverName: server: {
        assertion = server.bearerTokenFile == null || server.url != null;
        message = "codex.mcpServers.${serverName}.bearerTokenFile requires an HTTP url";
      }) config.codex.mcpServers;

    home.file.".codex/config.toml.nix-source".source = codexConfigSource;

    home.activation.seedCodexConfigAsMutableFile = {
      after = [
        "writeBoundary"
        "linkGeneration"
        "agenix"
        "disableAgenixLaunchdRestartLoop"
      ];
      before = [ ];
      data = ''
        export CODEX_CONFIG="$HOME/.codex/config.toml"
        export NIX_SOURCE="$HOME/.codex/config.toml.nix-source"
        export CODEX_TRUSTED_PROJECT_PARENT_DIRECTORIES=${lib.escapeShellArg (lib.concatStringsSep "\n" trustedProjectParentDirectories)}
        export CODEX_MCP_SERVER_BEARER_TOKEN_FILES=${lib.escapeShellArg codexMcpServerBearerTokenFiles}
        ${codexConfigSeedPython}/bin/python3 ${./config/seed_codex_config_mutable.py}
      '';
    };
  };
}

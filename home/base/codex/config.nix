{
  pkgs,
  lib,
  config,
  latest,
  hostname,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  browserMcp = import ../../../agents/skills/browser/install {
    inherit pkgs homeDir;
    nodejs = pkgs.nodejs_22;
    chromePackage = latest.google-chrome;
  };
  codexDefaultModel = "gpt-5.6-sol";
  includeVivaldiDevtoolsMcp = hostname == "chise";
  codexConfigTomlFormat = pkgs.formats.toml { };
  codexConfigSeedPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.tomli-w ]);
  trustedProjectParentDirectories = [
    "${homeDir}/repo"
  ];
  codexConfigSource = codexConfigTomlFormat.generate "codex-config.toml" {
    approval_policy = "never";
    model = codexDefaultModel;
    model_reasoning_effort = "xhigh";
    notify = [
      "notify-send"
      "--app-name"
      "Codex"
    ];
    sandbox_mode = "danger-full-access";
    features = {
      apply_patch_freeform = true;
      child_agents_md = true;
      enable_fanout = true;
      hooks = true;
      multi_agent = true;
      undo = true;
    };
    tui = {
      animations = false;
      session_picker_view = "dense";
      show_tooltips = false;
      status_line = [
        "run-state"
        "git-branch"
        "branch-changes"
        "model-with-reasoning"
        "context-used"
        "five-hour-limit"
        "weekly-limit"
        "permissions"
        "approval-mode"
        "current-dir"
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
    // lib.optionalAttrs includeVivaldiDevtoolsMcp {
      "vivaldi-devtools" = {
        command = browserMcp.vivaldiDevtoolsMcpStdioCommand;
        args = browserMcp.vivaldiDevtoolsMcpStdioArgs;
      };
    };
  };
in
{
  home.file.".codex/config.toml.nix-source".source = codexConfigSource;

  home.activation.seedCodexConfigAsMutableFile = {
    after = [
      "writeBoundary"
      "linkGeneration"
    ];
    before = [ ];
    data = ''
      export CODEX_CONFIG="$HOME/.codex/config.toml"
      export NIX_SOURCE="$HOME/.codex/config.toml.nix-source"
      export CODEX_TRUSTED_PROJECT_PARENT_DIRECTORIES=${lib.escapeShellArg (lib.concatStringsSep "\n" trustedProjectParentDirectories)}
      ${codexConfigSeedPython}/bin/python3 ${./config/seed_codex_config_mutable.py}
    '';
  };
}

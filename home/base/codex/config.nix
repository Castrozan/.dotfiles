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
    tui.show_tooltips = false;
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
      ${pkgs.python3}/bin/python3 ${./config/seed_codex_config_mutable.py}
    '';
  };
}

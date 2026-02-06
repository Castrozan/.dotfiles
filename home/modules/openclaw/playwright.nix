{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.openclaw.skills.playwright;

  # Helper script for agent-browser CLI wrapper
  browser-wrapper = pkgs.writeScriptBin "browser" ''
    #!${pkgs.runtimeShell}
    # Wrapper script for Vercel agent-browser CLI
    # Falls back to playwright MCP if agent-browser not available

    if command -v agent-browser &> /dev/null; then
      exec agent-browser "$@"
    else
      echo "Warning: agent-browser not found. Install with: npm install -g agent-browser" >&2
      echo "Falling back to playwright MCP server..." >&2
      # Could add MCP fallback here
      exit 1
    fi
  '';
in
{
  options.openclaw.skills.playwright = {
    enable = mkEnableOption "Playwright browser automation skill";

    agentBrowser = {
      enable = mkOption {
        type = types.bool;
        default = true;
        description = "Enable Vercel agent-browser installation";
      };

      package = mkOption {
        type = types.package;
        default = pkgs.nodePackages.agent-browser or (pkgs.buildNpmPackage rec {
          pname = "agent-browser";
          version = "latest";
          src = pkgs.fetchFromGitHub {
            owner = "vercel-labs";
            repo = "agent-browser";
            rev = "main";
            hash = lib.fakeHash; # Will need to be updated with actual hash
          };
          npmDepsHash = lib.fakeHash;
          nativeBuildInputs = with pkgs; [ rust cargo ];
        });
        description = "agent-browser package to use";
      };
    };

    playwright = {
      enable = mkOption {
        type = types.bool;
        default = true;
        description = "Enable Playwright MCP server support";
      };

      browsers = mkOption {
        type = types.listOf types.str;
        default = [ "chromium" ];
        description = "Browsers to install (chromium, firefox, webkit)";
      };
    };

    defaultBrowser = mkOption {
      type = types.enum [ "agent-browser" "playwright" ];
      default = "agent-browser";
      description = "Default browser automation backend";
    };
  };

  config = mkIf cfg.enable {
    # Node.js environment for browser automation tools
    home.packages = with pkgs; [
      nodejs_22
      nodePackages.npm
      nodePackages.pnpm
    ] ++ optionals cfg.agentBrowser.enable [
      # Dependencies for agent-browser on Linux
      nss
      nspr
      alsa-lib
      atk
      at-spi2-atk
      at-spi2-core
      cairo
      cups
      dbus
      expat
      gdk-pixbuf
      glib
      gtk3
      libdrm
      libxkbcommon
      mesa
      pango
      xorg.libX11
      xorg.libXcomposite
      xorg.libXdamage
      xorg.libXext
      xorg.libXfixes
      xorg.libXrandr
      xorg.libxcb
      browser-wrapper
    ] ++ optionals cfg.playwright.enable [
      playwright-driver
    ];

    # Environment variables
    home.sessionVariables = {
      PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
      PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";
      # Prefer agent-browser when available
      BROWSER_TOOL = cfg.defaultBrowser;
    } ++ optionalAttrs cfg.agentBrowser.enable {
      # Default session name for agent-browser
      AGENT_BROWSER_SESSION = "default";
    };

    # Shell initialization
    programs.zsh.initExtra = mkIf cfg.agentBrowser.enable ''
      # agent-browser completion (if available)
      if command -v agent-browser &> /dev/null; then
        eval "$(agent-browser completion zsh 2>/dev/null || true)"
      fi
    '';

    programs.bash.initExtra = mkIf cfg.agentBrowser.enable ''
      # agent-browser completion (if available)
      if command -v agent-browser &> /dev/null; then
        eval "$(agent-browser completion bash 2>/dev/null || true)"
      fi
    '';

    # Skill marker file for OpenClaw discovery
    home.file."openclaw/skills/playwright/.enabled" = mkIf cfg.enable {
      text = "enabled";
    };

    # Copy SKILL.md to expected location
    home.file."openclaw/skills/playwright/SKILL.md" = mkIf cfg.enable {
      source = ./../../../agents/openclaw/skills/playwright/SKILL.md;
    };
  };
}

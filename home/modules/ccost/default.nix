{ config, lib, pkgs, ... }:

let
  cfg = config.programs.ccost;
  ccostPackage = pkgs.callPackage ./package.nix { };
in
{
  options.programs.ccost = {
    enable = lib.mkEnableOption "ccost - Claude API cost tracking";

    package = lib.mkOption {
      type = lib.types.package;
      default = ccostPackage;
      description = "The ccost package to use";
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [ cfg.package ];

    home.shellAliases = {
      claude-cost = "ccost";
    };

    # Configuration file
    xdg.configFile."ccost/config.toml".text = lib.generators.toINI {} {
      general = {
        claude_projects_path = "~/.claude/projects";
        cost_mode = "auto";
      };
      currency = {
        default_currency = "USD";
      };
      timezone = {
        timezone = "America/Sao_Paulo";
        daily_cutoff_hour = 0;
      };
      output = {
        colored = true;
        decimal_places = 2;
        date_format = "yyyy-mm-dd";
      };
      pricing = {
        source = "auto"; # Options: static, live, auto
        cache_ttl_minutes = 60;
        offline_fallback = true;
      };
    };
  };
}

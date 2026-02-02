# Declarative patches for openclaw.json.
#
# openclaw.json is app-managed — the gateway, `openclaw configure`, and
# `doctor --fix` all do full JSON overwrites, destroying any inline
# directives. On every nix rebuild, the engine in config-patch.nix applies
# these patches via jq, then writes back atomically. The app can freely
# modify the config between rebuilds; next rebuild re-pins our fields.
#
# Add/remove a pinned field = add/remove one line here.
# Engine details: see config-patch.nix.
{ config, lib, ... }:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;
  isNixOS = builtins.pathExists /etc/NIXOS;
in
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault {
      ".agents.list" = [
        {
          id = openclaw.agent;
          default = true;
          workspace = "${homeDir}/${openclaw.workspacePath}";
        }
      ];
      ".agents.defaults.workspace" = "${homeDir}/${openclaw.workspacePath}";
      ".gateway.port" = openclaw.gatewayPort;
    };

    # agenix secrets only available on NixOS — skip on standalone Home Manager
    openclaw.secretPatches = lib.mkIf isNixOS (lib.mkOptionDefault {
      ".gateway.auth.token" = "/run/agenix/openclaw-gateway-token";
      ".tools.web.search.apiKey" = "/run/agenix/brave-api-key";
    });
  };
}

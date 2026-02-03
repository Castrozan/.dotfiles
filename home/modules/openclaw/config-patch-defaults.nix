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
      ".agents.defaults.model.primary" = "openai-codex/gpt-5.2-codex";
      ".agents.defaults.heartbeat.model" = "openai-codex/gpt-5.1-codex-mini";
      ".agents.defaults.subagents.model" = "openai-codex/gpt-5.1-codex";
      ".agents.defaults.model.fallbacks" = [
        "anthropic/claude-sonnet-4-5"
        "anthropic/claude-opus-4-5"
      ];
      ".agents.defaults.models" = {
        "anthropic/claude-opus-4-5" = {
          alias = "opus";
        };
        "anthropic/claude-sonnet-4-5" = {
          alias = "sonnet";
        };
        "openai-codex/gpt-5.2-codex" = {
          alias = "gpt-5.2-codex";
        };
        "openai-codex/gpt-5.1-codex" = {
          alias = "gpt-5.1-codex";
        };
        "openai-codex/gpt-5.1-codex-mini" = {
          alias = "gpt-5.1-codex-mini";
        };
      };
      ".auth.profiles" = {
        "anthropic:default" = {
          provider = "anthropic";
          mode = "token";
        };
        "openai-codex:default" = {
          provider = "openai-codex";
          mode = "oauth";
        };
      };
      ".agents.defaults.compaction.mode" = "safeguard";
      ".agents.defaults.compaction.memoryFlush.enabled" = true;
      ".gateway.port" = openclaw.gatewayPort;
    };

    # agenix secrets only available on NixOS — skip on standalone Home Manager
    openclaw.secretPatches = lib.mkIf isNixOS (
      lib.mkOptionDefault {
        ".gateway.auth.token" = "/run/agenix/openclaw-gateway-token";
        ".tools.web.search.apiKey" = "/run/agenix/brave-api-key";
      }
    );
  };
}

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

  # Generate agents list from enabled agents
  agentsList = lib.mapAttrsToList (
    name: agent:
    {
      id = name;
      workspace = "${homeDir}/${agent.workspace}";
      model = {
        primary = agent.model.primary;
      }
      // lib.optionalAttrs (agent.model.fallbacks != [ ]) { fallbacks = agent.model.fallbacks; };
    }
    // lib.optionalAttrs (name == openclaw.defaultAgent) { default = true; }
  ) openclaw.enabledAgents;

  # Default workspace for agents.defaults (use default agent's workspace)
  defaultWorkspace =
    if openclaw.defaultAgent != null then
      "${homeDir}/${openclaw.agents.${openclaw.defaultAgent}.workspace}"
    else
      "${homeDir}/openclaw";
in
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault {
      ".agents.list" = agentsList;
      ".agents.defaults.workspace" = defaultWorkspace;
      ".agents.defaults.model.primary" = "openai-codex/gpt-5.2-codex";
      ".agents.defaults.heartbeat.model" = "openai-codex/gpt-5.1-codex-mini";
      ".agents.defaults.subagents.model" = "openai-codex/gpt-5.2-codex";
      ".agents.defaults.model.fallbacks" = [
        "nvidia/moonshotai/kimi-k2.5"
        "openai-codex/gpt-5.2-codex"
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
        "nvidia/moonshotai/kimi-k2.5" = {
          alias = "kimi";
        };
      };
      ".models.mode" = "merge";
      ".models.providers.nvidia" = {
        baseUrl = "https://integrate.api.nvidia.com/v1";
        api = "openai-completions";
        models = [
          {
            id = "moonshotai/kimi-k2.5";
            name = "Kimi K2.5 (NVIDIA NIM)";
          }
        ];
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
        ".models.providers.nvidia.apiKey" = "/run/agenix/nvidia-api-key";
      }
    );
  };
}

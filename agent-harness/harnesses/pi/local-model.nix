{
  modelId,
  contextWindow,
  baseUrl,
}:
{
  config,
  pkgs,
  lib,
  ...
}:
let
  profileDirectory = "${config.home.homeDirectory}/.local/share/pi-local";
  launcher = pkgs.writeShellScriptBin "local-agent" ''
    export PI_CODING_AGENT_DIR=${lib.escapeShellArg profileDirectory}
    ${pkgs.systemd}/bin/systemctl --user start local-language-model.service || exit "$?"
    exec ${config.pi.package}/bin/pi --offline --provider chise --model ${lib.escapeShellArg modelId} --thinking off --no-extensions --no-skills --no-prompt-templates "$@"
  '';
in
{
  imports = [ ./default.nix ];

  config = {
    home.packages = [ launcher ];
    home.file = {
      ".local/bin/local-agent".source = "${launcher}/bin/local-agent";
      ".local/share/pi-local/AGENTS.md".text = config.home.file.".pi/agent/AGENTS.md".text;
      ".local/share/pi-local/models.json".text = builtins.toJSON {
        providers.chise = {
          inherit baseUrl;
          api = "openai-completions";
          apiKey = "local";
          compat = {
            supportsDeveloperRole = false;
            supportsReasoningEffort = false;
            supportsStore = false;
            maxTokensField = "max_tokens";
          };
          models = [
            {
              id = modelId;
              name = "Qwen3.5-4B Uncensored (Chise)";
              inherit contextWindow;
              maxTokens = 2048;
              reasoning = false;
              input = [ "text" ];
            }
          ];
        };
      };
      ".local/share/pi-local/settings.json".text = builtins.toJSON {
        defaultProvider = "chise";
        defaultModel = modelId;
        defaultThinkingLevel = "off";
        compaction = {
          enabled = true;
          reserveTokens = 7168;
          keepRecentTokens = 1024;
        };
      };
    };
  };
}

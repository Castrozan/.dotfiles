{
  modelId,
  contextWindow,
  baseUrl,
  healthUrl,
}:
{
  config,
  pkgs,
  lib,
  ...
}:
let
  profileDirectory = ".local/share/pi-local";
  launcher = pkgs.writeShellScriptBin "local-agent" (
    lib.replaceStrings
      [
        "@profileDirectory@"
        "@systemctl@"
        "@curl@"
        "@pi@"
        "@modelId@"
        "@healthUrl@"
      ]
      [
        (lib.escapeShellArg "${config.home.homeDirectory}/${profileDirectory}")
        "${pkgs.systemd}/bin/systemctl"
        "${pkgs.curl}/bin/curl"
        "${config.pi.package}/bin/pi"
        (lib.escapeShellArg modelId)
        (lib.escapeShellArg healthUrl)
      ]
      (builtins.readFile ./scripts/local-agent.sh)
  );
in
{
  imports = [
    ./default.nix
    (import ./plugins.nix { inherit profileDirectory; })
  ];

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

{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../ollama-home-manager.nix ];

  localModelModule =
    isNixOS:
    {
      pkgs,
      config,
      latest,
      lib,
      ...
    }:
    import ../llama-cpp-home-manager.nix {
      inherit
        pkgs
        config
        latest
        lib
        isNixOS
        ;
    };
  localModel = helpers.homeManagerTestConfiguration [ (localModelModule true) ];
  darwinLocalModel = helpers.homeManagerTestConfigurationForDarwin [ (localModelModule false) ];
  localModelService = localModel.systemd.user.services.local-language-model.Service;
  localAgentModels = builtins.fromJSON localModel.home.file.".local/share/pi-local/models.json".text;
  localAgentSettings =
    builtins.fromJSON
      localModel.home.file.".local/share/pi-local/settings.json".text;

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
in
{
  domain-ollama-service-binary = mkEvalCheck "domain-ollama-service-binary" (
    hasService "ollama" && hasFile ".local/bin/ollama"
  ) "ollama should have service and binary";

  domain-local-model-loopback = mkEvalCheck "domain-local-model-loopback" (
    lib.hasInfix "--host 127.0.0.1" (lib.concatStringsSep " " localModelService.ExecStart)
    && lib.hasInfix "--parallel 1" (lib.concatStringsSep " " localModelService.ExecStart)
    && localModelService.MemoryMax == "6G"
  ) "local inference must stay on loopback with bounded concurrency and memory";

  domain-local-agent-model-contract = mkEvalCheck "domain-local-agent-model-contract" (
    localAgentModels.providers.chise.baseUrl == "http://127.0.0.1:8081/v1"
    && (builtins.head localAgentModels.providers.chise.models).id == "qwen3.5-4b-uncensored"
    && (builtins.head localAgentModels.providers.chise.models).contextWindow == 16384
    && localAgentSettings.compaction.reserveTokens < 16384
    && localAgentSettings.compaction.keepRecentTokens < 16384
  ) "the local agent must use the local endpoint and fit its context budget";

  domain-local-agent-shared-assets = mkEvalCheck "domain-local-agent-shared-assets" (
    builtins.all
      (
        path:
        localModel.home.file.".local/share/pi-local/${path}".source
        == localModel.home.file.".pi/agent/${path}".source
      )
      [
        "plugins/dotfiles"
        "extensions/agent-plugins"
        "extensions/mcp-adapter"
      ]
    && builtins.hasAttr "registerProductionPiPlugin-.local/share/pi-local" localModel.home.activation
    && builtins.hasAttr "registerProductionPiPlugin-.pi/agent" localModel.home.activation
  ) "both Pi profiles must receive and register the same shared plugin and native loaders";

  domain-local-model-linux-only = mkEvalCheck "domain-local-model-linux-only" (
    !(builtins.hasAttr "local-language-model" darwinLocalModel.systemd.user.services)
    && !(builtins.hasAttr ".local/bin/local-agent" darwinLocalModel.home.file)
  ) "the Chise inference service and launcher must not deploy on Darwin";

  domain-local-agent-compacts-before-output-starvation =
    mkEvalCheck "domain-local-agent-compacts-before-output-starvation"
      (
        localAgentSettings.compaction.reserveTokens
        >= 4096 + (builtins.head localAgentModels.providers.chise.models).maxTokens + 1024
      )
      "compaction must leave Pi's safety margin, the full response budget, and room for the next message";
}

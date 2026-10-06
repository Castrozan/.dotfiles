{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../ollama-home-manager.nix ];

  localModelModule =
    isNixOS:
    arguments@{
      pkgs,
      config,
      latest,
      lib,
      ...
    }:
    import ../llama-cpp-home-manager.nix (
      arguments
      // {
        inherit isNixOS;
      }
    );
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

  domain-local-model-linux-only = mkEvalCheck "domain-local-model-linux-only" (
    !(builtins.hasAttr "local-language-model" darwinLocalModel.systemd.user.services)
    && !(builtins.hasAttr ".local/bin/local-agent" darwinLocalModel.home.file)
  ) "the Chise inference service and launcher must not deploy on Darwin";
}

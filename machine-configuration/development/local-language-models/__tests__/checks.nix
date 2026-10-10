{
  helpers,
  lib,
  pkgs,
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
  localModelUnit = localModel.systemd.user.services.local-language-model.Unit;
  localModelSocket = localModel.systemd.user.sockets.local-language-model;
  localModelProxy = localModel.systemd.user.services.local-language-model-proxy;
  localInferencePackage = lib.findFirst (
    package: (package.pname or "") == "llama-cpp"
  ) (throw "local inference package is missing") localModel.home.packages;
  localTokenizerPackage = localInferencePackage.override {
    cudaSupport = false;
    blasSupport = false;
  };
  tokenizerVocabulary = pkgs.fetchurl {
    url = "https://raw.githubusercontent.com/ggml-org/llama.cpp/42532afff43910e619a650c1704525b3acbbec5a/models/ggml-vocab-qwen35.gguf";
    hash = "sha256-Y+2VL/M4mWzwvfJKexABUSQnP3XG3Ju0JzVqo/Z+xiw=";
  };
  localAgentModels = builtins.fromJSON localModel.home.file.".local/share/pi-local/models.json".text;
  localAgentSettings =
    builtins.fromJSON
      localModel.home.file.".local/share/pi-local/settings.json".text;

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
in
{
  domain-local-agent-workflow-configurations =
    pkgs.runCommand "domain-local-agent-workflow-configurations" { }
      ''
        ${pkgs.jq}/bin/jq -se 'length == 1 and .[0].repeatFrequencyThreshold == 6' \
          ${localModel.home.file.".pi/loop-guard.json".source}
        touch "$out"
      '';

  domain-ollama-service-binary = mkEvalCheck "domain-ollama-service-binary" (
    hasService "ollama" && hasFile ".local/bin/ollama"
  ) "ollama should have service and binary";

  domain-local-model-loopback = mkEvalCheck "domain-local-model-loopback" (
    lib.hasInfix "--host 127.0.0.1" (lib.concatStringsSep " " localModelService.ExecStart)
    && lib.hasInfix "--parallel 1" (lib.concatStringsSep " " localModelService.ExecStart)
    && localModelService.MemoryMax == "6G"
  ) "local inference must stay on loopback with bounded concurrency and memory";

  domain-local-model-demand-lifecycle =
    mkEvalCheck "domain-local-model-demand-lifecycle"
      (
        localModelUnit.StopWhenUnneeded
        && (localModel.systemd.user.services.local-language-model.Install.WantedBy or [ ]) == [ ]
        && localModelSocket.Socket.ListenStream == "127.0.0.1:8081"
        && localModelSocket.Socket.Service == "local-language-model-proxy.service"
        && localModelSocket.Install.WantedBy == [ "sockets.target" ]
        && lib.elem "local-language-model.service" localModelProxy.Unit.Requires
        && lib.elem "local-language-model.service" localModelProxy.Unit.After
        && lib.elem "local-language-model.socket" localModelProxy.Service.Sockets
        && lib.hasInfix "--exit-idle-time=300 127.0.0.1:8082" (
          lib.concatStringsSep " " localModelProxy.Service.ExecStart
        )
        && lib.hasInfix "--port 8082" (lib.concatStringsSep " " localModelService.ExecStart)
        && lib.hasInfix "http://127.0.0.1:8082/health" localModelService.ExecStartPost
        && (localModelProxy.Install.WantedBy or [ ]) == [ ]
        && localModelService.TimeoutStartSec == 180
        && localModelService.TimeoutStopSec == 30
      )
      "only the loopback socket starts at boot; the proxy owns inference readiness and releases the backend after idle";

  domain-local-agent-model-contract = mkEvalCheck "domain-local-agent-model-contract" (
    localAgentModels.providers.chise.baseUrl == "http://127.0.0.1:8081/v1"
    && (builtins.head localAgentModels.providers.chise.models).id == "qwen3.5-4b-uncensored"
    && (builtins.head localAgentModels.providers.chise.models).contextWindow == 24576
    && lib.hasInfix "--ctx-size 24576" (lib.concatStringsSep " " localModelService.ExecStart)
    && localAgentSettings.compaction.reserveTokens < 24576
    && localAgentSettings.compaction.keepRecentTokens < 24576
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
    && !(builtins.hasAttr "local-language-model-proxy" darwinLocalModel.systemd.user.services)
    && !(builtins.hasAttr "local-language-model" darwinLocalModel.systemd.user.sockets)
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
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  domain-local-model-socket-proxy-lifecycle =
    pkgs.runCommand "domain-local-model-socket-proxy-lifecycle" { }
      ''
        ${pkgs.python3}/bin/python ${./verify-socket-proxy.py} \
          ${pkgs.systemd}/lib/systemd/systemd-socket-proxyd
        touch "$out"
      '';

  domain-local-model-tokenizer-long-input =
    pkgs.runCommand "domain-local-model-tokenizer-long-input" { }
      ''
        ${pkgs.python3}/bin/python ${./verify-tokenizer.py} \
          ${localTokenizerPackage}/bin/llama-tokenize \
          ${tokenizerVocabulary}
        touch "$out"
      '';
}

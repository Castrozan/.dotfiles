{
  config,
  pkgs,
  latest,
  lib,
  isNixOS,
  ...
}:
let
  modelId = "rhea-4b-coding-max";
  modelName = "Rhea 4B Coding Max (Chise)";
  contextWindow = 24576;
  listenPort = 8081;
  inferencePackage = (latest.llama-cpp.override { vulkanSupport = true; }).overrideAttrs (previous: {
    patches = (previous.patches or [ ]) ++ [
      (pkgs.fetchpatch {
        url = "https://github.com/ggml-org/llama.cpp/commit/42532afff43910e619a650c1704525b3acbbec5a.patch";
        includes = [ "src/unicode.cpp" ];
        hash = "sha256-jOqh65x8gZy0QBi+ZX1JQVSpLMm2RNaIX0BPO1/GQ+k=";
      })
    ];
  });
  modelWeights = pkgs.fetchurl {
    name = "rhea-4b-coding-max-q4_k_m.gguf";
    url = "https://huggingface.co/mradermacher/Rhea-4B-Coding-max-i1-GGUF/resolve/071e023294b73363aaacda8d0f9abad41ff7d334/Rhea-4B-Coding-max.i1-Q4_K_M.gguf";
    sha256 = "724d850de5666f7dead176a3c617afa6dcd175fc36cc04be1a3dda3e5564d99d";
  };
  tokenizerConfiguration = pkgs.fetchurl {
    url = "https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507/resolve/768f209d9ea81521153ed38c47d515654e938aea/tokenizer_config.json";
    sha256 = "60adcfc35f5f251e19a196ec977b4ca0fcfb534852911b3196d68d5e3b146aa0";
  };
  modelPython = pkgs.python312.withPackages (packages: [ packages.gguf ]);
  model = pkgs.runCommand "rhea-4b-coding-max-agent.gguf" { } ''
    ${modelPython}/bin/python ${./scripts/materialize_rhea_model.py} \
      ${modelWeights} ${tokenizerConfiguration} "$out"
  '';
  serverArguments = [
    "--model"
    "${model}"
    "--alias"
    modelId
    "--host"
    "127.0.0.1"
    "--port"
    (toString listenPort)
    "--device"
    "Vulkan1"
    "--gpu-layers"
    "all"
    "--ctx-size"
    (toString contextWindow)
    "--parallel"
    "1"
    "--cache-ram"
    "0"
    "--threads"
    "4"
    "--threads-http"
    "2"
    "--batch-size"
    "256"
    "--ubatch-size"
    "128"
    "--flash-attn"
    "on"
    "--cache-type-k"
    "q4_0"
    "--cache-type-v"
    "q4_0"
    "--jinja"
    "--reasoning"
    "on"
    "--reasoning-budget"
    "256"
    "--temp"
    "0.4"
    "--top-p"
    "0.8"
    "--top-k"
    "20"
    "--min-p"
    "0"
    "--sleep-idle-seconds"
    "300"
  ];
in
{
  imports = lib.optionals isNixOS [
    (import ../../../agent-harness/harnesses/pi/local-model.nix {
      inherit modelId modelName contextWindow;
      baseUrl = "http://127.0.0.1:${toString listenPort}/v1";
    })
  ];

  config = lib.mkIf isNixOS {
    home.packages = [ inferencePackage ];

    systemd.user.services.local-language-model = {
      Unit = {
        Description = "Local Rhea 4B uncensored coding inference";
        StartLimitIntervalSec = 300;
        StartLimitBurst = 3;
      };
      Service = {
        Type = "exec";
        ExecStart = "${inferencePackage}/bin/llama-server ${lib.escapeShellArgs serverArguments}";
        ExecStartPost = "${pkgs.curl}/bin/curl --fail --silent --retry 60 --retry-all-errors --retry-delay 1 --max-time 2 http://127.0.0.1:${toString listenPort}/health";
        Restart = "on-failure";
        RestartSec = 10;
        TimeoutStartSec = 180;
        MemoryHigh = "4G";
        MemoryMax = "6G";
        CPUQuota = "400%";
        Nice = 10;
        NoNewPrivileges = true;
        WorkingDirectory = config.home.homeDirectory;
      };
      Install.WantedBy = [ "default.target" ];
    };
  };
}

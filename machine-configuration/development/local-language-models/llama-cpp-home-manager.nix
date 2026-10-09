{
  config,
  pkgs,
  latest,
  lib,
  isNixOS,
  ...
}:
let
  modelId = "qwen3.5-4b-uncensored";
  contextWindow = 24576;
  listenPort = 8081;
  backendPort = 8082;
  inferencePackage =
    (latest.llama-cpp.override {
      cudaSupport = true;
      cudaPackages = latest.cudaPackages_12_9;
      vulkanSupport = false;
    }).overrideAttrs
      (previous: {
        cmakeFlags = (previous.cmakeFlags or [ ]) ++ [ "-DCMAKE_CUDA_ARCHITECTURES=86-real" ];
        patches = (previous.patches or [ ]) ++ [
          (pkgs.fetchpatch {
            url = "https://github.com/ggml-org/llama.cpp/commit/42532afff43910e619a650c1704525b3acbbec5a.patch";
            includes = [ "src/unicode.cpp" ];
            hash = "sha256-jOqh65x8gZy0QBi+ZX1JQVSpLMm2RNaIX0BPO1/GQ+k=";
          })
        ];
      });
  model = pkgs.fetchurl {
    name = "qwen3.5-4b-uncensored-q4_k_m.gguf";
    url = "https://huggingface.co/HauhauCS/Qwen3.5-4B-Uncensored-HauhauCS-Aggressive/resolve/c09cdbcdb1fefad6d335809d445621b5f5ba0c6e/Qwen3.5-4B-Uncensored-HauhauCS-Aggressive-Q4_K_M.gguf";
    sha256 = "79e28ecacf84e75b6056cf4059636d435aa9eb67795780f7b7dbc7d32a962741";
  };
  serverArguments = [
    "--model"
    "${model}"
    "--alias"
    modelId
    "--host"
    "127.0.0.1"
    "--port"
    (toString backendPort)
    "--device"
    "CUDA0"
    "--gpu-layers"
    "all"
    "--ctx-size"
    (toString contextWindow)
    "--parallel"
    "1"
    "--cache-ram"
    "0"
    "--ctx-checkpoints"
    "16"
    "--threads"
    "4"
    "--threads-http"
    "2"
    "--batch-size"
    "512"
    "--ubatch-size"
    "256"
    "--flash-attn"
    "on"
    "--cache-type-k"
    "q8_0"
    "--cache-type-v"
    "q8_0"
    "--jinja"
    "--reasoning"
    "off"
    "--temp"
    "0.7"
    "--top-p"
    "0.8"
    "--top-k"
    "20"
    "--min-p"
    "0"
    "--sleep-idle-seconds"
    "-1"
  ];
in
{
  imports = lib.optionals isNixOS [
    (import ../../../agent-harness/harnesses/pi/local-model.nix {
      inherit modelId contextWindow;
      baseUrl = "http://127.0.0.1:${toString listenPort}/v1";
      healthUrl = "http://127.0.0.1:${toString listenPort}/health";
    })
  ];

  config = lib.mkIf isNixOS {
    home.packages = [ inferencePackage ];

    systemd.user.services.local-language-model = {
      Unit = {
        Description = "Local Qwen3.5-4B uncensored inference";
        StartLimitIntervalSec = 300;
        StartLimitBurst = 3;
        StopWhenUnneeded = true;
      };
      Service = {
        Type = "exec";
        ExecStart = "${inferencePackage}/bin/llama-server ${lib.escapeShellArgs serverArguments}";
        ExecStartPost = "${pkgs.curl}/bin/curl --fail --silent --retry 60 --retry-all-errors --retry-delay 1 --max-time 2 http://127.0.0.1:${toString backendPort}/health";
        Restart = "on-failure";
        RestartSec = 10;
        TimeoutStartSec = 180;
        TimeoutStopSec = 30;
        MemoryHigh = "4G";
        MemoryMax = "6G";
        CPUQuota = "400%";
        Nice = 10;
        NoNewPrivileges = true;
        WorkingDirectory = config.home.homeDirectory;
      };
    };

    systemd.user.sockets.local-language-model = {
      Unit.Description = "Local inference on-demand listener";
      Socket = {
        ListenStream = "127.0.0.1:${toString listenPort}";
        Service = "local-language-model-proxy.service";
        NoDelay = true;
      };
      Install.WantedBy = [ "sockets.target" ];
    };

    systemd.user.services.local-language-model-proxy = {
      Unit = {
        Description = "Local inference demand and idle shutdown";
        Requires = [
          "local-language-model.service"
          "local-language-model.socket"
        ];
        After = [
          "local-language-model.service"
          "local-language-model.socket"
        ];
      };
      Service = {
        Type = "notify";
        Sockets = [ "local-language-model.socket" ];
        ExecStart = "${pkgs.systemd}/lib/systemd/systemd-socket-proxyd --exit-idle-time=300 127.0.0.1:${toString backendPort}";
        NoNewPrivileges = true;
      };
    };
  };
}

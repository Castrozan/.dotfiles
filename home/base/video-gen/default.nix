{
  pkgs,
  lib,
  unstable,
  ...
}:
let
  accelerateWithoutSandboxFlakyChecks =
    unstable.python312Packages.accelerate.overridePythonAttrs
      (_: {
        doCheck = false;
        dontUsePythonImportsCheck = true;
      });

  videoGenerationPythonEnvironment = unstable.python312.withPackages (pythonPackages: [
    pythonPackages.torch
    pythonPackages.torchvision
    pythonPackages.diffusers
    pythonPackages.transformers
    accelerateWithoutSandboxFlakyChecks
    pythonPackages.huggingface-hub
    pythonPackages.safetensors
    pythonPackages.sentencepiece
    pythonPackages.protobuf
    pythonPackages.einops
    pythonPackages.ftfy
    pythonPackages.numpy
    pythonPackages.pillow
  ]);

  videoGeneratorPackageRoot = lib.fileset.toSource {
    root = ./.;
    fileset = ./generate_video;
  };

  videoGenerationCommand = pkgs.writeShellScriptBin "video-gen" ''
    export PYTORCH_ENABLE_MPS_FALLBACK="''${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
    export TOKENIZERS_PARALLELISM="''${TOKENIZERS_PARALLELISM:-false}"
    export PATH="${pkgs.ffmpeg}/bin:$PATH"
    export PYTHONPATH="${videoGeneratorPackageRoot}''${PYTHONPATH:+:$PYTHONPATH}"
    exec ${videoGenerationPythonEnvironment}/bin/python -m generate_video "$@"
  '';
in
{
  home.packages = [ videoGenerationCommand ];
}

{
  pkgs,
  lib,
  ...
}:
let
  videoGenerationPythonEnvironment = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.torch
    pythonPackages.torchvision
    pythonPackages.diffusers
    pythonPackages.transformers
    pythonPackages.accelerate
    pythonPackages.huggingface-hub
    pythonPackages.safetensors
    pythonPackages.sentencepiece
    pythonPackages.protobuf
    pythonPackages.imageio
    pythonPackages.imageio-ffmpeg
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
    export PYTHONPATH="${videoGeneratorPackageRoot}''${PYTHONPATH:+:$PYTHONPATH}"
    exec ${videoGenerationPythonEnvironment}/bin/python -m generate_video "$@"
  '';
in
{
  home.packages = [ videoGenerationCommand ];
}

{
  pkgs,
  lib,
  unstable,
  ...
}:
let
  disableChecks =
    pythonPackage:
    pythonPackage.overridePythonAttrs (_: {
      doCheck = false;
      doInstallCheck = false;
      dontUsePythonImportsCheck = true;
    });

  useOfficialWheelWithoutBrokenDepCheck =
    pythonPackage:
    pythonPackage.overridePythonAttrs (previousAttributes: {
      dontCheckRuntimeDeps = true;
      dependencies = (previousAttributes.dependencies or [ ]) ++ [ unstable.python312Packages.fsspec ];
    });

  videoGenerationPython = unstable.python312.override {
    packageOverrides = finalPythonPackages: previousPythonPackages: {
      torch-bin = useOfficialWheelWithoutBrokenDepCheck previousPythonPackages.torch-bin;
      torchvision-bin = useOfficialWheelWithoutBrokenDepCheck previousPythonPackages.torchvision-bin;
      torch = finalPythonPackages.torch-bin;
      torchvision = finalPythonPackages.torchvision-bin;
      accelerate = disableChecks previousPythonPackages.accelerate;
      diffusers = disableChecks previousPythonPackages.diffusers;
      transformers = disableChecks previousPythonPackages.transformers;
      safetensors = disableChecks previousPythonPackages.safetensors;
      einops = disableChecks previousPythonPackages.einops;
      tensorboard = disableChecks previousPythonPackages.tensorboard;
    };
  };

  videoGenerationPythonEnvironment = videoGenerationPython.withPackages (pythonPackages: [
    pythonPackages.torch
    pythonPackages.torchvision
    pythonPackages.diffusers
    pythonPackages.transformers
    pythonPackages.accelerate
    pythonPackages.huggingface-hub
    pythonPackages.safetensors
    pythonPackages.sentencepiece
    pythonPackages.protobuf
    pythonPackages.av
    pythonPackages.fsspec
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

pythonPackages:
let
  espeakngLoader = pythonPackages.callPackage ./espeakng-loader-python-package.nix { };
  phonemizer = pythonPackages.callPackage ./phonemizer-python-package.nix { };
  kokoroOnnx = pythonPackages.callPackage ./kokoro-onnx-python-package.nix {
    espeakng-loader = espeakngLoader;
    inherit phonemizer;
  };
in
[
  kokoroOnnx
  pythonPackages.elevenlabs
]

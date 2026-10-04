{
  buildPythonPackage,
  fetchPypi,
  hatchling,
  numpy,
  onnxruntime,
  phonemizer,
  espeakng-loader,
}:
buildPythonPackage rec {
  pname = "kokoro-onnx";
  version = "0.6.1";
  pyproject = true;
  src = fetchPypi {
    pname = "kokoro_onnx";
    inherit version;
    hash = "sha256-e722bdU3dfcQiKmZmamu/a0kB0Da9UywlBDYux4pTjU=";
  };
  build-system = [ hatchling ];
  dependencies = [
    numpy
    onnxruntime
    phonemizer
    espeakng-loader
  ];
  pythonImportsCheck = [ "kokoro_onnx" ];
}

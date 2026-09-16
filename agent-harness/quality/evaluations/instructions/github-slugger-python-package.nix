{
  buildPythonPackage,
  fetchPypi,
}:
buildPythonPackage rec {
  pname = "github-slugger";
  version = "0.0.3";
  format = "wheel";

  src = fetchPypi {
    pname = "github_slugger";
    inherit version format;
    dist = "py3";
    python = "py3";
    hash = "sha256-LVMf8OQ5dikAvw7DvhB3Gx02NabUSGET8TUvoZwJGpE=";
  };

  pythonImportsCheck = [ "github_slugger" ];
}

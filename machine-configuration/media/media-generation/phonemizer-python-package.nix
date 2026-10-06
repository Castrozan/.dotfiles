{
  buildPythonPackage,
  fetchPypi,
  setuptools,
  joblib,
  attrs,
  dlinfo,
  segments,
  typing-extensions,
  stdenv,
}:
let
  platformDlinfo =
    if stdenv.hostPlatform.isDarwin then
      dlinfo.overrideAttrs (previous: {
        disabledTestPaths = (previous.disabledTestPaths or [ ]) ++ [ "tests/dlinfo_glibc_test.py" ];
        meta = previous.meta // {
          broken = false;
        };
      })
    else
      dlinfo;
in
buildPythonPackage rec {
  pname = "phonemizer";
  version = "3.4.0";
  pyproject = true;
  src = fetchPypi {
    inherit pname version;
    hash = "sha256-4TIxmAxQvGcewEZjeboCcmCtnWGSmVLYrpZls9DyUes=";
  };
  build-system = [ setuptools ];
  dependencies = [
    joblib
    attrs
    platformDlinfo
    segments
    typing-extensions
  ];
  pythonImportsCheck = [ "phonemizer" ];
}

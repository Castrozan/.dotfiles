{
  buildPythonPackage,
  fetchurl,
  stdenv,
}:
let
  wheels = {
    aarch64-darwin = {
      url = "https://files.pythonhosted.org/packages/a8/26/258c0cd43b9bc1043301c5f61767d6a6c3b679df82790c9cb43a3277b865/espeakng_loader-0.2.4-py3-none-macosx_11_0_arm64.whl";
      hash = "sha256-0nzcoxESIm5ymdhWLoidPjih5IBVye44G0XWaQcu5Z8=";
    };
    x86_64-darwin = {
      url = "https://files.pythonhosted.org/packages/f8/92/f44ed7f531143c3c6c97d56e2b0f9be8728dc05e18b96d46eb539230ed46/espeakng_loader-0.2.4-py3-none-macosx_10_12_x86_64.whl";
      hash = "sha256-t3R3ri3fYqdI4E5JcU6rsvOiTzRBZiALAFOQg71mmQQ=";
    };
    x86_64-linux = {
      url = "https://files.pythonhosted.org/packages/de/1e/25ec5ab07528c0fbb215a61800a38eca05c8a99445515a02d7fa5debcb32/espeakng_loader-0.2.4-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl";
      hash = "sha256-CHIbryfRPUYfa+bu2aZSd+cNaCNP9IT9i5iXsiLNy20=";
    };
    aarch64-linux = {
      url = "https://files.pythonhosted.org/packages/d9/ad/1b768d8daffc2996e07bbcb6f534d8de3202cd75fce1f1c45eced1ce6465/espeakng_loader-0.2.4-py3-none-manylinux_2_28_aarch64.whl";
      hash = "sha256-0eeYFBtGoFDNt1/PPBfblpuyxAOU8/SkiRBlXVR1CLk=";
    };
  };
in
buildPythonPackage {
  pname = "espeakng-loader";
  version = "0.2.4";
  format = "wheel";
  src = fetchurl wheels.${stdenv.hostPlatform.system};
  pythonImportsCheck = [ "espeakng_loader" ];
}

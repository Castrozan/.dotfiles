{
  lib,
  rustPlatform,
  fetchFromGitHub,
  pkg-config,
  sqlite,
}:

rustPlatform.buildRustPackage rec {
  pname = "ccost";
  version = "0.2.0";

  src = fetchFromGitHub {
    owner = "carlosarraes";
    repo = "ccost";
    rev = "d2149d94f72cab3370b723a863c71bdb6e50d9d2";
    hash = "sha256-7aNk1o5M3kKZPSx+dkk/H2Bl1sJ52AlJOCyW0844aho=";
  };

  cargoHash = "sha256-NwOv2CeXn2TRp3DfCtnL2SXrsGlBtKHIZfQy8+RpcS8=";

  nativeBuildInputs = [
    pkg-config
  ];

  buildInputs = [
    sqlite
  ];

  meta = with lib; {
    description = "Accurate Claude API usage tracking and cost analysis tool";
    homepage = "https://github.com/carlosarraes/ccost";
    license = licenses.mit;
    maintainers = [ ];
    mainProgram = "ccost";
  };
}

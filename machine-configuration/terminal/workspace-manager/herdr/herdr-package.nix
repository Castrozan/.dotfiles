{ pkgs, inputs }:
inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default.overrideAttrs (previous: {
  patches = (previous.patches or [ ]) ++ [
    ./patches/selection-action.patch
    ./patches/navigator-current-workspace.patch
  ];
  postPatch = (previous.postPatch or "") + ''
    mkdir -p tests
    cp -r ${inputs.herdr}/tests/fixtures tests/fixtures
    cp ${inputs.herdr}/distribution/latest.json distribution/latest.json
  '';
  doCheck = true;
  cargoTestFlags = [
    "--bin"
    "herdr"
    "navigator"
  ];
})

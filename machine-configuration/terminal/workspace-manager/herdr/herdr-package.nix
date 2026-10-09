{ pkgs, inputs }:
inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default.overrideAttrs (previous: {
  patches = (previous.patches or [ ]) ++ [
    ./patches/selection-action.patch
    ./patches/navigator-current-workspace.patch
    ./patches/agent-exit-pane-cleanup.patch
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
  postCheck = (previous.postCheck or "") + ''
    cargo test --offline --locked --release --jobs 1 \
      --target ${pkgs.stdenv.hostPlatform.rust.rustcTarget} \
      --bin herdr app::api::agent_lifecycle::tests -- --test-threads=1
  '';
})

{ pkgs }:
let
  patchedUpstreamVersion = "1.4.5";
in
pkgs.btop.overrideAttrs (previousAttributes: {
  version = patchedUpstreamVersion;
  src = pkgs.fetchFromGitHub {
    owner = "aristocratos";
    repo = "btop";
    tag = "v${patchedUpstreamVersion}";
    hash = "sha256-ZLT+Hc1rvBFyhey+imbgGzSH/QaVxIh/jvDKVSmDrA0=";
  };
  patches = (previousAttributes.patches or [ ]) ++ [
    ./patches/memory-totals.patch
    ./patches/system-process-group.patch
  ];
  postPatch = (previousAttributes.postPatch or "") + ''
    cp ${./system-process-group.hpp} src/btop_system_process_group.hpp
  '';
})

{ pkgs }:
pkgs.btop.overrideAttrs (previousAttributes: {
  patches = (previousAttributes.patches or [ ]) ++ [
    ./patches/memory-totals.patch
    ./patches/system-process-group.patch
  ];
  postPatch = (previousAttributes.postPatch or "") + ''
    cp ${./system-process-group.hpp} src/btop_system_process_group.hpp
  '';
})

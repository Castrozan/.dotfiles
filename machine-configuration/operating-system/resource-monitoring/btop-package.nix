{ pkgs }:
pkgs.btop.overrideAttrs (previousAttributes: {
  patches = (previousAttributes.patches or [ ]) ++ [ ./patches/memory-totals.patch ];
})

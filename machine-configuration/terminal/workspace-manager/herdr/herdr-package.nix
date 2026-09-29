{ pkgs, inputs }:
inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default.overrideAttrs (previous: {
  patches = (previous.patches or [ ]) ++ [ ./patches/selection-action.patch ];
})

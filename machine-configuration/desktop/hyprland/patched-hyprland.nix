{ pkgs, inputs }:
let
  hyprlandPackages = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
in
hyprlandPackages.hyprland.overrideAttrs (previousAttrs: {
  patches = (previousAttrs.patches or [ ]) ++ [
    ./hyprland-patches/fix-layershell-keyboard-focus-restore.patch
  ];
})

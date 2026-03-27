{ pkgs, inputs, ... }:
let
  opencodeFromFlakeInput = inputs.opencode.packages.${pkgs.stdenv.hostPlatform.system}.default;

  opencodeWithPatchedShebangs = opencodeFromFlakeInput.overrideAttrs (previousAttrs: {
    postConfigure = ''
      ${previousAttrs.postConfigure or ""}
      patchShebangs .
    '';
  });

  opencode = pkgs.writeShellScriptBin "opencode" ''
    exec ${opencodeWithPatchedShebangs}/bin/opencode "$@" 2> >(grep -v "^INFO" >&2)
  '';
in
{
  home.packages = [ opencode ];
}

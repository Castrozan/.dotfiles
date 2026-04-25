{ pkgs, inputs, ... }:
# TODO: opencode v1.3.8 has stale bun lockfile upstream — re-enable when fixed
# let
#   opencodeFromFlakeInput = inputs.opencode.packages.${pkgs.stdenv.hostPlatform.system}.default;
#
#   opencodeWithPatchedShebangs = opencodeFromFlakeInput.overrideAttrs (previousAttrs: {
#     nativeBuildInputs = previousAttrs.nativeBuildInputs ++ [ pkgs.nodejs ];
#     postConfigure = ''
#       ${previousAttrs.postConfigure or ""}
#       patchShebangs .
#     '';
#   });
#
#   opencode = pkgs.writeShellScriptBin "opencode" ''
#     exec ${opencodeWithPatchedShebangs}/bin/opencode "$@" 2> >(grep -v "^INFO" >&2)
#   '';
# in
{
  home.packages = [ ];
}

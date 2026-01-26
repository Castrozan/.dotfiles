{ pkgs, inputs, ... }:
let
  opencode-unwrapped = inputs.opencode.packages.${pkgs.stdenv.hostPlatform.system}.default;

  # Wrapper to filter noisy INFO logs
  opencode = pkgs.writeShellScriptBin "opencode" ''
    exec ${opencode-unwrapped}/bin/opencode "$@" 2> >(grep -v "^INFO" >&2)
  '';
in
{
  home.packages = [ opencode ];
}

{
  pkgs,
  lib,
  helpers,
  ...
}:
let
  hooks = import ../. {
    inherit pkgs lib;
    hostname = "test";
  };
  rulesync = import ../../package.nix { inherit pkgs; };
  missingPrivateConfiguration = builtins.tryEval (
    builtins.toJSON (
      import ../source.nix {
        inherit pkgs lib;
        hostname = "test";
        isDarwin = true;
        privateConfigRoot = "/nonexistent/private-configuration";
      }
    )
  );
in
{
  rulesync-hook-generation-contract = pkgs.runCommand "rulesync-hook-generation-contract" { } ''
    ${pkgs.python312}/bin/python3 ${./verify_generation.py} ${../build_hooks.py} ${hooks.source} ${rulesync}/bin/rulesync
    touch "$out"
  '';
  rulesync-hooks-require-darwin-private-allowlists =
    helpers.mkEvalCheck "rulesync-hooks-require-darwin-private-allowlists"
      (!missingPrivateConfiguration.success)
      "Rulesync must reject a missing Darwin private registry rather than silently remove host hook exemptions";
}

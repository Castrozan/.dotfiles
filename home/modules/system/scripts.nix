{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "rebuild" (builtins.readFile ./scripts/rebuild))
    (pkgs.writeShellScriptBin "nix-gc" (builtins.readFile ./scripts/nix-gc))
    (pkgs.writeShellScriptBin "tar-unzip2dir" (builtins.readFile ./scripts/tar-unzip2dir))
    (pkgs.writeShellScriptBin "mouse-poll-rate" ''
      export PATH="${pkgs.python3}/bin:$PATH"
      ${builtins.readFile ./scripts/mouse-poll-rate}
    '')
  ];
}

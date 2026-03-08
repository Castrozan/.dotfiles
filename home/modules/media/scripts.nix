{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "daily-note" (builtins.readFile ./scripts/daily-note))
    (pkgs.writeShellScriptBin "on" (builtins.readFile ./scripts/on))
    (pkgs.writeShellScriptBin "pdf-edit" (builtins.readFile ./scripts/pdf-edit))
    (pkgs.writeShellScriptBin "speed-read" ''
      export PATH="${pkgs.bc}/bin:${pkgs.coreutils}/bin:${pkgs.gnused}/bin:$PATH"
      ${builtins.readFile ./scripts/speed-read}
    '')
  ];
}

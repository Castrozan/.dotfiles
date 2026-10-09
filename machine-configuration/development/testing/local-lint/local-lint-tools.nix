{ pkgs }:
let
  qualitySource = ../../../../repository/verification/quality/local-lint;
  qualityLibrary = pkgs.runCommand "dotfiles-local-lint-library" { } ''
    mkdir -p "$out"
    cp ${qualitySource}/*.py "$out/"
  '';
  nativeNixFindings = pkgs.writeShellScriptBin "dotfiles-nix-findings" ''
    exec ${pkgs.python312}/bin/python3 ${qualityLibrary}/nix_findings.py "$@"
  '';
  runtimePackages = [
    (import ./qlty-package.nix { inherit pkgs; })
    nativeNixFindings
    pkgs.git
    pkgs.bash
    pkgs.coreutils
    pkgs.ast-grep
    pkgs.ruff
    pkgs.biome
    pkgs.shellcheck
    pkgs.markdownlint-cli
    pkgs.gitleaks
    pkgs.statix
    pkgs.deadnix
  ];
  lint = pkgs.writeShellApplication {
    name = "dotfiles-lint";
    runtimeInputs = runtimePackages;
    text = ''
      export DOTFILES_LINT_TOOL_PATH="${pkgs.lib.makeBinPath runtimePackages}"
      export QLTY_TELEMETRY=off
      export RAYON_NUM_THREADS=2
      exec ${pkgs.python312}/bin/python3 ${qualityLibrary}/check.py "$@"
    '';
  };
in
{
  inherit lint;
  coverage = pkgs.writeShellApplication {
    name = "dotfiles-coverage-check";
    runtimeInputs = [
      pkgs.git
      pkgs.python312Packages.diff-cover
    ];
    text = ''
      exec diff-cover "$@" --fail-under=65
    '';
  };
}

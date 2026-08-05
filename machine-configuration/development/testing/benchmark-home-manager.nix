{ pkgs, lib, ... }:
let
  mkTestingPythonScript = import ./make-testing-python-script.nix { inherit pkgs; };

  desktopBenchmarkIsHyprlandOnlyAndUnavailableOnDarwin = lib.optional pkgs.stdenv.hostPlatform.isLinux (
    mkTestingPythonScript "benchmark-desktop" ./scripts/benchmark_desktop.py
  );
in
{
  home.packages = [
    (mkTestingPythonScript "benchmark-rebuild" ./scripts/benchmark_rebuild.py)
    (mkTestingPythonScript "benchmark-shell" ./scripts/benchmark_shell.py)
  ]
  ++ desktopBenchmarkIsHyprlandOnlyAndUnavailableOnDarwin;
}

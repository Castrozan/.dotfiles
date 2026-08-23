{
  pkgs,
  lib,
  hostname,
  ...
}:
let
  mkTestingPythonScript = import ./make-testing-python-script.nix {
    inherit pkgs hostname;
  };

  desktopBenchmarkIsHyprlandOnlyAndUnavailableOnDarwin =
    lib.optional pkgs.stdenv.hostPlatform.isLinux
      (mkTestingPythonScript {
        name = "benchmark-desktop";
        source = ./scripts/benchmark_desktop.py;
      });
in
{
  home.packages = [
    (mkTestingPythonScript {
      name = "benchmark-rebuild";
      source = ./scripts/benchmark_rebuild.py;
    })
    (mkTestingPythonScript {
      name = "benchmark-shell";
      source = ./scripts/benchmark_shell.py;
    })
  ]
  ++ desktopBenchmarkIsHyprlandOnlyAndUnavailableOnDarwin;
}

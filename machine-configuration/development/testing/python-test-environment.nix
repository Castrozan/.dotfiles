{ pkgs }:
(pkgs.python312.withPackages (
  pythonPackages:
  [
    pythonPackages.pytest
    pythonPackages.pytest-cov
    pythonPackages.elevenlabs
    pythonPackages.numpy
    pythonPackages.tomlkit
    pythonPackages.tomli-w
    pythonPackages.websockets
  ]
  ++ import ../../../agent-harness/quality/evaluations/instructions/python-packages.nix pythonPackages
)).overrideAttrs
  (previous: {
    postBuild = (previous.postBuild or "") + ''
      echo 'import os; __import__("coverage").process_startup() if os.environ.get("COVERAGE_PROCESS_START") else None' > "$out/${pkgs.python312.sitePackages}/dotfiles_coverage.pth"
    '';
  })

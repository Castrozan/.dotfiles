{ pkgs }:
pkgs.python312.withPackages (pythonPackages: [
  pythonPackages.pytest
  pythonPackages.numpy
  pythonPackages.tomli-w
  pythonPackages.pyyaml
])

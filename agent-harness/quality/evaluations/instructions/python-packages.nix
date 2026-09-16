pythonPackages: [
  pythonPackages.pyyaml
  pythonPackages.markdown-it-py
  (pythonPackages.callPackage ./github-slugger-python-package.nix { })
]

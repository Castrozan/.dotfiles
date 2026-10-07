{ pkgs, ... }:
let
  python = pkgs.python312.withPackages (packages: [ packages.pytest ]);
in
{
  domain-shorts-production-contract = pkgs.runCommand "domain-shorts-production-contract" { } ''
    export PYTHONDONTWRITEBYTECODE=1
    cp -R ${../.} source
    chmod -R u+w source
    cd source
    ${python}/bin/python3 -m pytest -q -p no:cacheprovider \
      __tests__/unit/test_shorts_production.py __tests__/unit/test_shorts_quality.py
    touch "$out"
  '';
}

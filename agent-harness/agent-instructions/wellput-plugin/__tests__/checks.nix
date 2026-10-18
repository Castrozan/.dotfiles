{ pkgs, ... }:
let
  plugin = import ../. { inherit pkgs; };
  python = pkgs.python312.withPackages (packages: [ packages.pytest ]);
in
{
  wellput-plugin = pkgs.runCommand "check-wellput-plugin" { } ''
    ${python}/bin/python -m pytest -p no:cacheprovider \
      ${plugin}/tests/test_hooks.py \
      ${plugin}/tests/test_human_facing_reply_rules.py \
      ${plugin}/tests/test_reply_format_configuration.py \
      ${plugin}/tests/test_reply_markdown_structure.py \
      ${plugin}/tests/test_reply_quotation_performance.py
    touch "$out"
  '';
}

{ pkgs, hostname }:
pkgs.runCommand "rebuild" { } ''
  mkdir -p $out/bin $out/libexec/rebuild/backends

  install -m 0755 ${./rebuild} $out/bin/rebuild
  install -m 0644 ${./backends/nixos} $out/libexec/rebuild/backends/nixos
  install -m 0644 ${./backends/darwin} $out/libexec/rebuild/backends/darwin
  install -m 0644 ${./backends/home-manager} $out/libexec/rebuild/backends/home-manager

  substituteInPlace $out/bin/rebuild \
    --replace-fail '@machineAlias@' '${hostname}' \
    --replace-fail '@backendsDirectory@' "$out/libexec/rebuild/backends"
''
